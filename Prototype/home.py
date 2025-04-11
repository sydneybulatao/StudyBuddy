import streamlit as st
from generate_test import generate_test_page
from streamlit_calendar import calendar
from study_calendar import display_calendar

def home_page():
  ### Handle flow
  # GENERATE TEST BUTTON CLICKED
  if 'generate_test' in st.session_state and st.session_state.generate_test:
    generate_test_page()
    return
  # UPLOAD NEW NOTES BUTTON CLICKED
  elif 'upload_notes' in st.session_state and st.session_state.upload_notes:
    return # put upload notes page here
  # HOME PAGE
  else:
    # Reset button variables
    st.session_state.generate_test = False
    st.session_state.upload_notes = False
  
    ### Overall page elements
    st.title("Study Buddy 🌿•₊✧💻⋆⭒˚☕️｡⋆")
    calendar, nav = st.columns([0.7, 0.3])

    ### Study plan calendar
    with calendar:
      display_calendar(st.session_state.initial_input.get("course"))

    ### Buttons for naviation
    take_test = nav.button("Take Practice Test", 
      help="Take an initial assessment, check-in test, or final assessment.",
      use_container_width=True)
    upload_notes = nav.button("Upload Notes", 
      help="Add additional notes to your studying material.",
      use_container_width=True)

    ## Handle button clicks
    if take_test:
      st.session_state.generate_test = True
      st.rerun()

    elif upload_notes:
      st.session_state.upload_notes = True
      st.rerun()