### Gathers initial input from the student to create a custom study plan

import streamlit as st
import time
from llmproxy import generate, pdf_upload, retrieve
import os
import re
from string import Template
from FileUpload import upload_file_to_rag, summarize_uploaded_file
from home import home_page

def initial_input():
    if 'home' in st.session_state and st.session_state.home:
        home_page()
    else:
        # Overall page elements
        st.input_submitted = False
        st.title("Study Buddy 🌿•₊✧💻⋆⭒˚☕️｡⋆")
        st.header("Help us create your personalized study plan!")
        st.session_state.home = False

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

            # Set a unique session id for this student + test
            st.session_state.session_id = st.session_state.initial_input.get("name") + st.session_state.initial_input.get("course")
            
            # ✅ Clark's Code: Upload to RAG and summarize
            uploaded_files = st.session_state.initial_input.get("notes")
            if uploaded_files:
                total_files = len(uploaded_files)
                progress_bar = st.progress(0)

                for idx, uploaded_file in enumerate(uploaded_files):
                    with st.spinner(f"📤 Uploading {uploaded_file.name} to knowledge base..."):
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

            # TODO: idk if here we should have them review the summary before moving on? 
            # Move to the home page
            st.session_state.home = True
            st.rerun()
                  
def start_page():
    if 'start' in st.session_state and st.session_state.start:
        initial_input()  # Move to form
    else:
        # Overall page elements
        st.set_page_config(layout="wide")
        st.start = False
        st.title("Study Buddy 🌿•₊✧💻⋆⭒˚☕️｡⋆")

        # Description of app
        st.subheader("Welcome to Study Buddy!")
        st.write("Design a Custom Study Plan, Break It Into Daily Goals, and Track Your Progress with Interactive Check-Ins!")
        st.divider()

        with st.form("Start Page"):
            steps_html = """
            <div style='text-align: center;'>
                <h2>How It Works:</h2>
                <h4>⭒ Input your study preferences & course notes to build a custom study plan</h4>
                <h4>⭒ Use your study plan to break down studying into manageable increments each day</h4>
                <h4>⭒ Check your knowledge throughout the process with check-in assessments</h4>
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