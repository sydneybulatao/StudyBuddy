import streamlit as st
import os
import time
import re
from llmproxy import pdf_upload, generate
import pprint

def generate_check_in_test_page():
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
    if st.button("Home", type='primary'):
      # Reset any test session variables
      st.session_state.generate_test = False
      st.session_state.upload_notes = False
      st.session_state.test_input_submitted = False
      st.session_state.test_submitted = False
      st.session_state.generate_check_in = False

      st.session_state.responses = {}

      st.session_state.go_home = True
      st.rerun()

    # ✅ Insert popup control here
    if 'show_check_in_popup' not in st.session_state:
        st.session_state.show_check_in_popup = True

    if st.session_state.show_check_in_popup:
        with st.expander("📝 Welcome to Your Custom Practice Test!", expanded=True):
              st.markdown("""
              Here's how to set up your test:

              - **Choose Topics**: Select one or more subtopics you want to be tested on. *(You can also select 'All' to be tested on everything.)*
              - **Number of Questions**: Pick how many questions you want — between 5 and 20.
              - **Question Format**: Choose whether you want **multiple choice** or **short answer** questions.
              - **Familiarity Slider**: Select how familiar you are with the material.  
                - Lower values = easier, more basic questions.  
                - Higher values = harder, more in-depth questions.

              ---

            🔔 **Please Note**:  
            The questions generated are strictly conceptual and are designed to test if you have studied the uploaded material.  
            They are not guaranteed to cover every nuance or ensure complete mastery of the topics.
            """)

    st.header("Check-In Test Generator")
    st.write("Build a custom practice test focused on specific subtopics to help you study.")

    # --- Upload PDFs ---
    #uploaded_files = st.file_uploader("📚 Upload your PDF study materials", type="pdf", accept_multiple_files=True)

    # --- Test Configuration ---
    subject = st.session_state.initial_input.get("course")
    all_topics = st.session_state.all_study_topics

    st.subheader("🛠️ Customize Your Check-In Test")
    st.write("Subject: " + subject)
    st.write("Select the specific topics you want to be tested on:")

    # 🔵 Insert "All" as an option
    options_with_all = ["All"] + all_topics

    # 🔵 Multiselect from options including "All"
    selected_options = st.multiselect("📚 Choose Topics", options_with_all)

    # 🔵 If "All" is selected, automatically select all real topics
    if "All" in selected_options:
        final_selected_topics = all_topics
    else:
        final_selected_topics = selected_options

    # 🔵 Save into session state or whatever you're using
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

      st.session_state.test_input["selected_topics"] = selected_topics

      submit = st.form_submit_button("Generate Practice Test")

    if submit:
      st.success("Form submitted! Starting test generation...")

      # Get test input
      num_questions = st.session_state.test_input["num_questions"]
      question_type = st.session_state.test_input["question_type"]
      familiarity = st.session_state.test_input["familiarity"]

      SESSION_ID = st.session_state.session_id

      # Create temp dir to save uploaded PDFs
      # TEMP_DIR = "temp_uploads"
      # os.makedirs(TEMP_DIR, exist_ok=True)

      # uploaded_filenames = []

      # # Upload PDFs to RAG
      # for uploaded_file in uploaded_files:
      #     file_path = os.path.join(TEMP_DIR, uploaded_file.name)
      #     with open(file_path, "wb") as f:
      #         f.write(uploaded_file.getbuffer())
      #     uploaded_filenames.append(uploaded_file.name)
          
      #     with st.spinner(f"Uploading {uploaded_file.name} to RAG..."):
      #         response = pdf_upload(
      #             path=file_path,
      #             strategy='smart',
      #             session_id=SESSION_ID
      #         )
      #         st.success(f"Uploaded {uploaded_file.name}")

      # Wait a bit to ensure RAG context is indexed
      # st.info("Indexing uploaded documents...")
      # time.sleep(8)

      st.subheader("📄 Generating Your Practice Test...")
      st.info("This may take a moment...")

      # Build system prompt
      system_prompt = f"""
        You are a smart and helpful study assistant that creates high-quality, relevant practice tests based on uploaded class materials and student preferences.

        Your job is to generate a **Check-In Practice Test** that:
        - Contains EXACTLY {num_questions} questions — no more, no less.
        - Uses ONLY this question format: "{question_type}"
        - Focuses ONLY on the following selected subtopics: {', '.join(selected_topics)}
        - Aligns with the student's familiarity rating of {familiarity}/5:
        - 1-2 = easier questions on basic ideas and definitions.
        - 3 = mixed difficulty, with some reasoning or applied questions.
        - 4-5 = advanced questions requiring interpretation, nuance, or synthesis.
        - Includes AT LEAST one question for EACH of the selected subtopics.
        - Clearly indicate which subtopic each question is testing.

        You must use ONLY the provided study materials (RAG context). Do NOT use outside knowledge.

        🧠 For each question, think: *What is this question testing, and why is it useful for the student to answer it?* Use this reflection to guide your design, but do NOT include it in your output.

        🔧 Your output must follow this strict format:

        1. Start with a test title in ALL CAPS, based on the subject.
        2. Output the line: --- QUESTIONS ---
        3. Then, for each question:

        - If the format is "short answer":
            Q1: <question text>
            Topic: <subtopic this question tests>

        - If the format is "multiple choice":
            Q1: <question text>
            A. <option A>
            B. <option B>
            C. <option C>
            D. <option D>
            Topic: <subtopic this question tests>

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
        Topic: Justice Theories

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
        st.error("Error: .")
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
        if current_q:
            if question_type == "multiple choice":
                c_match = choice_pattern.match(line)
                if c_match:
                    test_data[current_q].setdefault("choices", []).append(c_match.group(1).strip())

            if line.lower().startswith("topic:"):
                topic_name = line.split(":", 1)[1].strip()
                test_data[current_q]["topic"] = topic_name

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
      topics_used = list({q_data.get("topic", "Unknown") for q_data in test_data.values()})
      # Update system session variables
      # Test information
      st.session_state.questions = test_data
      st.session_state.test_type = "Check-In Test"
      st.session_state.topics = topics_used
      st.session_state.subject = subject

      st.session_state.test_input_submitted = True
      st.rerun()