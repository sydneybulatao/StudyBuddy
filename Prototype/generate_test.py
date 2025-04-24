import streamlit as st
import os
import time
import re
from llmproxy import pdf_upload, generate
import pprint

def generate_test_page():
  if st.session_state.get("test_input_submitted", False):
    st.rerun()
    return
  else:
    # Otherwise, still need to gather input to generate test
    st.session_state.test_input_submitted = False # reset this for new test

    # Page styling
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

    st.header("Overall Practice Test Generator")
    st.write("Build a custom practice test, based on all study topics.")
    st.write("We recommend taking this test at the end of your studying journey to assess your overall knowledge.")

    # --- Test Configuration ---
    subject = st.session_state.initial_input.get("course")
    st.subheader("🛠️ Customize Your Test")
    st.write("Subject: " + subject)
    st.session_state.test_input = {}
    submit = False

    with st.form(key='test_form'):
      st.session_state.test_input["num_questions"] = st.slider("Number of Questions", min_value=5, max_value=20, value=10)

      st.session_state.test_input["question_type"] = st.selectbox(
          "Question Format",
          options=["multiple choice", "short answer"]
      )

      st.session_state.test_input["familiarity"] = st.slider(
          "How familiar are you with this material?",
          min_value=1, max_value=5, value=3,
          help="1 = not at all familiar, 5 = very familiar"
      )

      submit = st.form_submit_button("Generate Practice Test")

    if submit:
      st.success("Form submitted! Starting test generation...")

      # Get test input
      num_questions = st.session_state.test_input["num_questions"]
      question_type = st.session_state.test_input["question_type"]
      familiarity = st.session_state.test_input["familiarity"]

      SESSION_ID = st.session_state.session_id

      st.subheader("📄 Generating Your Practice Test...")
      st.info("This may take a moment...")

      # Build system prompt
      system_prompt = f"""
        You are a smart and helpful study assistant that creates high-quality, relevant practice tests based on uploaded class materials and student preferences.

        Your job is to generate a practice test that:
        - Contains EXACTLY {num_questions} questions — no more, no less.
        - Uses ONLY this question format: "{question_type}"
        - Aligns with the student's familiarity rating of {familiarity}/5:
        - 1-2 = easier questions on basic ideas and definitions.
        - 3 = mixed difficulty, with some reasoning or applied questions.
        - 4-5 = advanced questions requiring interpretation, nuance, or synthesis.

        You must use ONLY the provided study materials (RAG context). Do NOT use outside knowledge.

        🧠 For each question, think: *What is this question testing, and why is it useful for the student to answer it?* Use this reflection to guide your design, but do NOT include it in your output.

        🔧 Your output must follow this strict format:

        1. Start with a test title in ALL CAPS, based on the subject.
        2. Output the line: --- QUESTIONS ---
        3. Then, for each question:

        - If the format is "short answer":
            Q1: <question text>

        - If the format is "multiple choice":
            Q1: <question text>
            A. <option A>
            B. <option B>
            C. <option C>
            D. <option D>

        4. Leave one blank line between each question.
        5. Then output the line: --- ANSWER KEY ---
        6. For each answer:
            Q1: <full text of the correct answer choice>

        ❗DO NOT include "A", "B", or any letters in the answer key. Only provide the full text of the correct option — nothing else.

        Example:
        Q3: The philosopher who developed the theory of justice as fairness is:
        A. Aristotle
        B. John Rawls
        C. H.L.A. Hart
        D. Jeremy Bentham

        Answer:
        Q3: John Rawls
        """
      
      query = f"Please generate a practice test for a class called '{subject}'. Use only the uploaded class notes or study materials available in the session context."

      response = generate(
          model='4o-mini',
          system=system_prompt,
          query=query,
          temperature=0.0,
          lastk=0,
          session_id=SESSION_ID,
          rag_usage=True,
          rag_threshold=0.2,
          rag_k=2
      )

      raw_output = response.get("response", "") if isinstance(response, dict) else response
      st.success("✅ Test generated!")

      # --- Parse output ---
      lines = raw_output.splitlines()
      question_pattern = re.compile(r"^Q(\d+): (.+)")
      choice_pattern = re.compile(r"^[A-D]\. (.+)")
      try:
        answer_key_start = lines.index("--- ANSWER KEY ---")
      except ValueError:
        st.error("Error: Could not generate answer key.")
        st.stop()

      test_data = {}
      current_q = None

      for i, line in enumerate(lines):
        if i > answer_key_start:
          break
        q_match = question_pattern.match(line)
        if q_match:
          current_q = int(q_match.group(1))
          test_data[current_q] = {
              "question_number": current_q,
              "question": q_match.group(2).strip(),
              "type": "short answer" if question_type == "short answer" else "multiple choice"
          }
          continue
        if current_q and question_type == "multiple choice":
          c_match = choice_pattern.match(line)
          if c_match:
            test_data[current_q].setdefault("choices", []).append(c_match.group(1).strip())

      # Extract answers
      answers = [l.strip() for l in lines[answer_key_start + 1:] if l.strip()]
      for idx, answer in enumerate(answers, 1):
        if idx in test_data:
          # Clean answer formatting for both short answer and MC
          answer_clean = re.sub(r"^Q\d+:\s*", "", answer)
          if question_type == "multiple choice":
            answer_clean = re.sub(r"^[A-D]\.\s*", "", answer_clean)
          test_data[idx]["answer"] = answer_clean.strip()


      # Update system session variables
      # Test information
      st.session_state.questions = test_data
      st.session_state.test_type = "Overall Assessment"
      st.session_state.topics = st.session_state.all_topics
      st.session_state.subject = subject

      st.session_state.test_input_submitted = True
      st.rerun()