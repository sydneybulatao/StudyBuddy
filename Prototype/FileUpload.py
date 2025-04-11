# # File upload logic

# from llmproxy import generate, pdf_upload, retrieve
# import time
# import os
# import re
# from string import Template

# SESSION_ID = 'summary_generator'

# def upload_documents_for_rag():
#     context_dir = "RagContext"
#     for filename in os.listdir(context_dir):
#         if filename.lower().endswith('.pdf'):
#             path = os.path.join(context_dir, filename)
#             print(f"Uploading {path} to RAG...")
#             response = pdf_upload(
#                 path=path,
#                 strategy='smart',
#                 session_id=SESSION_ID
#             )
#             print(f"Uploaded: {response}")

#     # generate summary of documents and summarize info that user uploads

# def generate_summary(rag_context):
#     context_string = ""

#     i=1
#     for collection in rag_context:
    
#         if not context_string:
#             context_string = """The following is additional context that may be helpful in answering the user's query."""

#         context_string += """
#         #{} {}
#         """.format(i, collection['doc_summary'])
#         j=1
#         for chunk in collection['chunks']:
#             context_string+= """
#             #{}.{} {}
#             """.format(i,j, chunk)
#             j+=1
#         i+=1
#     return context_string

# if __name__ == '__main__':
#     # Starting screen and information
#     print("--- Notes Summary ---")
#     print("This part generates a note summary based on the files that are uploaded.\n")
#     input("Press Enter to proceed...")
#     upload_documents_for_rag()

#     print("Waiting for uploaded documents to be indexed...")
#     time.sleep(10)
#     os.system('clear')

#     # document is already added to RAG_context
#     # Query used to retrieve relevant context
#     query = 'Generate a list of topics for a study guide based on all of the documents in the rag context.'

#     # assuming some document(s) has previously been uploaded to session_id=RAG
#     rag_context = retrieve(
#         query =query,
#         session_id=SESSION_ID,
#         rag_threshold = 0.2,
#         rag_k = 3)

#     # combining query with rag_context
#     query_with_rag_context = Template("$query\n$rag_context").substitute(
#                             query=query,
#                             rag_context=generate_summary(rag_context))
#     print(query_with_rag_context)

#     # Pass to LLM using a different session (session_id=GenericSession)
#     # You can also set rag_usage=True to use RAG context from GenericSession
#     response = generate(model = '4o-mini',
#         system = 'Answer my question',
#         query = query_with_rag_context,
#         temperature=0.0,
#         lastk=0,
#         session_id=SESSION_ID,
#         rag_usage = False
#         )

#     print(response)

# File: /Users/clarkbolin/Desktop/CS150/StudyBuddy/Clark/FileUpload.py

from llmproxy import generate, pdf_upload, retrieve
import tempfile
import time
from string import Template
import streamlit as st

SESSION_ID = 'hiba-meeting'

def summarize_uploaded_file(file_name: str) -> str:
    query = f"Summarize the document: {file_name}"
    
    rag_context = retrieve(
        query=query,
        session_id=st.session_state.session_id,
        rag_threshold=0.2,
        rag_k=3
    )

    return generate_summary(rag_context)

def generate_summary(rag_context: list) -> str:
    context_string = ""
    i = 1
    for collection in rag_context:
        if not context_string:
            context_string = "Summary based on document content:\n"
        context_string += f"\n#{i} {collection['doc_summary']}\n"
        j = 1
        for chunk in collection['chunks']:
            context_string += f"#{i}.{j} {chunk}\n"
            j += 1
        i += 1
    return context_string

def upload_file_to_rag(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    response = pdf_upload(
        path=tmp_path,
        strategy='smart',
        session_id=st.session_state.session_id
    )
    time.sleep(10)  # Wait to ensure indexing
    print(response)
    return uploaded_file.name