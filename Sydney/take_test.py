### Outputs test as a form that user can fill out to take the test.

import streamlit as st
import time
from grade_test import grade_test_page

def take_test_page():
  ### dummy input to test 
  test_type = "Check-In Test" # "Check-In Test" or "Initial Assessment" or "Final Assessment"
  topics = ["JOIN", "ANY", "ALL"] # List of strings of test sub-topics (can just say "all topics" if an initial or final assessment)
  questions = {
    1: {
      "question" : "What is the purpose of the SQL JOIN clause?",
      "type" : "short answer",
      "answer" : "The JOIN clause is used to combine rows from two or more tables based on a related column between them." 
    },
    2: {
      "question" : "What does the ANY keyword do in SQL?",
      "type" : "short answer",
      "answer" : "The ANY keyword is used in a subquery to compare a value to any value returned by the subquery."
    },
    3: {
      "question" : "Which of the following SQL clauses is used to combine rows from two tables based on a common column?",
      "type" : "multiple choice",
      "choices" : ["UNION", "JOIN", "WHERE", "SELECT"],
      "answer" : "JOIN"
    },
    4: {
      "question" : "Which SQL operator would you use to compare a value to all values returned by a subquery?",
      "type" : "multiple choice",
      "choices" : ["ANY", "ALL", "IN", "BETWEEN"],
      "answer" : "ALL"
    },
    5: {
      "question" : "How does the ALL keyword differ from ANY in SQL?",
      "type" : "short answer",
      "answer" : "The ALL keyword compares a value to all values returned by a subquery, ensuring that the condition holds true for every value in the result set."
    }
  }

  ### Store test information
  st.session_state.test_type = test_type
  st.session_state.topics = topics
  st.session_state.questions = questions

  ### Overall page elements
  if 'responses' not in st.session_state:
      st.session_state.responses = {}

  # Grade test once submitted
  if 'test_submitted' in st.session_state and st.session_state.test_submitted:
    grade_test_page()
  else:
    st.session_state.test_submitted = False # reset this for new test
    st.title(test_type + " ⋆｡°✎ᝰ ˎˊ˗") 
    st.header("Topics covered: " + ", ".join(topics)) 

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
    submit = test.form_submit_button('Submit')

    ### Go to grade test page
    if submit:
      st.success("Test submitted!")
      time.sleep(1)
      st.session_state.test_submitted = True
      st.rerun()

take_test_page()
