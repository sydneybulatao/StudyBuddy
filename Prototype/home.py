import streamlit as st
from generate_test import generate_test_page
from streamlit_calendar import calendar

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
    # cal, nav = st.columns([6, 1])

    ### Buttons for naviation
    # take_test = nav.button("Take Practice Test", 
    #   help="Take an initial assessment, check-in test, or final assessment.",
    #   use_container_width=True)
    # upload_notes = nav.button("Upload Notes", 
    #   help="Add additional notes to your studying material.",
    #   use_container_width=True)

    ### Study plan calendar
    calendar_options = {
        "headerToolbar": {
                "left": "today,prev,next",
                "center": "title",
                "right": "dayGridDay,dayGridWeek,dayGridMonth"},
        "initialView": "dayGridMonth",
        "editable": True,
        "selectable": True,
        "slotMinTime": "00:00:00",
        "slotMaxTime": "23:59:59",
    }

    calendar_events = [] # TODO: INPUT EVENTS HERE

    # Display calendar
    # with cal:
      # calendar(
      #   events=calendar_events,
      #   options=calendar_options
      # )
    calendar(
        events=calendar_events,
        options=calendar_options
      )

    ### Buttons for naviation
    take_test = st.button("Take Practice Test", 
      help="Take an initial assessment, check-in test, or final assessment.",
      use_container_width=True)
    upload_notes = st.button("Upload Notes", 
      help="Add additional notes to your studying material.",
      use_container_width=True)

    ## Handle button clicks
    if take_test:
      st.session_state.generate_test = True
      st.rerun()

    elif upload_notes:
      st.session_state.upload_notes = True
      st.rerun()

home_page()