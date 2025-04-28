# Practice Test Generator with RAG

from llmproxy import generate, pdf_upload
import time
import os
import re

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


if __name__ == '__main__':
  # Starting screen and information
  print("--- Practice Test Generator ---")
  print("This program allows you to generate practice tests based on what you are currently studying.")
  print("")
  input("Press Enter to proceed...")
  upload_documents_for_rag()

  print("Waiting for uploaded documents to be indexed...")
  time.sleep(10)
  os.system('clear')


  # Ask for subject and question format
  print("--- Customize Your Test ---")
  subject = input("Subject / Class Name: ")

  validNum = False
  while (not validNum):
    numQ = int(input("Number of questions (5-20): "))
    if (numQ > 20 or numQ < 5):
      print("Invalid number of questions.")
    else:
      validNum = True

  validFormat = False
  validFormats = ["multiple choice", "short answer"]
  while (not validFormat):
    format = input("Question format (multiple choice / short answer): ").lower()
    if (format in validFormats):
      validFormat = True
    else:
      print("Invalid format type.")

  # Generate test 
  os.system('clear')
  print("--- Generating Your Test ---")
  print("This may take a moment...")
  
  # Format system prompt
  system = (
    "You are a study assistant generating a practice test for a student based on their uploaded study materials. "
    "You must only use the content found in the RAG context and avoid introducing external knowledge. "
    "Your test must be accurate, relevant to the documents, and well-structured.\n\n"
    "Format the test as follows:\n"
    "1. First, output the test name in ALL CAPS based on the subject.\n"
    "2. Then output '--- QUESTIONS ---' in ALL CAPS.\n"
    "3. Then output exactly " + str(numQ) + " questions in " + format + " format, one after the other, each separated by a blank line.\n"
    "4. Finally, output '--- ANSWER KEY ---' in ALL CAPS followed by correct answers for each question with blank lines in between.\n"
  )

  # Format query
  query = "Please generate a practice test for a class called '" + subject + "'. Use only the uploaded class notes or study materials available in the session context."

  response = generate(
  model = 'azure-phi3',
  system = system,
  query = query,
  temperature = 0.0,
  lastk = 0,
  session_id = SESSION_ID,
  rag_usage = True,
  rag_threshold = 0.1,
  rag_k = 5
)
  os.system('clear')

print("--- DOCUMENTS USED ---")
docs = [f for f in os.listdir("RagContext") if f.lower().endswith('.pdf')]
if docs:
    for doc in docs:
        print(f"- {doc}")
else:
    print("No documents were found in RagContext.")


# print("\n--- GENERATED PRACTICE TEST ---")
# print(response.get("response", response))

# --- Parse test into questions + answers ---
raw_output = response.get("response", response)

# Split by the answer key section
if "--- ANSWER KEY ---" in raw_output:
    question_block, answer_block = raw_output.split("--- ANSWER KEY ---", 1)
else:
    question_block = raw_output
    answer_block = ""

# Match all questions (with or without choices)
question_pattern = re.compile(
    r"(\d+)\.\s+(.*?)\n\n((?:[A-D]\.\s+.*?\n){0,4})",
    re.DOTALL
)

# Match individual choices (A., B., etc.)
choice_pattern = re.compile(r"[A-D]\.\s+(.*)")

# Match answers (e.g., 1. A or 2. A. some explanation)
answer_pattern = re.compile(r"(\d+)\.\s*([A-D])(?:\.\s+.*)?")

questions_dict = {}

for match in question_pattern.finditer(question_block):
    q_number = int(match.group(1))
    q_text = match.group(2).strip()
    q_choices_raw = match.group(3).strip()

    if q_choices_raw:
        q_type = "multiple choice"
        choices = choice_pattern.findall(q_choices_raw)
    else:
        q_type = "short answer"
        choices = []

    questions_dict[q_number] = {
        "question": q_text,
        "type": q_type,
    }

    if choices:
        questions_dict[q_number]["choices"] = choices

# Attach correct answers (and resolve to full text for multiple choice)
for match in answer_pattern.finditer(answer_block):
    q_number = int(match.group(1))
    answer_letter = match.group(2).strip()
    if q_number in questions_dict:
        qdata = questions_dict[q_number]
        if qdata["type"] == "multiple choice":
            letter_to_index = {"A": 0, "B": 1, "C": 2, "D": 3}
            index = letter_to_index.get(answer_letter)
            if index is not None and "choices" in qdata and index < len(qdata["choices"]):
                qdata["answer"] = qdata["choices"][index]
            else:
                qdata["answer"] = f"(Invalid answer letter: {answer_letter})"
        else:
            qdata["answer"] = answer_letter

# If short answers weren’t matched in the key above, fall back to line-by-line
if any(q["type"] == "short answer" and "answer" not in q for q in questions_dict.values()):
    short_answers = [line.strip() for line in answer_block.strip().split("\n") if line.strip()]
    for idx, (qid, qdata) in enumerate(questions_dict.items()):
        if qdata["type"] == "short answer" and "answer" not in qdata:
            if idx < len(short_answers):
                qdata["answer"] = short_answers[idx].split(".", 1)[-1].strip()

# --- Final Output ---
print("\n--- PARSED QUESTION OBJECT ---")
for qid, q in questions_dict.items():
    print(f"{qid}: {q}")
