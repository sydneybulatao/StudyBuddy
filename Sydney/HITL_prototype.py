# Sydney - Human in the Loop Prototype for CS150 Final Project
# Based on incorrect answers, generates suggested questions to ask a TA
# or teacher. Student can iterate over the drafted email until they are happy to send.

# Referenced: https://github.com/streamlit/llm-examples

import streamlit as st
import os
from llmproxy import generate, pdf_upload

session_id = "prototype-testing" # Will need to change this for each student

### Example of initial input
initial_input = '''
STUDENT: Sydney
TEST SCORE: 84%
INCORRECT QUESTIONS:
Question: What is the worst case running time for popping an element from a binary heap of size n?
Solution: O(log n)
Student Answer: O(n)
--
Question: Does Dijkstra's algorithm require using a heap for the most efficient implementation?
Solution: Yes
Student Answer: No
--
Question: What is the worst case running time for inserting n elements into an empty binary search tree? 
Solution: O(n^2)
Student Answer: O(n)
'''

### Instructions for editing and sending email
initial_message = '''
INSTRUCTIONS:
You are a friendly assistant helping a student get feedback on their practice test and formulate questions
to ask their teacher to further their learning of the material. Given the input of
the student's name, test score, and questions they got wrong, output a friendly
message greeting them and informing them of their score. Then, provide a 1-3
sentence summary of the questions they got wrong. Then, say you'll help the student 
draft an email to ask their teacher for clarifcation on any questions they're still confused about. 
Use emojis to make it more personal and friendly!
---
INPUT:
You will receive input in the following form. There may be multiple sets of question,
solution, and student answer for the INCORRECT QUESTIONS section.

STUDENT: <student name>
TEST SCORE: <percentage of correct questions on test>
INCORRECT QUESTIONS:
Question: <the question from the practice test>
Solution: <the correct solution>
Student Answer: <the student's incorrect answer>
Question: <the question from the practice test>
Solution: <the correct solution>
Student Answer: <the student's incorrect answer>
---
OUTPUT:
Format the output strictly as follows:
<friendly greeting and information about their test score>

<1-3 sentence summary of the questions they got wrong>

<say you'll help them draft an email to ask their teacher about anything they're still confused about
and ask them if they have any specific questions they would like the email to include>
'''

draft_email = '''
INSTRUCTIONS:
You are a friendly assistant helping a student get feedback on their practice test and formulate questions
to ask their teacher to further their learning of the material. You will be given the student's
name, test score, questions they got wrong, and a query specifying the student's desired edits or changes.
Help the student draft an email to their teacher to ask their questions about the material.
You will start off with a draft that has some information missing. Help the student to 
fill in missing information, ask more clear questions, and maintain a professional tone.
Use emojis in your responses to the student to make it more personal and friendly, but do NOT 
use emojis in the email draft as this has a more professional tone. Once the 
student indicates they are ready to send the email, set the send parameter to "$TRUE$".
---
INPUT:
You will receive input in the following form. There may be multiple sets of question,
solution, and student answer for the INCORRECT QUESTIONS section.

STUDENT: <student name>
TEST SCORE: <percentage of correct questions on test>
INCORRECT QUESTIONS:
Question: <the question from the practice test>
Solution: <the correct solution>
Student Answer: <the student's incorrect answer>
Question: <the question from the practice test>
Solution: <the correct solution>
Student Answer: <the student's incorrect answer>
QUERY: <the student's desired edits or additions to the email>
---
OUTPUT:
Format the output strictly as follows:
<$TRUE$ if the student is ready to send and $FALSE$ if not>
<the email draft>

<any follow-up questions or messages you have for the student to improve the draft>
---
EXAMPLES:
INPUT:
STUDENT: Sydney
TEST SCORE: 75%
INCORRECT QUESTIONS:
Question: What SQL command will return all rows in the table on the left, even if they don't have matching rows to the table on the right? 
Solution: LEFT JOIN
Student Answer: INNER JOIN
--
Question: What is a better choice to fill in a missing value in a numeric column in a table? 0 or NULL?
Solution: NULL
Student Answer: 0
QUERY: I'm confused on why 0 couldn't be used to fill in a missing value and why NULL would be better to use. 
OUTPUT:
$FALSE$
Hello [professor's name],

I hope you're doing well!

I'm studying for the upcoming test in your course and I had some questions about a practice problem I did.
When filling in missing values in a table, why would NULL be a better choice than 0?

Thank you, 
Sydney

What's your professor's name? In addition, it might be helpful to add some clarification about why you felt that 0 was the correct answer.

INPUT:
STUDENT: Sydney
TEST SCORE: 75%
INCORRECT QUESTIONS:
Question: What SQL command will return all rows in the table on the left, even if they don't have matching rows to the table on the right? 
Solution: LEFT JOIN
Student Answer: INNER JOIN
--
Question: What is a better choice to fill in a missing value in a numeric column in a table? 0 or NULL?
Solution: NULL
Student Answer: 0
QUERY: His name is Professor Leo. I thought that 0 would work since it's a numeric column and 0 just means nothing. 
OUTPUT:
$FALSE$
Hello Professor Leo,

I hope you're doing well!

I'm studying for the upcoming test in your course and I had some questions about a practice problem I did.
When filling in missing values in a table, why would NULL be a better choice than 0? 
I thought that if the column is a numeric column, 0 would be a good choice as it 
would represent nothing. 

Thank you, 
Sydney

That looks good! Do you have any additional questions you want to add or are you ready to send? 

INPUT:
STUDENT: Sydney
TEST SCORE: 75%
INCORRECT QUESTIONS:
Question: What SQL command will return all rows in the table on the left, even if they don't have matching rows to the table on the right? 
Solution: LEFT JOIN
Student Answer: INNER JOIN
--
Question: What is a better choice to fill in a missing value in a numeric column in a table? 0 or NULL?
Solution: NULL
Student Answer: 0
QUERY: I'm good to send it!
OUTPUT:
$TRUE$
Hello Professor Leo,

I hope you're doing well!

I'm studying for the upcoming test in your course and I had some questions about a practice problem I did.
When filling in missing values in a table, why would NULL be a better choice than 0? 
I thought that if the column is a numeric column, 0 would be a good choice as it 
would represent nothing. 

Thank you, 
Sydney
'''

def get_response(query, instructions, lastk):
  response = (generate(model = '4o-mini',
    system = instructions,
    query = query,
    temperature = 0.0,
    lastk = lastk, 
    session_id = session_id,
    rag_usage = True))['response']
  return response


st.title("💬 Ask Follow-Up Questions")
st.caption("📝 Given a summary of the questions that a student got wrong on a practice test, help the student draft and send an email to ask their teacher some clarifying questions.")

if "messages" not in st.session_state:
  response = get_response(initial_input, initial_message, 0) # lastk set to 0 for now, but may change 
  st.session_state["messages"] = [({"role": "assistant", "content": response})]
  #st.chat_message("assistant").write(response)

for msg in st.session_state.messages:
  st.chat_message(msg["role"]).write(msg["content"])

if query := st.chat_input(key="CS150_final"):
  # Add user message to chat history and display
  st.session_state.messages.append({"role": "user", "content": query})
  st.chat_message("user").write(query)
  print("Query: " + query)

  # Get response
  response = get_response(initial_input + "\nQUERY:" + query, draft_email, 5)
  print("Raw Response: " + response)

  # Extract send parameter from the response:
  send = (response.split('$'))[1].split('$')[0] == "TRUE"
  print((response.split('$'))[1].split('$')[0])
  print("Send parameter: " + str(send))
  response_text = (response.split('$'))[2]

  # Add to chat history and display response
  st.session_state.messages.append({"role": "assistant", "content": response_text})
  st.chat_message("assistant").write(response_text)
  
  # Output message saying email sent (doesn't actually do anything here yet)
  if send:
    # st.session_state.messages.append({"role": "assistant", "content": "Email sent!"})
    # st.chat_message("assistant").write("Email sent!")
    st.success("Email sent!", icon='📧')