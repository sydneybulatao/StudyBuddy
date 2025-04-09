import streamlit as st
import os
import time
import re
from llmproxy import pdf_upload, generate
import pprint

st.set_page_config(page_title="Study Buddy Test Generator", layout="centered")

st.title("📝 Study Buddy – Practice Test Generator")
st.write("Upload your class materials and build a custom practice test to help you study.")

# --- Upload PDFs ---
uploaded_files = st.file_uploader("📚 Upload your PDF study materials", type="pdf", accept_multiple_files=True)

# --- Test Configuration ---
st.subheader("🛠️ Customize Your Test")

with st.form(key='test_form'):
    subject = st.text_input("Subject / Class Name", placeholder="e.g. Philosophy of Law")

    num_questions = st.slider("Number of Questions", min_value=5, max_value=20, value=10)

    question_type = st.selectbox(
        "Question Format",
        options=["multiple choice", "short answer"]
    )

    familiarity = st.slider(
        "How familiar are you with this material?",
        min_value=1, max_value=5, value=3,
        help="1 = not at all familiar, 5 = very familiar"
    )

    submitted = st.form_submit_button("Generate Practice Test")

if submitted:
    st.info("✅ Form submitted! Starting document upload and test generation...")

# Set a constant session ID for now
SESSION_ID = "streamlit-test-session"

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
        st.success(f"Uploaded {uploaded_file.name} ✅")

# Wait a bit to ensure RAG context is indexed
st.info("Indexing uploaded documents...")
time.sleep(8)

st.subheader("📄 Generating Your Practice Test...")
st.info("This may take a moment...")

# Build system prompt
system_prompt = f"""
You are a study assistant generating a practice test for a student based on their uploaded study materials and their inputs for the number of questions and question types.
You MUST generate EXACTLY {num_questions} questions. Do not generate any more or any fewer than {num_questions} questions.
All questions MUST be of type: "{question_type}". Do not include any other types.
Use ONLY the content found in the uploaded study materials (RAG context). Do NOT introduce any external knowledge.
The student has rated their familiarity with the material as a {familiarity}/5.
Tailor the difficulty accordingly:
- A familiarity of 1 or 2 means easier, foundational questions.
- A familiarity of 4 or 5 means more advanced and nuanced questions that connect larger themes.
The questions should be designed to help the student study and prepare for an exam.

You must strictly follow this output format:

1. First, output the test name in ALL CAPS based on the subject.
2. Then output the line: --- QUESTIONS --- (in ALL CAPS).
3. Then, for each question:

- If the format is "short answer":
    Q1: <question text>

- If the format is "multiple choice":
    Q1: <question text>
    A. <option A>
    B. <option B>
    C. <option C>
    D. <option D>

Leave a blank line between each question.

4. Finally output the line: --- ANSWER KEY --- (in ALL CAPS).
After this line, return the answer for each question. Each answer must return the **full text** of the correct choice (NOT just a letter or letter + period).

Leave a blank line between each answer.
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

# Preview test_data dictionary
with st.expander("🧠 View Parsed Test Data (Dictionary Format)"):
    st.code(pprint.pformat(test_data, sort_dicts=False))


