# File: /Users/clarkbolin/Desktop/CS150/StudyBuddy/Prototype/start_app.py

import streamlit as st
import time
from llmproxy import generate, pdf_upload, retrieve
import os
import re
from string import Template
from FileUpload import upload_file_to_rag, summarize_uploaded_file
from diagnostic_test import run_diagnostic_test
from home import home_page

def initial_input():
    if 'home' in st.session_state and st.session_state.home:
        home_page()
    else:
        st.input_submitted = False
        st.title("Study Buddy")
        st.divider()
        st.header("Help us create your personalized study plan!")
        st.session_state.home = False

        # Store form information
        st.session_state.initial_input = {}

        form = st.form("Initial Input")

        # Name
        response = form.text_input("Name:")
        st.session_state.initial_input["name"] = response.lower().title()

        # Course
        response = form.text_input("Course Name:")
        st.session_state.initial_input["course"] = response.lower().title()

        # Date of Test
        response = form.date_input("Date of Test:", value=None)
        st.session_state.initial_input["test_date"] = response

        # Time to Study Per Day
        response = form.number_input("How much time do you want to study per day? (in hours)",
                                    value=0.5, step=0.5)
        st.session_state.initial_input["study_time_per_day"] = response

        study_topics = upload_notes(form)
        # print(study_topics)

        # trigger diagnostic test
        if st.button("Start Diagnostic Test", disabled=(study_topics == None)):
            st.session_state.generate_diagnostic = True
            st.session_state.home = True
            st.rerun()

def upload_notes(form):
    response = form.file_uploader(
        "Upload your course notes.", 
        type="pdf", 
        accept_multiple_files=True
    )
    st.session_state.initial_input["notes"] = response

    submit = form.form_submit_button("Submit Study Preferences")

    ### Process data once submitted
    if submit:
        st.success("Information submitted!")
        time.sleep(1)
        st.session_state.input_submitted = True

        # Initialize master list of study topics if it doesn't exist
        if 'all_study_topics' not in st.session_state:
            st.session_state.all_study_topics = []

        # Set a unique session id for this student + test
        st.session_state.session_id = st.session_state.initial_input.get("name") + st.session_state.initial_input.get("course")

        uploaded_files = st.session_state.initial_input.get("notes")
        if uploaded_files:
            total_files = len(uploaded_files)
            progress_bar = st.progress(0)

            for idx, uploaded_file in enumerate(uploaded_files):
                with st.spinner(f"📤 Uploading {uploaded_file.name} to knowledge base..."):
                    file_name = upload_file_to_rag(uploaded_file)

                with st.spinner(f"🧠 Summarizing {uploaded_file.name}..."):
                    summary_text, study_topics = summarize_uploaded_file(file_name)

                # 📄 Review Summaries
                with st.expander(f"📄 Review Summary for {uploaded_file.name}"):
                    parts = summary_text.split('###')
                    for part in parts:
                        part = part.strip()
                        if part.startswith("Overall Summary"):
                            st.subheader("📚 Overall Summary")
                            st.write(part.replace("Overall Summary", "").strip())
                        elif part.startswith("Study Topics"):
                            st.subheader("📝 Study Topics")
                            st.markdown(part.replace("Study Topics", "").strip())

                # Add extracted study topics to master list
                st.session_state.all_study_topics.extend(study_topics)

                # Update Progress
                progress = (idx + 1) / total_files
                progress_bar.progress(progress)

        # Stop Here and Review
        st.info("📚 Please review your summaries carefully before moving forward.")

        return st.session_state.all_study_topics

def start_page():
    if 'start' in st.session_state and st.session_state.start:
        initial_input()
    else:
        st.set_page_config(layout="wide")
        st.start = False
        st.title("Study Buddy")
        st.divider()

        st.subheader("Welcome to Study Buddy!")
        st.write("Design a Custom Study Plan, Break It Into Daily Goals, and Track Your Progress with Interactive Check-Ins!")

        with st.form("Start Page"):
            steps_html = """
            <div style='text-align: center;'>
                <h2>How It Works:</h2>
                <h4>⭒ Input your study preferences & course notes, then take a quick diagnostic test to spot any tricky topics </h4>
                <h4>⭒ StudyBuddy puts it all together to create a personalized study plan that focuses on what you need most </h4>
                <h4>⭒ Follow your plan step by step, with manageable study sessions and helpful check-ins to keep you on track and feeling confident </h4>
                <br>
            </div>
            """
            st.markdown(steps_html, unsafe_allow_html=True)

            submit = st.form_submit_button("**Let's Go!**", use_container_width=True)
            if submit:
                time.sleep(1)
                st.session_state.start = True
                st.rerun()

start_page()