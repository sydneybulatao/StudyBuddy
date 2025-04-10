### Outputs test as a form that user can fill out to take the test.

import streamlit as st
import time
from grade_test import grade_test_page

def take_test_page():
  ### Overall page elements
  if 'responses' not in st.session_state:
      st.session_state.responses = {}

  # Grade test once submitted
  if 'test_submitted' in st.session_state and st.session_state.test_submitted:
    grade_test_page()
    return
  else:
    # Get back test information
    test_type = st.session_state.test_type
    topics = st.session_state.topics
    questions = st.session_state.questions
    subject = st.session_state.subject

    st.session_state.test_submitted = False # reset this for new test
    st.title("Study Buddy 🌿•₊✧💻⋆⭒˚☕️｡⋆")
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
