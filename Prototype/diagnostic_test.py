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

        # --- Test Configuration ---
        subject = st.session_state.initial_input.get("course")
        selected_topics = st.session_state.all_study_topics
        question_type = "multiple choice"

        st.header(f"{subject} Diagnostic Test")
        st.subheader("📄 Generating Diagnostic Test...")

        SESSION_ID = st.session_state.session_id
        st.info("This may take a moment...")

        # Build system prompt
        system_prompt = f"""
        You are a smart and helpful study assistant that creates high-quality, relevant practice tests based on uploaded class materials and student preferences.
        You are creating these tests for college students at Tufts University, a leading university in the United States. The intricacy and depth of the questions you ask should be appropriate for students of this level .

        Your job is to generate a **Diagnostic Practice Test** that:
        - Tests the student's understanding across ALL of the following subtopics: {', '.join(selected_topics)}
        - Includes AT LEAST one question for each subtopic
        - Uses ONLY this question format: "multiple choice"
        - Allows question difficulty to vary naturally — some should be basic, some should require deeper reasoning
        - Keeps the total number of questions reasonable, based on topic count (typically 1–2 per topic)

        You must use ONLY the provided study materials (RAG context). Do NOT use outside knowledge.

        🧠 For each question, think: *What is this question testing, and why is it useful for the student to answer it?* Use this reflection to guide your design, but do NOT include it in your output.

        🔧 Your output must follow this strict format:

        1. Start with a test title in ALL CAPS, based on the subject.
        2. Output the line: --- QUESTIONS ---
        3. Then, for each question:

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
            Q1: <full text of the correct answer>

        ❗DO NOT include "A", "B", or any letters in the answer key. Only provide the full text of the correct answer.

        EXAMPLE QUESTIONS:
        If the student is taking a Generative AI class and has provided a slide deck that contains information about using Agents and Agentic Workflow, strong questions could be:

        Q1: What is the main reason that LLMs alone struggle with complex, multi-step tasks?
        A. They are trained mostly on outdated internet data
        B. They lack built-in access to high-speed computation
        C. They generate responses in isolation without memory or planning
        D. They are too expensive to deploy on mobile devices
        Topic: Limitations of Traditional LLMs

        Answer:
        Q1: They generate responses in isolation without memory or planning

        Q2: In a tool-augmented agentic workflow, what advantage does the agent gain from using a tool like a search engine or code interpreter?
        A. The agent can delegate tasks to human users
        B. The agent can generate content in multiple languages simultaneously
        C. The agent can interact with external systems to gather information or perform actions
        D. The agent becomes capable of modifying its own model weights
        Topic: Components of Agentic Workflows

        Answer:
        Q2: The agent can interact with external systems to gather information or perform actions
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
