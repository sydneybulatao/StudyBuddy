### Grades test and provides actionable feedback to the student based on answers.

import streamlit as st
from llmproxy import generate
import re

shorten_instructions = """
INSTRUCTIONS:
You will be given text containing the test insights from a student's practice test. 
Shorten the insights and summarize them into 3 sentences. Feel free to add emojis.
Do not make anything bold. Remove any ** symbols you see. 

Address the student directly."""

grading_instructions = """
INSTRUCTIONS:
You are grading test answers. You will be given the question,
the student's answer, and the solution. 

GRADING CRITERIA:
Compare the student's answer to the solution. The wording does not have to 
be exactly the same, but the student's answer should capture everything
mentioned in the solution. 

OUTPUT:
Strictly output either "CORRECT" or "INCORRECT" based on if the student's
answer correctly answers the question.
"""

check_in = """
INSTRUCTIONS:
You are providing insights for a student to guide their studying, based on how 
well they performed on a check-in test. The check-in test is only on a subset of topics. 
For each topic, you will provide a keyword that lets the student know how well
they did on the questions pertaining to that topic. In addition, you will output
a short blurb of 2 sentences that lets the student know how well they did on the test, 
encourages them to further study topics that they didn't do well on, and commends
them for topics they did do well on. Use a friendly, encouraging, and supportive tone. 
Use emojis in your blurb to make it friendly!

If they did not do well on the test (the number correct was low compared to the total),
DO NOT say they did a good job. Instead, encourage them to put a bit more
time into studying than they currently have been. 

KEYWORD CRITERIA:
Revisit 🔴: The student got all "INCORRECT" for questions pertaining to the topic.
Explanation: "You answered all questions incorrect."

Learning 🟡: The student got some "INCORRECT" and some "CORRECT" for questions pertaining to the topic. 
Explanation: "You answered some questions correct, but some incorrect."

Familiar 🟢: The student got all "CORRECT" for questions pertaining to the topic. 
Explanation: "You answered all questions correct."

OUTPUT:
Strictly output as follows. There may be a smaller or larger number of topics than
what is listed here. Make the topic names and keywords bold in all text that is output.
<topic 1> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Learning 🟡', 'Familiar 🟢'>
<topic 2> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Learning 🟡', 'Familiar 🟢'>
<topic 3> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Learning 🟡', 'Familiar 🟢'>

<2-3 sentence blurb that lets the student know how well they did on the test and identifies areas to study further>
"""

initial = """
INSTRUCTIONS:
You are providing insights for a student to guide their studying, based on how 
well they performed on an initial diagnostic test. The student may not know much about the
topics currently, so it is important to be supportive. This test is on all 
topics that the student must study. 
For each topic, you will provide a keyword that lets the student know how well
they did on the questions pertaining to that topic. In addition, you will output
a short blurb of 2 sentences that lets the student know how they did on the test, 
encourages them to further study topics that they didn't do well on, and commends
them for topics they did do well on. Use a friendly, encouraging, and supportive tone. 
Use emojis in your blurb to make it friendly! Remind them that they don't need to 
know everything right now. Their studying journey is just beginning and with 
their study plan they'll make progress in no time!
Let the student know that based on their results from this diagnostic test, 
the study plan will focus on the topics that they struggled with to help them be
confident and prepared for their test. 

KEYWORD CRITERIA:
Unfamiliar 🔴: The student got all "INCORRECT" for questions pertaining to the topic.
Explanation: "You answered all questions incorrect."

Somewhat Familiar 🟡: The student got some "INCORRECT" and some "CORRECT" for questions pertaining to the topic. 
Explanation: "You answered some questions correct, but some incorrect."

Familiar 🟢: The student got all "CORRECT" for questions pertaining to the topic. 
Explanation: "You answered all questions correct."

OUTPUT:
Strictly output as follows. There may be a smaller or larger number of topics than
what is listed here. Make the topic names and keywords bold in all text that is output.
<topic 1> : <one of the following, based on the critera and the questions in that topic: 'Unfamiliar 🔴', 'Somewhat Familiar 🟡', 'Familiar 🟢'>
<topic 2> : <one of the following, based on the critera and the questions in that topic: 'Unfamiliar 🔴', 'Somewhat Familiar 🟡', 'Familiar 🟢'>
<topic 3> : <one of the following, based on the critera and the questions in that topic: 'Unfamiliar 🔴', 'Somewhat Familiar 🟡', 'Familiar 🟢'>

<2-3 sentence blurb that lets the student know how they did on the test and identifies areas to study further>
"""

overall = """
INSTRUCTIONS:
You are providing insights for a student to guide their studying, based on how 
well they performed on an test. This test is on all topics that the student must study. 
For each topic, you will provide a keyword that lets the student know how 
they did on the questions pertaining to that topic. In addition, you will output
a short blurb of 2 sentences that lets the student know how they did on the test, 
points them to further study topics that they didn't do well on, and commends
them for topics they did do well on. Use a friendly, encouraging, and supportive tone. 
Use emojis in your blurb to make it friendly!

KEYWORD CRITERIA:
Revisit 🔴: The student got all "INCORRECT" for questions pertaining to the topic.
Explanation: "You answered all questions incorrect."

Learning 🟡: The student got some "INCORRECT" and some "CORRECT" for questions pertaining to the topic. 
Explanation: "You answered some questions correct, but some incorrect."

Familiar 🟢: The student got all "CORRECT" for questions pertaining to the topic. 
Explanation: "You answered all questions correct."

OUTPUT:
Strictly output as follows. There may be a smaller or larger number of topics than
what is listed here. Make the topic names and keywords bold in all text that is output.
<topic 1> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Learning 🟡', 'Familiar 🟢'>
<topic 2> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Learning 🟡', 'Familiar 🟢'>
<topic 3> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Learning 🟡', 'Familiar 🟢'>

<2-3 sentence blurb that lets the student know how they did on the test and identifies areas to study further>
"""

insights_instructions = {
  "Check-In Test" : check_in,
  "Diagnostic Test" : initial,
  "Overall Assessment" : overall
}

def shorten_insights(insights):
  response = generate(model = '4o-mini',
    system = shorten_instructions,
    query = "INSIGHTS: " + insights,
    temperature = 0.0,
    lastk = 0,
    session_id = "shorten_insights_session",
    rag_usage = False)

  return response.get("response", "") if isinstance(response, dict) else response

def grade_question(question, student_answer, solution):
  # Check if answer is blank
  if (student_answer == None):
    student_answer = ""

  # Give question to model to grade
  response = generate(model = '4o-mini',
    system = grading_instructions,
    query = "QUESTION: " + question + ", STUDENT'S ANSWER: " + student_answer + ", SOLUTION: " + solution,
    temperature = 0.0,
    lastk = 0,
    session_id = "grading_session",
    rag_usage = False)

  return response.get("response", "") if isinstance(response, dict) else response

def calculate_grade(questions):
  # Calculate percentage grade, number correct, and number incorrect
  correct = sum(1 for ans in questions.values() if ans == 'CORRECT')
  incorrect = sum(1 for ans in questions.values() if ans == 'INCORRECT')
  percent = round(correct / (correct + incorrect) * 100, 0)

  return percent, correct, correct + incorrect

def get_insights(test_type, topics, questions, graded_questions, correct, total):
  # Match questions with grade for the prompt
  student_answers = []
  for q_number in list(questions.keys()):
    student_answers.append(questions[q_number]["question"] + " : " + graded_questions[q_number])
  student_answers = ", ".join(student_answers)

  # Generate insights to guide the student's studying 
  response = generate(model = '4o-mini',
    system = insights_instructions[test_type],
    query = "CORRECT: " + str(correct) + ", TOTAL: " + str(total) + ", TOPICS: " + ", ".join(topics) + ", ANSWERS: " + student_answers,
    temperature = 0.0,
    lastk = 0,
    session_id = st.session_state.session_id,
    rag_usage = False)

  return response.get("response", "") if isinstance(response, dict) else response

def grade_test_page():
  if 'test_submitted' in st.session_state and st.session_state.test_submitted:
    # Retrieve submitted answers
    test_type = st.session_state.test_type
    topics = st.session_state.topics
    questions = st.session_state.questions
    responses = st.session_state.responses
    subject = st.session_state.subject

    # Page elements
    st.title("Study Buddy")
    st.divider()

    # Home button
    if (test_type != "Diagnostic Test"):
      if st.button("Home"):
        # Reset any test session variables
        st.session_state.generate_test = False
        st.session_state.upload_notes = False
        st.session_state.test_input_submitted = False
        st.session_state.test_submitted = False
        st.session_state.generate_check_in = False
        st.session_state.responses = {}

        st.session_state.go_home = True
        st.rerun()

      st.header(subject + " " + test_type) 

    if test_type == "Diagnostic Test":
      col1, col2 = st.columns([2,1])
      st.session_state.header_col = col1
      with col2:
        st.markdown("""
            <div style="background-color: #ECECEC; padding: 20px; border-radius: 10px; width: 100%;">
                <p style="font-size: 20px; margin-top: 0;">Once you finish reviewing your results, generate your customized study plan!</p>
            </div>
            <br>
        """, unsafe_allow_html=True)

        # Styling for the button
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
          
        if st.button("Generate Study Plan", use_container_width=True):
            # Reset any test session variables
            st.session_state.generate_test = False
            st.session_state.upload_notes = False
            st.session_state.test_input_submitted = False
            st.session_state.test_submitted = False
            st.session_state.generate_check_in = False
            st.session_state.responses = {}

            st.session_state.go_home = True
            st.rerun()
      
      with col1:
        st.header(subject + " " + test_type) 

    if (test_type == "Check-In Test"):
      st.subheader("Topics covered: " + ", ".join(topics)) 

    # Grade test
    graded_questions = {}

    progress_text = "Grading your answers..."
    my_bar = st.progress(0, text=progress_text)
    num_questions = len(list(questions.keys()))

    for q_number in list(questions.keys()):
        q_info = questions[q_number]
        q_type = q_info["type"]

        if (q_type == "multiple choice"):
          if (responses[q_number] == q_info["answer"]):
            graded_questions[q_number] = "CORRECT"
          else:
            graded_questions[q_number] = "INCORRECT" 

        else:
          if (responses[q_number] == ""):
            graded_questions[q_number] = "INCORRECT"
          else:
            graded_questions[q_number] = grade_question(q_info["question"],
                                                        responses[q_number],
                                                        q_info["answer"])

        # Update progress bar
        my_bar.progress(q_number / num_questions, text=progress_text)
    my_bar.empty()

    # Output stats and insights
    percent, correct, total = calculate_grade(graded_questions)

    if (test_type == "Diagnostic Test"):
      with st.session_state.header_col:
        st.subheader("Score: " + str(percent) + "%")
        st.subheader(str(correct) + " correct out of " + str(total) + " questions")
    else:
      st.subheader("Score: " + str(percent) + "%")
      st.subheader(str(correct) + " correct out of " + str(total) + " questions")
    st.divider()

    # Save score for home page
    st.session_state.test_stats = {
      "score": str(percent),
      "insights": ""
    }

    # Output scored test
    for q_num in list(questions.keys()):
      mark = graded_questions[q_num]
      student_answer = responses[q_num]
      question_text = "Q" + str(q_num) + ". " + questions[q_num]["question"]

      # Color / icon for correct vs incorrect answers
      icon = "✔"
      color = "green"
      if (mark == "INCORRECT"):
        icon = "✗"  
        color = "red"

      # Check if starred
      starred = st.session_state.starred_questions.get(q_num, False)
      star = ""
      if starred:
        star = "⭐"
      
      # Display each question and the result with an icon
      st.markdown(f"<span style='color:{color};'>{star} {icon} {question_text}</span>", unsafe_allow_html=True)
      
      #st.write(question_text)
      if (student_answer == None):
        student_answer = ""
        
      st.markdown("**Your Answer:** " + student_answer)

      if (mark == "INCORRECT"):
        st.markdown("**Correct Answer:** " + questions[q_num]["answer"])

      st.write("")

    with st.sidebar:
      st.sidebar.title("Insights ✨")
      insights = ""
      with st.spinner("Gathering insights from your results..."):
        insights = get_insights(test_type, topics, questions, graded_questions, correct, total)
      st.write(insights)
      st.session_state.test_stats["insights"] = shorten_insights(insights) # Save insights for home page

      # If diagnostic test, format the insights for the study plan generation
      if (test_type == "Diagnostic Test"):
        # Output message about insights for diagnostic test
        st.write("StudyBuddy will take your familiarity with each topic into account when customizing your study plan! **Each topic will studied at least once**, but less familiar topics will be prioritized.")

        # Format the insights for calendar generation
        statuses = ["Unfamiliar 🔴", "Somewhat Familiar 🟡", "Familiar 🟢"]

        # Use regex to match lines ending in one of those
        pattern = r"^.*: (Unfamiliar 🔴|Somewhat Familiar 🟡|Familiar 🟢)$"
        topics = [line.strip() for line in insights.strip().split('\n') if re.match(pattern, line.strip())]

        # Categorize by status
        categorized = {"Unfamiliar 🔴": [], "Somewhat Familiar 🟡": [], "Familiar 🟢": []}
        for line in topics:
            for status in statuses:
                if line.endswith(status):
                    categorized[status].append(line)
                    break

        # Build output string
        output_str = "CATEGORIZED TOPICS: "
        for status, items in categorized.items():
            output_str += f"\n{status}:\n"
            for item in items:
                output_str += f" - {item}\n"
        st.session_state.diagnostic_results = categorized
        st.session_state.diagnostic_results_str = output_str