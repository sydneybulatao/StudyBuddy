import streamlit as st
import os
import time
import re
from llmproxy import pdf_upload, generate
import pprint
from take_test import take_test_page

def generate_test_page():
  if 'test_input_submitted' in st.session_state and st.session_state.test_input_submitted:
    take_test_page() # Move on to taking the test
    return
  else:
    # Otherwise, still need to gather input to generate test
    st.session_state.test_input_submitted = False # reset this for new test

    # Page styling
    st.title("Study Buddy 🌿•₊✧💻⋆⭒˚☕️｡⋆")
    st.header("Practice Test Generator")
    st.write("Upload your class materials and build a custom practice test to help you study.")

    # --- Upload PDFs ---
    uploaded_files = st.file_uploader("📚 Upload your PDF study materials", type="pdf", accept_multiple_files=True)

    # --- Test Configuration ---
    st.subheader("🛠️ Customize Your Test")
    st.session_state.test_input = {}

    with st.form(key='test_form'):
        st.session_state.test_input["subject"] = st.text_input("Subject / Class Name", placeholder="e.g. Philosophy of Law")

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

        st.session_state.test_input_submitted = st.form_submit_button("Generate Practice Test")

    if st.session_state.test_input_submitted:
      # TODO: form verification - ensure all questions answered or attempted
      st.success("Form submitted! Starting document upload and test generation...")

      # Get test input
      subject = st.session_state.test_input["subject"]
      num_questions = st.session_state.test_input["num_questions"]
      question_type = st.session_state.test_input["question_type"]
      familiarity = st.session_state.test_input["familiarity"]

      # Set a constant session ID for now
      # TODO: create a unique session ID for each student
      SESSION_ID = "streamlit-test-session-8-9"

      # Create temp dir to save uploaded PDFs
      TEMP_DIR = "temp_uploads"
      os.makedirs(TEMP_DIR, exist_ok=True)

      uploaded_filenames = []

      # Upload PDFs to RAG
      for uploaded_file in uploaded_files:
          file_path = os.path.join(TEMP_DIR, uploaded_file.name)
          with open(file_path, "wb") as f:
              f.write(uploaded_file.getbuffer())
          uploaded_filenames.append(uploaded_file.name)
          
          with st.spinner(f"Uploading {uploaded_file.name} to RAG..."):
              response = pdf_upload(
                  path=file_path,
                  strategy='smart',
                  session_id=SESSION_ID
              )
              st.success(f"Uploaded {uploaded_file.name}")

      # TODO: create a unique folder to store each students' notes 

      # Wait a bit to ensure RAG context is indexed
      st.info("Indexing uploaded documents...")
      time.sleep(8)

      st.subheader("📄 Generating Your Practice Test...")
      st.info("This may take a moment...")

      # Build system prompt
      system_prompt = f"""
        You are a helpful, smart study assistant that creates high-quality practice tests for students using their uploaded notes.

        Your role is to generate a test that:
        - Helps the student review key ideas from the material
        - Matches the desired number of questions: EXACTLY {num_questions}
        - Uses ONLY this question type: "{question_type}"
        - Reflects the student's familiarity level: {familiarity}/5 (1 = beginner, 5 = advanced)

        DO NOT include any external facts or knowledge not found in the uploaded materials. Use only the provided content.

        You must strictly follow the output format below:

        1. The first line is the TEST TITLE in ALL CAPS, based on the subject.
        2. The next line must be: --- QUESTIONS ---
        3. For each question:

        - If short answer:
            Q1: <question text>

        - If multiple choice:
            Q1: <question text>
            A. <option A>
            B. <option B>
            C. <option C>
            D. <option D>

        4. Leave one blank line between each question.

        5. Then output the line: --- ANSWER KEY ---
        6. For each answer, write:
            Q1: <full text of correct answer choice>

        ✅ For multiple choice, DO NOT write "A", "B", or any letters in the answer. Just output the correct choice as plain text. This is critical for grading.

        💡 Make sure each question serves a purpose:
        - Cover a variety of key themes or facts from the material
        - Include both recall and reasoning-based prompts (especially if familiarity is high)
        - Tie each question to a learning outcome (even if not shown)

        Examples of weak questions:
        - "What is something mentioned in the text?" (too vague)
        - "True or false" (not allowed)

        Examples of strong questions:
        - "According to the lecture, what was the key reason for the policy shift?"
        - "Which of the following best explains the main idea of section 3?"

        You must generate exactly {num_questions} well-structured, relevant questions with consistent formatting.
        """

      query = f"Please generate a practice test for a class called '{subject}'. Use only the uploaded class notes or study materials available in the session context."

      response = generate(
          model='azure-phi3',
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
          st.error("❌ Could not find the answer key in the output.")
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
              if question_type == "multiple choice":
                  test_data[idx]["answer"] = re.sub(r"^Q\d+:\s*[A-D]\.\s*", "", answer)
              else:
                  test_data[idx]["answer"] = re.sub(r"^Q\d+:\s*", "", answer)

      # Update system session variables
      # Test information
      st.session_state.questions = test_data
      st.session_state.test_type = "Initial Assessment"
      st.session_state.topics = ["All Topics"]
      st.session_state.subject = subject

      st.session_state.test_input_submitted = True
      st.rerun()

      # # Preview test_data dictionary
      # with st.expander("🧠 View Parsed Test Data (Dictionary Format)"):
      #     st.code(pprint.pformat(test_data, sort_dicts=False))

generate_test_page()