import streamlit as st
from generate_test import generate_test_page
from study_calendar import display_calendar
from datetime import datetime, date

def home_page():
  ### Handle flow
  # GENERATE TEST BUTTON CLICKED
  if 'generate_test' in st.session_state and st.session_state.generate_test:
    generate_test_page()
  # UPLOAD NEW NOTES BUTTON CLICKED
  elif 'upload_notes' in st.session_state and st.session_state.upload_notes:
    return # put upload notes page here
  # HOME PAGE
  else:
    # Reset button variables
    st.session_state.generate_test = False
    st.session_state.upload_notes = False
  
    ### Overall page elements
    st.title("Study Buddy")
    st.divider()
    _, calendar, _, nav = st.columns([0.1, 0.7, 0.1, 0.3])

    ### Study plan calendar
    with calendar:
      display_calendar(st.session_state.initial_input.get("course"))

    ### Buttons for naviation
    # Pick greeting based on current time
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Good morning, "
    elif 12 <= current_hour < 17:
        greeting = "Good afternoon, "
    elif 17 <= current_hour < 21:
        greeting = "Good evening, "
    else:
        greeting = "Hi there, "

    nav.subheader(greeting + st.session_state.initial_input.get("name") + "!")
    nav.write("Currently Studying: " + st.session_state.initial_input.get("course"))
    days_left = (st.session_state.initial_input.get("test_date") - date.today()).days
    nav.write("Days Until Test: " + str(days_left))
    take_test = nav.button("Take Practice Test", 
      help="Take an initial assessment, check-in test, or final assessment.")
    upload_notes = nav.button("Upload Notes", 
      help="Add additional notes to your studying material.")

    ## Handle button clicks
    if take_test:
      st.session_state.generate_test = True
      st.rerun()

    elif upload_notes:
      st.session_state.upload_notes = True
      st.rerun()