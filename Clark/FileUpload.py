# File upload logic

from llmproxy import generate, pdf_upload, retrieve
import time
import os
import re
from string import Template

SESSION_ID = 'test-generator'

def upload_documents_for_rag():
    context_dir = "RagContext"
    for filename in os.listdir(context_dir):
        if filename.lower().endswith('.pdf'):
            path = os.path.join(context_dir, filename)
            print(f"Uploading {path} to RAG...")
            response = pdf_upload(
                path=path,
                strategy='smart',
                session_id=SESSION_ID
            )
            print(f"Uploaded: {response}")

def generate_summary(rag_context):
    context_string = ""

    i=1
    for collection in rag_context:
    
        if not context_string:
            context_string = """The following is additional context that may be helpful in answering the user's query."""

        context_string += """
        #{} {}
        """.format(i, collection['doc_summary'])
        j=1
        for chunk in collection['chunks']:
            context_string+= """
            #{}.{} {}
            """.format(i,j, chunk)
            j+=1
        i+=1
    return context_string

if __name__ == '__main__':
    # Starting screen and information
    print("--- Notes Summary ---")
    print("This part generates a note summary based on the files that are uploaded.\n")
    input("Press Enter to proceed...")
    upload_documents_for_rag()

    print("Waiting for uploaded documents to be indexed...")
    time.sleep(10)
    os.system('clear')

    # document is already added to RAG_context
    # Query used to retrieve relevant context
    query = 'Summarize the most recently uploaded rag document.'

    # assuming some document(s) has previously been uploaded to session_id=RAG
    rag_context = retrieve(
        query =query,
        session_id=SESSION_ID,
        rag_threshold = 0.2,
        rag_k = 3)

    # combining query with rag_context
    query_with_rag_context = Template("$query\n$rag_context").substitute(
                            query=query,
                            rag_context=generate_summary(rag_context))
    print(query_with_rag_context)

    # Pass to LLM using a different session (session_id=GenericSession)
    # You can also set rag_usage=True to use RAG context from GenericSession
    response = generate(model = '4o-mini',
        system = 'Answer my question',
        query = query_with_rag_context,
        temperature=0.0,
        lastk=0,
        session_id=SESSION_ID,
        rag_usage = False
        )

    print(response)