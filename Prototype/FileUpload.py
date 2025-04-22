# File: /Users/clarkbolin/Desktop/CS150/StudyBuddy/Prototype/FileUpload.py

from llmproxy import generate, pdf_upload, retrieve
import tempfile
import time
import streamlit as st
from typing import List, Tuple

def summarize_uploaded_file(file_name: str) -> Tuple[str, List[str]]:
    """Retrieve, summarize, and extract study topics from uploaded file."""
    query = f"Summarize the document: {file_name}"
    
    rag_context = retrieve(
        query=query,
        session_id=st.session_state.session_id,
        rag_threshold=0.2,
        rag_k=3
    )

    print(rag_context)

    return generate_summary(rag_context)

def generate_summary(rag_context: list) -> Tuple[str, List[str]]:
    """Generate a clean, structured summary and extract study topics with fallback safety."""
    if not rag_context:
        return "No context available to summarize.", []

    # Step 1: Merge context safely
    merged_text = ""
    for collection in rag_context:
        if isinstance(collection, dict):
            merged_text += collection.get('doc_summary', '') + "\n\n"
            merged_text += "\n".join(collection.get('chunks', [])) + "\n\n"
        else:
            merged_text += str(collection) + "\n\n"

    # Step 2: Ask LLM to summarize
    prompt = f"""
You are a helpful study assistant.

Your task is to generate a clean and structured summary of the following class notes. Your output should help a student identify the **main topics** they need to focus on when studying.

INSTRUCTIONS:

1. First, write a brief high-level summary of the document. Use the heading: `### Overall Summary`.

2. Then generate a list of the **main study topics**. Use the heading: `### Study Topics`.

3. Each topic should be written as a single bullet point, bolded using Markdown (`**Topic Name**`). 

4. Do **not** include any sub-bullets or explanations — just the list of bolded topics.

5. Only include topics that are clearly and meaningfully present in the document. Do **not** invent or extrapolate subtopics. 

6. Always avoid redundancy, overly narrow topics, or vague phrasing.

---

Here are the raw notes to process:

{merged_text}
"""

    response = generate(
        model="4o-mini",
        system="Study Summarizer",
        query=prompt,
        temperature=0.2,
        lastk=0,
        session_id=st.session_state.session_id,
        rag_usage=False
    )

    summary_text = response['response'] if isinstance(response, dict) else str(response)

    # Step 3: Extract bolded study topics
    study_topics = []
    lines = summary_text.splitlines()
    collecting_topics = False

    for line in lines:
        line = line.strip()
        if line.lower().startswith("### study topics"):
            collecting_topics = True
            continue
        if collecting_topics:
            if line.startswith("-"):
                clean_topic = line.lstrip("- ").strip()
                if clean_topic.startswith("**") and clean_topic.endswith("**"):
                    clean_topic = clean_topic.replace("**", "").strip()
                    if clean_topic:
                        study_topics.append(clean_topic)
            elif line.startswith("###"):
                break

    return summary_text, study_topics

def upload_file_to_rag(uploaded_file):
    """Upload a PDF file to RAG system."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    response = pdf_upload(
        path=tmp_path,
        strategy='smart',
        session_id=st.session_state.session_id
    )
    time.sleep(10)  # Ensure RAG indexes the document
    print(response)
    return uploaded_file.name