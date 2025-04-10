### Gathers initial input from the student to create a custom study plan

import streamlit as st
import time
from llmproxy import generate, pdf_upload, retrieve
import os
import re
from string import Template
from FileUpload import upload_file_to_rag, summarize_uploaded_file
from streamlit_calendar import calendar
from datetime import datetime, timedelta



def initial_input():
    # Overall page elements
    st.input_submitted = False
    st.title("Study Buddy 🌿•₊✧💻⋆⭒˚☕️｡⋆")
    st.header("Help us create your personalized study plan!")

    # Store form information
    st.session_state.initial_input = {}

    # Initial input form
    form = st.form("Initial Input")

    # Name
    response = form.text_input("Name:")
    st.session_state.initial_input["name"] = response

    # Course
    response = form.text_input("Course Name:")
    course_name = response
    st.session_state.initial_input["course"] = response

    # Date of Test
    response = form.date_input("Date of Test:", value=None)
    st.session_state.initial_input["test_date"] = response

    # Time to Study Per Day
    response = form.number_input("How much time do you want to study per day? (in hours)",
                                 value=0.5, step=0.5)
    st.session_state.initial_input["study_time_per_day"] = response

    # Upload Notes
    response = form.file_uploader(
    "Upload your course notes.", 
    type="pdf", 
    accept_multiple_files=True
    )
    st.session_state.initial_input["notes"] = response

    # Submit
    submit = form.form_submit_button("Generate Study Plan!")

    ### Process data once submitted
    if submit:
        st.success("Information submitted!")
        time.sleep(1)
        st.session_state.input_submitted = True
        
        # ✅ Clark's Code: Upload to RAG and summarize
        uploaded_files = st.session_state.initial_input.get("notes")
        if uploaded_files:
            total_files = len(uploaded_files)
            progress_bar = st.progress(0)

            for idx, uploaded_file in enumerate(uploaded_files):
                with st.spinner(f"📤 Uploading {uploaded_file.name} to RAG..."):
                    file_name = upload_file_to_rag(uploaded_file)

                with st.spinner(f"🧠 Summarizing {uploaded_file.name}..."):
                    summary = summarize_uploaded_file(file_name)

                st.success(f"✅ Done processing {uploaded_file.name}!")
                st.subheader(f"Summary for {uploaded_file.name}")
                st.markdown(f"```text\n{summary}\n```")

                # 🎯 Update Progress
                progress = (idx + 1) / total_files
                progress_bar.progress(progress)

            st.success("🎉 All files uploaded and summarized!")
    display_calendar(course_name)

def start_page():
    if 'start' in st.session_state and st.session_state.start:
        initial_input()  # Move to form
    else:
        # Overall page elements
        st.start = False
        st.title("Study Buddy 🌿•₊✧💻⋆⭒˚☕️｡⋆")

        # Description of app
        st.subheader("Welcome to Study Buddy!")
        st.write("Design a Custom Study Plan, Break It Into Daily Goals, and Track Your Progress with Interactive Check-Ins!")
        st.divider()

        with st.form("Start Page"):
            # Steps
            st.header("How It Works:")
            st.write("⭒ Input your study preferences & course notes to build a custom study plan")
            st.write("⭒ Use your study plan to break down studying into manageable increments each day")
            st.write("⭒ Check your knowledge throughout the process with check-in assessments")

            submit = st.form_submit_button("Let's Go!")
            if submit:
                time.sleep(1)
                st.session_state.start = True
                st.rerun()

def display_calendar(course_name):
    st.divider()
    st.header("🗓️ Your Study Calendar")

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

start_page()