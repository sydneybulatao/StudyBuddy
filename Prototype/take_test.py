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
    if (test_type != "Diagnostic Test"):
      if st.button("Home", type='primary'):
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

    if (test_type == "Diagnostic Test"):
      st.write("""
            Welcome to your personalized diagnostic test!  
            This short assessment is designed to **evaluate your familiarity** with the key topics from your uploaded notes.  

            Please answer each question to the **best of your ability**.  
            ⭐ **Star** any questions you're uncertain about to remember to review after grading.  
            Your results will help tailor your future study plan to focus on the areas where you need the most support.
            """)
    else:
      st.write("""**Answer all questions**—if you're unsure, make your best guess.  
              ⭐ **Star** any questions you're uncertain about to remember to review after grading.  
              Good luck!""")

    # Initialize session state for starred questions
    if "starred_questions" not in st.session_state:
        st.session_state.starred_questions = {}

    ### Test form
    test =  st.form("Practice Test")
    # Iterate through each question and format based on type
    for q_number in list(questions.keys()):
      question_text = "Q" + str(q_number) + ". " + questions[q_number]["question"]
      q_type = questions[q_number]["type"]
      question_html = f"<div style='font-size: 20px; font-weight: bold; display: inline-block;'>{question_text}</div>"

      # Display the question with a checkbox to mark as starred
      starred = st.session_state.starred_questions.get(q_number, False)
      checkbox_label = "⭐"

      # Checkbox to mark the question as starred
      if test.checkbox(checkbox_label, value=starred, key=f"star_{q_number}"):
          st.session_state.starred_questions[q_number] = True
      else:
          st.session_state.starred_questions[q_number] = False

      # Display the question with the star button
      test.markdown(question_html, unsafe_allow_html=True)

      # Input field, depending on type 
      if (q_type == "multiple choice"):
        response = test.radio(
          question_text,
          questions[q_number]["choices"],
          index=None,
          label_visibility='collapsed'
        )
        st.session_state.responses[q_number] = response
      
      elif (q_type == "short answer"):
        response = test.text_input(question_text, label_visibility='collapsed')
        if response is None:
          response = ""
        st.session_state.responses[q_number] = response
      
      test.markdown("<br>", unsafe_allow_html=True)

    # Submit button
    submit = test.form_submit_button('Submit')

    ### Go to grade test page
    if submit:
      st.success("Test submitted!")
      time.sleep(1)
      st.session_state.test_submitted = True
      st.rerun()
