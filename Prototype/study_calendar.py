from streamlit_calendar import calendar
from datetime import datetime, timedelta, date
import streamlit as st
from llmproxy import generate
import base64

study_plan_instructions = """
INSTRUCTIONS:
You are helping create a customized study plan for a student. You will receive the following information:
- The course name
- A list of topics the student must study, categorized by their current knowledge with the topics
- The amount of time they would like to study per day
- The date they want to finish studying (END DATE)
- The current date (CURRENT DATE)

Topics will be provided in three categories of mastery:
- Unfamiliar 🔴: Topics the student struggled with. These should be studied first and may require multiple days of review.
- Somewhat Familiar 🟡: Topics the student somewhat understands. These should be reviewed after Revisit topics and may require more than one session.
- Familiar 🟢: Topics the student is comfortable with. These should be reviewed briefly and only once.

Your task is to break up the topics and generate a calendar-based study plan starting on the CURRENT DATE and ending on the END DATE.
As the student studies topics, they should also complete check-in tests after completing one or more related topics.

Study Plan Rules:
- Every topic provided must appear in **at least one study entry**. Do not skip any topics.
- If there are more topics than available days, **combine multiple related topics into one study entry**.
  - Prioritize stacking topics in the same category (e.g., two Unfamiliar 🔴 topics together).
  - You may combine 2–3 topics per day if needed.
  - Try to balance workload sensibly so that the student is not overwhelmed.
- Prioritize topics in this order: Unfamiliar 🔴 → Somewhat Familiar 🟡 → Familiar 🟢.
- Topics in the Unfamiliar 🔴 category should appear multiple times (2–3 study sessions each depending on available days).
- Topics in the Somewhat Familiar 🟡 category may also appear more than once if time allows.
- Topics in the Familiar 🟢 category should be studied only once.
- ALL topics must be studied — no topics may be skipped.
- Check-In Tests should be scheduled after related topics are studied (1–3 topics per test).
- The student studies once per day. Only one calendar entry per day is allowed.
- IMPORTANT: There should be a check-in test scheduled **at least once every 2–3 days** to ensure consistent assessment. Do not allow more than 3 days to pass without a check-in test.
- DO NOT schedule a check-in test immediately after another check-in test. There must be at least one day of studying between check-in tests.

Date Rules — Very Important:
1. Only generate entries for dates between and including the CURRENT DATE and the END DATE.
2. Do not generate any entries after the END DATE — the final calendar entry must occur on or before the END DATE.
3. The END DATE is allowed to have a calendar entry (such as a final check-in test).
4. **Ensure that only one calendar entry is generated per day.** If there is already a calendar entry (study or check-in test) for a given date, do not generate another for that date.
5. Any entries generated after the END DATE are invalid and must be avoided completely. 
   This includes even one extra day — the final date allowed for any entry is the END DATE itself.
   Violating this rule means the plan is unusable.
6. You must generate an entry for each day within the range of CURRENT DATE and END DATE.

STUDY TIME PER DAY is given in hours. If it is less than 1 hour, convert it into minutes for the title (e.g., 0.5 hours → 30 Minutes, 0.75 hours → 45 Minutes, etc.).

OUTPUT:
Strictly output your response in only one of the two following formats for each calendar entry. 
For studying entries, strictly output as follows:
TYPE: study  
TITLE: Study <study time>: <topic or topic(s) to study>  
START: <date in yyyy-mm-dd format>  

For check-in test entries, strictly output as follows:
TYPE: check_in  
TITLE: Check-In Test: <topic or topic(s) to do check-in test for>  
START: <date in yyyy-mm-dd format>  

EXAMPLES:  
INPUT:  
COURSE NAME: Database Design and Structure  
TOPICS:  
Unfamiliar 🔴: Aggregate Functions, JOIN  
Somewhat Familiar 🟡: ALL  
Familiar 🟢: ANY  
STUDY TIME PER DAY: 0.5 hours  
END DATE: 4/20/2025  
CURRENT DATE: 4/13/2025  

OUTPUT:   
TYPE: study  
TITLE: Study 30 Minutes: Aggregate Functions  
START: 2025/04/13  
TYPE: study  
TITLE: Study 30 Minutes: JOIN  
START: 2025/04/14  
TYPE: study  
TITLE: Study 30 Minutes: Aggregate Functions  
START: 2025/04/15  
TYPE: check_in  
TITLE: Check-In Test: Aggregate Functions, JOIN  
START: 2025/04/16  
TYPE: study  
TITLE: Study 30 Minutes: JOIN  
START: 2025/04/17  
TYPE: study  
TITLE: Study 30 Minutes: ALL  
START: 2025/04/18  
TYPE: study  
TITLE: Study 30 Minutes: ANY  
START: 2025/04/19  
TYPE: check_in  
TITLE: Check-In Test: ALL, ANY  
START: 2025/04/20

INPUT:
COURSE NAME: Software Engineering Principles
TOPICS:
Unfamiliar 🔴: Requirements Analysis, Design Patterns, UML, Agile Methodologies
Somewhat Familiar 🟡: Testing Strategies, Version Control, CI/CD
Familiar 🟢: Deployment, DevOps Basics, Documentation
STUDY TIME PER DAY: 1 hour
END DATE: 4/27/2025
CURRENT DATE: 4/21/2025

OUTPUT:
TYPE: study
TITLE: Study 1 Hour: Requirements Analysis, Design Patterns
START: 2025/04/21
TYPE: study
TITLE: Study 1 Hour: UML, Agile Methodologies
START: 2025/04/22
TYPE: check_in
TITLE: Check-In Test: Requirements Analysis, Design Patterns, UML, Agile Methodologies
START: 2025/04/23
TYPE: study
TITLE: Study 1 Hour: Testing Strategies, Version Control
START: 2025/04/24
TYPE: study
TITLE: Study 1 Hour: CI/CD, Deployment
START: 2025/04/25
TYPE: check_in
TITLE: Check-In Test: Testing Strategies, Version Control, CI/CD
START: 2025/04/26
TYPE: study
TITLE: Study 1 Hour: DevOps Basics, Documentation
START: 2025/04/27


‼️ FINAL REMINDER:
1. You must not generate any entries for dates beyond the END DATE. The final calendar entry must be on or before the END DATE. Any entries after that are invalid.

2. You must include **every single study topic** in at least one study entry. 
   - It is acceptable to include **multiple topics** in one study entry if needed.
   - No topic may be skipped or left out of the schedule.

‼️ FINAL REMINDER: Double-check your plan before finalizing.
"""

note_instructions = """
INSTRUCTIONS:
You are helping create a personalized study note based on a diagnostic test.

You will be given:
1. A TITLE which includes the time and the specific topic(s) being studied today.
2. A TOPICS section that shows the student's diagnostic results, categorized into:
   - Unfamiliar 🔴: Topics the student struggled with (high priority)
   - Somewhat Familiar 🟡: Topics the student somewhat understands (medium priority)
   - Familiar 🟢: Topics the student is comfortable with (low priority)

YOUR TASK:
Write a one-sentence note that:
- Describes the student's understanding **only** for the topic(s) listed in the TITLE.
- Gives brief guidance on which topic(s) to focus more on and why based on the diagnostic results.

CRITICAL RULES:
- Only mention the topic(s) listed in the TITLE. Do not include any topics not in the TITLE, even if they appear in the TOPICS list.
- If multiple topics are in the TITLE, compare their levels of understanding.
- If only one topic is listed, comment only on that topic’s understanding and suggested focus.

FORMAT:
Input:  
TITLE: 📚 Study 1 Hour <Topic1>, <Topic2>, ...
TOPICS:  
Unfamiliar 🔴: <list of topics>  
Somewhat Familiar 🟡: <list of topics>  
Familiar 🟢: <list of topics>

Output:  
A one-sentence note that:
- Mentions only the topic(s) listed in the TITLE
- Reflects how the student performed on those topic(s) in the diagnostic
- Suggests what to focus on while studying

Example 1:
Input:  
TITLE: 📚 Study 1 Hour JOIN, ALL  
TOPICS:  
Unfamiliar 🔴: Aggregate Functions, JOIN  
Somewhat Familiar 🟡: ALL  
Familiar 🟢: ANY

Output:  
You struggled with JOIN on the diagnostic test, but did okay with ALL. Prioritize JOIN a bit more than ALL when studying.

Example 2:
Input:  
TITLE: 📚 Study 1 Hour Aggregate Functions  
TOPICS:  
Unfamiliar 🔴: Aggregate Functions, JOIN  
Somewhat Familiar 🟡: ALL  
Familiar 🟢: ANY

Output:  
You struggled with Aggregate Functions on the diagnostic test, so make sure to review it thoroughly.
"""

def generate_study_plan():
    response = generate(
        model="4o-mini",
        system=study_plan_instructions,
        query="COURSE NAME: " + st.session_state.initial_input["course"] +
              "TOPICS: " + st.session_state.diagnostic_results_str +
              "STUDY TIME PER DAY: " + str(st.session_state.initial_input["study_time_per_day"]) + " hours" +
              "END DATE: " + str(st.session_state.initial_input["test_date"] - timedelta(days=2)) +
              "CURRENT DATE: " + str(date.today()),
        temperature=0.0,
        lastk=0,
        session_id="calendar_session",
        rag_usage=False
    )
    return response.get("response", "") if isinstance(response, dict) else response

def get_study_plan_and_parse(end, retry_count=0):
    study_plan = "No Study Plan Generated."
    try:
        study_plan = generate_study_plan()
        print(study_plan)
        print("\n\n")
        lines = [line.strip() for line in study_plan.strip().splitlines() if line.strip()]
        entries = []
        for i in range(0, len(lines), 3):
            entry_id = lines[i].replace("TYPE: ", "")
            title = lines[i + 1].replace("TITLE: ", "")
            start = lines[i + 2].replace("START: ", "")

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

        if entries == []:
            raise ValueError("Empty entries list")

        return entries

    except Exception as e:
      # Retry logic with a maximum of 10 retries
      if retry_count < 10:
        return get_study_plan_and_parse(end, retry_count + 1)
      else:
        # Show the error after all retries used 
        st.error("Error: Unable to transform study plan into calendar format.")

        # Show what was generated
        st.info(study_plan)
        return []

def generate_note(event):
    response = generate(
        model="4o-mini",
        system=note_instructions,
        query="TITLE: " + event.get("title", "") +
              "TOPICS: " + st.session_state.diagnostic_results_str,
        temperature=0.0,
        lastk=0,
        session_id="note_session",
        rag_usage=False
    )
    return response.get("response", "") if isinstance(response, dict) else response

@st.dialog("Task")
def show_event_details():
    event_title = st.session_state.get("selected_event_title", "Unknown Title")
    event_start = st.session_state.get("selected_event_start", "Unknown Date")

    st.write(f"**{event_title}**")
    st.write(f"**Date:** {event_start}")

    event_notes = st.session_state.event_notes.get(event_title, "")
    if event_notes:
        st.write(f"**Insights:** {event_notes}")

    key_name = f"completed_{event_title}_{event_start}"
    if st.checkbox("Mark as Completed", key=key_name):
        # Find the event and update it
        updated_events = []
        for e in st.session_state.events:
            if e['title'] == event_title and e['start'] == event_start:
                updated_event = e.copy()
                updated_event['title'] = "✅ " + e['title']
                updated_event['backgroundColor'] = "#B0B0B0"
                updated_event['borderColor'] = "#B0B0B0"
                updated_event['textColor'] = "rgba(0, 0, 0, 0.6)" #text color
                updated_events.append(updated_event)
            else:
                updated_events.append(e)

        # Update the session_state
        st.session_state.events = updated_events

        # Clear selected event
        del st.session_state.selected_event_title
        del st.session_state.selected_event_start

        st.success("Marked as completed! Click event again to see the crossed off title!")

        st.session_state.calendar_version += 1  # force calendar to rebuild

@st.dialog("Welcome to Your Study Plan!", width="large")
def show_welcome_message():
    # Define steps as a list of (gif_path, message) tuples
    steps = [
        ("gifs/click.gif", "Click on tasks for more information"),
        ("gifs/drag.gif", "Drag and drop tasks to customize"),
        ("gifs/check.gif", "Check off completed tasks")
    ]

    # Initialize step tracker
    step_key = "welcome_step"
    if step_key not in st.session_state:
        st.session_state[step_key] = 0

    step = st.session_state[step_key]

    # Stop if out of bounds
    if step >= len(steps):
        st.session_state[step_key] = 0
        st.rerun()

    gif_path, message = steps[step]

    # Load and display the GIF
    with open(gif_path, "rb") as f:
        contents = f.read()
    data_url = base64.b64encode(contents).decode("utf-8")

    st.markdown(f"""
        <div style='text-align: center;'>
            <img src="data:image/gif;base64,{data_url}" alt="step gif" style="max-width: 100%; height: auto;" />
            <p style="font-weight: bold;">{message}</p>
        </div>
    """, unsafe_allow_html=True)

    # Show Next button
    if step < len(steps) - 1:
        if st.button("Next", type="primary", key=f"next_{step}"):
            st.session_state[step_key] += 1

def display_calendar(course_name):
    st.header("🗓️ " + st.session_state.initial_input.get("name") + "'s Study Calendar")
    if 'calendar_version' not in st.session_state:
      st.session_state.calendar_version = 0
    test_date = st.session_state.initial_input.get("test_date")

    if 'events' not in st.session_state:
        if test_date:
            overall_assessment_day = test_date - timedelta(days=1)
            events = [
                {
                    "id": "assessment",
                    "title": f"📝 Overall Practice Test: {course_name}",
                    "start": overall_assessment_day.strftime("%Y-%m-%d"),
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

            with st.spinner("Generating your personalized study plan..."):
                end = str(test_date - timedelta(days=2))
                study_plan_entries = get_study_plan_and_parse(end=end)

            with st.spinner("Adding insights from your diagnostic results..."):
                if study_plan_entries:
                    st.session_state.event_notes = {}
                    for entry in study_plan_entries:
                        events.append({
                            "id": entry.get("id"),
                            "title": entry.get("title"),
                            "start": entry.get("start"),
                            "allDay": True,
                            "backgroundColor": entry.get("color"),
                            "borderColor": entry.get("color")
                        })
                        if entry.get("id") == "study":
                            st.session_state.event_notes[entry.get("title")] = generate_note(entry)

                    st.session_state.events = events
                    show_welcome_message()
        else:
            st.error("Error: No test date input.")

    if st.session_state.get('events'):
        clicked = calendar(
          events=st.session_state.events,  # Always pulling updated events
          options={
              "initialView": "dayGridMonth",
              "height": 700,
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
          callbacks=["eventClick"],  # Enable event click callback
          # force re-render
          key=f"study_calendar_v{st.session_state.calendar_version}"  
        )

        if clicked and clicked.get("eventClick"):
            event = clicked["eventClick"]["event"]
            st.session_state.selected_event_title = event['title']
            st.session_state.selected_event_start = event['start']
            show_event_details()
    else:
        st.error("Error: Cannot generate study plan.")