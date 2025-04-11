from streamlit_calendar import calendar
from datetime import datetime, timedelta
import streamlit as st

def display_calendar(course_name):
    st.header("🗓️ " + st.session_state.initial_input.get("name") + "'s Study Calendar")

    test_date = st.session_state.initial_input.get("test_date")

    if test_date:
        study_notes_day = test_date - timedelta(days=3)
        practice_problems_day = test_date - timedelta(days=2)
        practice_test_day = test_date - timedelta(days=1)

        events = [
            {
                "id": "study",
                "title": f"📖 Study Notes for {course_name}",
                "start": study_notes_day.strftime("%Y-%m-%d"),
                "allDay": True,
                "backgroundColor": "#3D9DF3",
                "borderColor": "#3D9DF3",
            },
            {
                "id": "problems",
                "title": f"📝 Practice Problems - {course_name}",
                "start": practice_problems_day.strftime("%Y-%m-%d"),
                "allDay": True,
                "backgroundColor": "#FFBD45",
                "borderColor": "#FFBD45",
            },
            {
                "id": "practice_test",
                "title": f"🧠 Practice Test - {course_name}",
                "start": practice_test_day.strftime("%Y-%m-%d"),
                "allDay": True,
                "backgroundColor": "#FF6C6C",
                "borderColor": "#FF6C6C",
            },
            {
                "id": "exam_day",
                "title": f"📅 Exam Day! - {course_name}",
                "start": test_date.strftime("%Y-%m-%d"),
                "allDay": True,
                "backgroundColor": "#3DD56D",
                "borderColor": "#3DD56D",
            }
        ]

        # 📅 Set up calendar with eventClick enabled
        clicked = calendar(
            events=events,
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
            st.info(f"📝 **Event:** {event['title']}")

    else:
        st.error("⚠️ Test Date is missing. Please enter your test date above.")