### Gathers initial input from the student to create a custom study plan

import streamlit as st
import time

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
  st.session_state.initial_input["course"] = response

  # Date of Test
  response = form.date_input("Date of Test:", value=None)
  st.session_state.initial_input["test_date"] = response

  # Time to Study Per Day
  response = form.number_input("How much time do you want to study per day? (in hours)",
    value=0.5, step=0.5)
  st.session_state.initial_input["study_time_per_day"] = response

  # Upload Notes
  response = form.file_uploader("Upload your course notes.", type="pdf")
  st.session_state.initial_input["notes"] = response

  # Submit
  submit = form.form_submit_button("Generate Study Plan!")

  ### Process data once submitted
  if submit:
    st.success("Information submitted!")
    time.sleep(1)
    st.session_state.input_submitted = True
    # TODO: connect here to processing data, uploading rag, etc

def start_page():
  if 'start' in st.session_state and st.session_state.start:
    initial_input() # Move to form
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
      st.write("⭒ Use your study plan to break down studying into managable increments each day")
      st.write("⭒ Check your knowledge throughout the process with check-in assessments")

      submit = st.form_submit_button("Let's Go!")
      if submit:
        time.sleep(1)
        st.session_state.start = True
        st.rerun()

start_page()