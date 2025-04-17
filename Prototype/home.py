import streamlit as st
from generate_test import generate_test_page
from take_test import take_test_page
from grade_test import grade_test_page
from study_calendar import display_calendar
from datetime import datetime, date

def home_page():
  ### ROUTING LOGIC (handles returning to home, etc.)
  if st.session_state.get("go_home", False):
    st.session_state.go_home = False  # Reset the flag
    # Continue into home page

  # TEST SUBMITTED, GRADING
  if st.session_state.get('test_submitted', False):
    grade_test_page()
    return

  # TEST FORM SUBMITTED, TAKING THE TEST
  if st.session_state.get('test_input_submitted', False):
    take_test_page()
    return

  # GENERATE TEST BUTTON CLICKED
  if st.session_state.get('generate_test', False):
    generate_test_page()
    return

  ### DEFAULT: HOME PAGE
  # Reset any other session state for a clean home experience
  st.session_state.generate_test = False
  st.session_state.upload_notes = False

  ### Overall page elements
  st.title("Study Buddy")
  st.divider()
  _, calendar, _, nav = st.columns([0.1, 0.7, 0.1, 0.4])

  ### Study plan calendar
  with calendar:
    display_calendar(st.session_state.initial_input.get("course"))

  # Pick greeting based on current time
  greeting = "Hi there, "
  current_hour = datetime.now().hour
  if 5 <= current_hour < 12:
      greeting = "Good morning, "
  elif 12 <= current_hour < 17:
      greeting = "Good afternoon, "
  elif 17 <= current_hour < 21:
      greeting = "Good evening, "

  # Navigation to other pages
  with nav:
    days_left = str((st.session_state.initial_input["test_date"] - date.today()).days)
    st.markdown(f"""
        <div style="background-color: #ECECEC; padding: 20px; border-radius: 10px; width: 100%;">
          <h3>{greeting}{st.session_state.initial_input["name"]}!</h3>
          <p>Currently Studying: {st.session_state.initial_input["course"]}</p>
          <p>Days Until Test: {days_left}</p>
        </div>
        <br>
    """, unsafe_allow_html=True)

    # Styling for the buttons
    st.markdown("""
      <style>
      button[kind="secondary"] {
        background-color: #78C18A;
        color: white;
        padding: 10px 10px;
        margin: 8px 0;
        border: 1px solid #087623;
        cursor: pointer;
        width: 200px;
      }
      </style>
      """, unsafe_allow_html=True)

    ### Buttons for naviation
    take_test = st.button("Take Practice Test", 
      help="Take an initial assessment, check-in test, or final assessment.")
    upload_notes = st.button("Upload Notes", 
      help="Add additional notes to your studying material.")

    ## Handle button clicks
    if take_test:
      st.session_state.generate_test = True
      st.rerun()

    # elif upload_notes:
    #   st.session_state.upload_notes = True
    #   st.rerun()

    if ('test_stats' in st.session_state):
      st.markdown(f"""
          <div style="background-color: #ECECEC; padding: 20px; border-radius: 10px; width: 100%;">
            <p style="font-size: 20px;"><strong>Last Test Taken:</strong></p>
            <p>Score: {st.session_state.test_stats['score']}%</p>
            <p>{st.session_state.test_stats['insights']}</p>
          </div>
          <br>
      """, unsafe_allow_html=True)
    else:
      st.markdown(f"""
          <div style="background-color: #ECECEC; padding: 20px; border-radius: 10px; width: 100%;">
            <p style="font-size: 20px;"><strong>Last Test Taken:</strong></p>
            <p>No results yet...</p>
            <p>Take the initial assessment to assess your current knowledge!</p>
          </div>
          <br>
      """, unsafe_allow_html=True)

### FOR TESTING HOME PAGE:
# st.session_state.initial_input = {
#   "name": 'Sydney',
#   "course": 'Computation Theory',
#   "test_date": date.today(),
#   "study_time_per_day": 0.5
# }
# st.session_state.session_id = st.session_state.initial_input.get("name") + st.session_state.initial_input.get("course")
# home_page()