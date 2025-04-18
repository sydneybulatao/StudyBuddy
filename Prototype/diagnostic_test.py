import streamlit as st
import os
import time
import re
from llmproxy import pdf_upload, generate
import pprint

def run_diagnostic_test():
    if st.session_state.get("test_input_submitted", False):
        st.rerun()
        return
    else:
        # Otherwise, still need to gather input to generate test
        st.session_state.test_input_submitted = False  # reset this for new test

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
            st.session_state.generate_check_in = False
            st.session_state.responses = {}
            st.session_state.go_home = True
            st.rerun()

        st.header("Check-In Test Generator")
        st.write("Build a custom practice test focused on specific subtopics to help you study.")

        # --- Upload PDFs ---
        # uploaded_files = st.file_uploader("📚 Upload your PDF study materials", type="pdf", accept_multiple_files=True)

        # --- Test Configuration ---
        subject = st.session_state.initial_input.get("course")
        selected_topics = st.session_state.all_study_topics
        question_type = "short answer"

        st.subheader("🧠 Diagnostic Assessment")
        st.write(f"Creating a diagnostic test for: **{subject}**")
        st.write("""
            Welcome to your personalized diagnostic test!  
            This short assessment is designed to evaluate your familiarity with the key topics from your uploaded notes.  

            Please answer each question to the best of your ability. Your results will help tailor your future study plan to focus on the areas where you need the most support.
            """)


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
        #     uploaded_filenames.append(uploaded_file.name

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

        Your job is to generate a **Diagnostic Practice Test** that:
        - Tests the student's understanding across ALL of the following subtopics: {', '.join(selected_topics)}
        - Includes AT LEAST one question for each subtopic
        - Uses ONLY this question format: "short answer"
        - Allows question difficulty to vary naturally — some should be basic, some should require deeper reasoning
        - Keeps the total number of questions reasonable, based on topic count (typically 1–2 per topic)

        You must use ONLY the provided study materials (RAG context). Do NOT use outside knowledge.

        🧠 For each question, think: *What is this question testing, and why is it useful for the student to answer it?* Use this reflection to guide your design, but do NOT include it in your output.

        🔧 Your output must follow this strict format:

        1. Start with a test title in ALL CAPS, based on the subject.
        2. Output the line: --- QUESTIONS ---
        3. Then, for each question:

        - If the format is "short answer":
            Q1: <question text>
            Topic: <subtopic this question tests>

        4. Leave one blank line between each question.
        5. Then output the line: --- ANSWER KEY ---
        6. For each answer:
            Q1: <full text of the correct answer>

        ❗DO NOT include "A", "B", or any letters in the answer key. Only provide the full text of the correct answer.

        Example:
        Q3: What philosopher argued that punishment restores moral balance?
        Topic: Retributive Justice

        Answer:
        Q3: Immanuel Kant
        """

        query = f"Generate a diagnostic practice test for the course '{subject}', designed to assess the student’s familiarity with each of the selected subtopics listed above."

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
                answer_clean = re.sub(r"^Q\d+:\s*", "", answer)
                if question_type == "multiple choice":
                    answer_clean = re.sub(r"^[A-D]\.\s*", "", answer_clean)
                test_data[idx]["answer"] = answer_clean.strip()

        # Update system session variables
        topics_used = list({q_data.get("topic", "Unknown") for q_data in test_data.values()})
        st.session_state.questions = test_data
        st.session_state.test_type = "Diagnostic Test"
        st.session_state.topics = topics_used
        st.session_state.subject = subject
        st.session_state.test_input_submitted = True
        st.session_state.generate_diagnostic = False
        st.rerun()
