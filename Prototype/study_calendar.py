from streamlit_calendar import calendar
from datetime import datetime, timedelta, date
import streamlit as st
from llmproxy import generate

study_plan_instructions = """
INSTRUCTIONS:
You are helping create a customized study plan for a student. You will receive the following information:
The course name
A list of topics the student must study
The amount of time they would like to study per day
The date they want to finish studying (END DATE)
The current date (CURRENT DATE)

Your task is to break up the topics evenly and generate a calendar-based study plan starting on the CURRENT DATE and ending on the END DATE.
As the student studies topics, they should also complete check-in tests after completing one or more topics. Include check-in tests after related topics are finished.
ALL topics listed in the TOPICS must be studied — no topics may be skipped.
After one or more topics are studied, schedule a Check-In Test to help the student review those topics.
You may group related topics together when appropriate based on the available time, but ensure each topic is studied and tested at least once.
The student studies once per day.

Date Rules — Very Important:
1. Only generate entries for dates between and including the CURRENT DATE and the END DATE.
2. Do not generate any entries after the END DATE — the final calendar entry must occur on or before the END DATE.
3. The END DATE is allowed to have a calendar entry (such as a final check-in test).
4. **Ensure that only one calendar entry is generated per day.** If there is already a calendar entry (study or check-in test) for a given date, do not generate another for that date.
5. Any entries generated after the END DATE are invalid.

STUDY TIME PER DAY is given in hours. If it is less than 1 hour, convert it into minutes for the title (e.g., 0.5 hours → 30 Minutes, 0.75 hours → 45 Minutes, etc.).

OUTPUT:
Strictly output your response in the following format for each calendar entry. 
For studying entries:
TYPE: study
TITLE: Study <study time>: <topic or topic(s) to study>
START: <date in yyyy-mm-dd format>

For check-in test entries:
TYPE: check_in
TITLE: Check-In Test: <topic or topic(s) to do check-in test for>
START: <date in yyyy-mm-dd format>

EXAMPLES:
INPUT: 
COURSE NAME: Database Design and Structure
TOPICS: Aggregate Functions, JOIN, ALL, ANY
STUDY TIME PER DAY: 0.5 hours
END DATE: 4/17/2025
CURRENT DATE: 4/13/2025

OUTPUT:
TYPE: study
TITLE: Study 30 Minutes: Aggregate Functions
START: 2025/04/13
TYPE: study
TITLE: Study 30 Minutes: JOIN
START: 2025/04/14
TYPE: check_in
TITLE: Check-In Test: Aggregate Functions, JOIN
START: 2025/04/15
TYPE: study
TITLE: Study 30 Minutes: ALL, ANY
START: 2025/04/16
TYPE: check_in
TITLE: Check-In Test: ALL, ANY
START: 2025/04/17
"""

def generate_study_plan():
    # Get study plan from model
    response = generate(model = '4o-mini',
      system = study_plan_instructions,
      query = "COURSE NAME: " + st.session_state.initial_input["course"] + \
        "TOPICS: " + ", ".join(st.session_state.all_study_topics) + \
        "STUDY TIME PER DAY: " + str(st.session_state.initial_input["study_time_per_day"]) + " hours" + \
        "END DATE: " + str(st.session_state.initial_input["test_date"] - timedelta(days=2)) + \
        "CURRENT DATE: " + str(date.today()),
      temperature = 0.0,
      lastk = 0,
      session_id = "calendar_session",
      rag_usage = False)
    response = response.get("response", "") if isinstance(response, dict) else response

    return response

def display_calendar(course_name):
    st.header("🗓️ " + st.session_state.initial_input.get("name") + "'s Study Calendar")

    test_date = st.session_state.initial_input.get("test_date")

    # Check if calendar populated yet
    if 'events' not in st.session_state:
      if test_date:
          # Add initial and final assessments
          initial_assessment_day = date.today()
          final_assessment_day = test_date - timedelta(days=1)

          events = [
              {
                  "id": "assessment",
                  "title": f"📝 Initial Assessment: {course_name}",
                  "start": initial_assessment_day.strftime("%Y-%m-%d"),
                  "allDay": True,
                  "backgroundColor": "#78C18A",
                  "borderColor": "#78C18A",
              },
              {
                  "id": "assessment",
                  "title": f"📝 Final Assessment: {course_name} ",
                  "start": final_assessment_day.strftime("%Y-%m-%d"),
                  "allDay": True,
                  "backgroundColor": "#78C18A",
                  "borderColor": "#78C18A",
              },
              {
                  "id": "exam_day",
                  "title": f"📅 Exam Day: {course_name}",
                  "start": test_date.strftime("%Y-%m-%d"),
                  "allDay": True,
                  "backgroundColor": "#F8E16C",
                  "borderColor": "#F8E16C",
              }
          ]

          # Get study plan from model
          study_plan = generate_study_plan()
          
          # Parse
          lines = [line.strip() for line in study_plan.strip().splitlines() if line.strip()]
          entries = []
          for i in range(0, len(lines), 3):
            entry_id = lines[i].replace("TYPE: ", "")
            title = lines[i+1].replace("TITLE: ", "")
            start = lines[i+2].replace("START: ", "")
            
            if entry_id == "check_in":
                title = "✅ " + title
                color = "#254E70"
            elif entry_id == "study":
                title = "📚 " + title
                color = "#8FB8DE"
            else:
                entry_id = "unknown"
                color = "#000"

            entries.append({
                "title": title,
                "start": start,
                "id": entry_id,
                "color": color
            })
          
          # Add to calendar entries
          for entry in entries:
            events.append(
              {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "start": entry.get("start"),
                "allDay": True,
                "backgroundColor": entry.get("color"),
                "borderColor": entry.get("color")
              }
            )

          # Save events
          st.session_state.events = events

      else:
        st.error("Error: No test date input.")

    if st.session_state.events:
      # 📅 Set up calendar with eventClick enabled
      clicked = calendar(
          events=st.session_state.events,
          options={
              "initialView": "dayGridMonth",
              "editable": True,
              "selectable": True,
              "headerToolbar": {
                  "left": "prev,next today",
                  "center": "title",
                  "right": "dayGridMonth,timeGridWeek,timeGridDay"
              }
          },
          custom_css="""
              .fc-event {
                  font-size: 12px;
                  padding: 4px;
              }
          """,
          callbacks=["eventClick"],  # ✅ Enable event click callback
          key="study_calendar"
      )

      # 📤 Check if the user clicked on an event
      if clicked and clicked.get("eventClick"):
          event = clicked["eventClick"]["event"]
          st.info(f"**Task:** {event['title']}")
    
    else:
      st.error("Error: Cannot generate study plan.")