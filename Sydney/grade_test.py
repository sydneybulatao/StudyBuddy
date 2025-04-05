### Grades test and provides actionable feedback to the student based on answers.

import streamlit as st
from llmproxy import generate

# TODO: maybe add explanation to why wrong/what was missing? 
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
a short blurb of 2-3 sentences that lets the student know how well they did on the test, 
encourages them to further study topics that they didn't do well on, and commends
them for topics they did do well on. Use a friendly, encouraging, and supportive tone. 
Especially if they got less than half of the questions right, make sure you let them know 
that they didn't do well on the test and should put some more work into studying,
but still use an encouraging tone. Also use emojis in your blurb to make it friendly!

KEYWORD CRITERIA:
Revisit 🔴: The student got all "INCORRECT" for questions pertaining to the topic.
Explanation: "You answered all questions incorrect."

Refine 🟡: The student got some "INCORRECT" and some "CORRECT" for questions pertaining to the topic. 
Explanation: "You answered some questions correct, but some incorrect."

Mastered 🟢: The student got all "CORRECT" for questions pertaining to the topic. 
Explanation: "You answered all questions correct."

OUTPUT:
Strictly output as follows. There may be a smaller or larger number of topics than
what is listed here. Make the topic names and keywords bold in all text that is output.
<topic 1> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Refine 🟡', 'Mastered 🟢'>
<keyword explanation for topic 1>
<topic 2> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Refine 🟡', 'Mastered 🟢'>
<keyword explanation for topic 2> 
<topic 3> : <one of the following, based on the critera and the questions in that topic: 'Revisit 🔴', 'Refine 🟡', 'Mastered 🟢'>
<keyword explanation for topic 3>

<2-3 sentence blurb that lets the student know how well they did on the test and identifies areas to study further>
"""

initial = """
"""

final = """
"""

insights_instructions = {
  "Check-In Test" : check_in,
  "Initial Assessment" : initial,
  "Final Assessment" : final
}

def grade_question(question, student_answer, solution):
  # Give question to model to grade
  response = generate(model = '4o-mini',
    system = grading_instructions,
    query = "QUESTION: " + question + ", STUDENT'S ANSWER: " + student_answer + ", SOLUTION: " + solution,
    temperature = 0.0,
    lastk = 0,
    session_id = "grading_session",
    rag_usage = False)

  return response['response']

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
    session_id = "insights_session",
    rag_usage = False)

  return response["response"]

def grade_test_page():
  if 'test_submitted' in st.session_state and st.session_state.test_submitted:
    # Retrieve submitted answers
    test_type = st.session_state.test_type
    topics = st.session_state.topics
    questions = st.session_state.questions
    responses = st.session_state.responses

    # Page elements
    st.title("Graded " + test_type)

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

        elif (q_type == "short answer"):
          graded_questions[q_number] = grade_question(q_info["question"],
                                                      responses[q_number],
                                                      q_info["answer"])
        
        # Update progress bar
        my_bar.progress(q_number / num_questions, text=progress_text)
    my_bar.empty()

    # Output stats and insights
    percent, correct, total = calculate_grade(graded_questions)
    st.subheader("Score: " + str(percent) + "%")
    st.subheader(str(correct) + " correct out of " + str(total) + " questions")
    st.divider()

    # Output scored test
    for q_num in list(questions.keys()):
      mark = graded_questions[q_num]
      student_answer = responses[q_num]
      question_text = "Q" + str(q_num) + ". " + questions[q_num]["question"]

      # Color / icon for correct vs incorrect answers
      icon = "✅"
      color = "green"
      if (mark == "INCORRECT"):
        icon = "❌"  
        color = "red"
      
      # Display each question and the result with an icon
      st.markdown(f"<span style='color:{color};'>{icon} {question_text}</span>", unsafe_allow_html=True)
      
      #st.write(question_text)
      st.markdown("**Your Answer:** " + student_answer)

      if (mark == "INCORRECT"):
        st.markdown("**Correct Answer:** " + questions[q_num]["answer"])

      st.write("")

    with st.sidebar:
      insights = ""
      with st.spinner("Gathering insights from your results..."):
        insights = get_insights(test_type, topics, questions, graded_questions, correct, total)
      st.subheader("Insights ✨")
      st.write(insights)