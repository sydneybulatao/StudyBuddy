### Outputs test as a form that user can fill out to take the test.

import streamlit as st
import time

def take_test_page():
  ### Overall page elements
  if 'responses' not in st.session_state:
    st.session_state.responses = {}

  # Grade test once submitted
  if st.session_state.get("test_submitted", False):
    st.rerun()
    return
  else:
    # Get back test information
    test_type = st.session_state.test_type
    topics = st.session_state.topics
    questions = st.session_state.questions
    subject = st.session_state.subject

    st.session_state.test_submitted = False # reset this for new test

    st.title("Study Buddy")
    st.divider()

    # Home button
    if st.button("Home"):
      # Reset any test session variables
      st.session_state.generate_test = False
      st.session_state.upload_notes = False
      st.session_state.test_input_submitted = False
      st.session_state.test_submitted = False
      st.session_state.responses = {}

      st.session_state.go_home = True
      st.rerun()

    st.header(subject + " " + test_type) 
    if (test_type == "Check-In Test"):
      st.subheader("Topics covered: " + ", ".join(topics)) 

    ### Test form
    test =  st.form("Practice Test")
    # Iterate through each question and format based on type
    for q_number in list(questions.keys()):
      question_text = "Q" + str(q_number) + ". " + questions[q_number]["question"]
      q_type = questions[q_number]["type"]

      # Input field, depending on type 
      if (q_type == "multiple choice"):
        response = test.radio(
          question_text, 
          questions[q_number]["choices"],
          index=None
        )
        st.session_state.responses[q_number] = response
      
      elif (q_type == "short answer"):
        response = test.text_input(question_text)
        st.session_state.responses[q_number] = response

    # Submit button
    # TODO: form verification - ensure all questions answered or attempted
    submit = test.form_submit_button('Submit')

    ### Go to grade test page
    if submit:
      st.success("Test submitted!")
      time.sleep(1)
      st.session_state.test_submitted = True
      st.rerun()
