from llmproxy import generate, text_upload
from flask import Flask, request, jsonify, session
import requests
import os
import psycopg2
from datetime import timedelta

app = Flask(__name__)

# API endpoint
url = "https://chat.genaiconnect.net/api/v1/chat.postMessage" #URL of RocketChat server, keep the same

# Headers with authentication tokens
headers = {
    "Content-Type": "application/json",
    "X-Auth-Token": 'AzNCz3nUBiQDR_dX8iQWxY0Gsc73Q-3ZShPjSqlxW8E', #Replace with your bot token for local testing or keep it and store secrets in Koyeb
    "X-User-Id": 'S2xaY9Kq9mTuKt6Hn'#Replace with your bot user id for local testing or keep it and store secrets in Koyeb
}

### Advisor bot information
session_id_advisor_bot = 'sydney-advisor-bot'
message_advisor_instructions = '''
INSTRUCTIONS:
You are a bot that summarizes a student's question to a advisor and provides the 
advisor with potential responses to that question. You will receive a student's name, question, and background
in the input. You will output the student's name, a summary of the question, 
and two potential responses for the advisor.

TWO POTENTIAL RESPONSES:
Be sure that the two responses are different in their content. Use your context
to provide helpful links and/or contact information in the responses, when appropriate. 

INPUT FORMAT:
Student: (student's name)
Question: (student's question)
Background: (helpful background information about the student)

OUTPUT FORMAT:
*You have a question from (student's name)!*
(a 1-3 sentence summary of the question, using the student's background information to provide context)
RESPONSE1: %(a 1-2 sentence response to the question)%
REPONSE2: $(a 1-2 sentence response to the question, different from response 1)$

EXAMPLES:
INPUT:
Student: Sydney
Question: Is professor dogar teaching CS150 next semester?
Background: Sydney is a sophomore interested in artificial intelligence and is looking to learn more about generative AI.
OUTPUT:
*You have a question from Sydney!*
Is Professor Dogar teaching CS150 next semester? The student would like to know as they are interested in learning more about generative AI. 
RESPONSE1: %Hi Sydney! Professor Dogar is not teaching CS150 next semester.%
RESPONSE2: $Hi Sydney! Professor Dogar is teaching CS150 next semester.$

INPUT:
Student: Sam
Question: What forms do I need to submit for graduation? 
Background: Sam is a senior who will be graduating this May. The student wants more clarification on graduation requirements and isn't sure what they need to do to graduate. 
OUTPUT:
*You have a question from Sam!*
What forms do seniors need to submit for graduation? Sam is currently a senior on track to graduate this May and would like some clarification on the requirements. 
RESPONSE1: %Hi Sam! Take a look at the Computer Science Department website for some information on the forms for graduation.%
RESPONSE2: $Hi Sam! Would you be available to set up a meeting to discuss the graduation requirements in person?$
'''

### Message Editor bot information
session_id_editor_bot = 'sydney-editor-bot'
message_editor_instructions = '''
INSTRUCTIONS:
You are a bot that is helping an advisor draft a response to a student's question. 
Initially, you will receive the initial message that the advisor is working off of,
and the student's username.
The initial message may be blank or a pre-written message. 
After, the advisor may ask you to rewrite, edit, or add content to the current message.
Keep editing the message until the advisor is ready to send it.
If the user asks you to do any tasks unrelated to editing or sending a message, remind them
that you are only able to help them edit and send their responses to students.

STEPS:
1. Output the initial message and ask if there is anything the user has any edits.
2. Make any edits specified to the message and then ask if the user is ready to send it.
Keep making edits until the user is ready to send. 
3. Once the user confirms they're ready to send the message, set the SEND variable to TRUE.

This example shows the full process from an empty message to sending the message.
You must format your output as is shown in the examples. It must always have the three
fields displayed (SEND:, STUDENT:, MESSAGE:). 
EXAMPLES:
INPUT: student: sydney.bulatao message: 
OUTPUT: 
SEND: $FALSE$
STUDENT: sydney.bulatao
MESSAGE: 
What would you like to respond with? ✏️

INPUT: Hi Sydney! Would you be available to set up a meeting to discuss the graduation requirements in person?
OUTPUT:
SEND: $FALSE$
STUDENT: sydney.bulatao
MESSAGE: Hi Sydney! Would you be available to set up a meeting to discuss the graduation requirements in person?

Would you like to make any edits or are you ready to send this? ✏️

INPUT: Can you add a sentence that says I would be available to meet with Sydney on Friday at 1pm? 
OUTPUT:
SEND: $FALSE$
STUDENT: sydney.bulatao
MESSAGE: Hi Sydney! Would you be available to set up a meeting to discuss the graduation requirements in person? I'm available Friday at 1pm. 

Would you like to make any edits or are you ready to send this? ✏️

INPUT: I'm ready to send
OUTPUT:
SEND: $TRUE$
STUDENT: sydney.bulatao
MESSAGE: Hi Sydney! Would you be available to set up a meeting to discuss the graduation requirements in person? I'm available Friday at 1pm. 
Great! I'll send your message! ✉️
'''

# Upload context from txt files to the advisor bot for better pre-written responses 
def upload_context():
  for filename in os.listdir('RagContext'):
      if filename.lower().endswith('.txt'):
          file_path = os.path.join('RagContext', filename)
          print(f"Uploading file: {file_path}")
          with open(file_path, "r", encoding="utf-8") as file:
              text_content = file.read()
          response = text_upload(
              text=text_content,
              strategy='fixed',
              session_id=session_id_advisor_bot,
              local=True
          )
          print(f"Text upload response: {response}")

def editor_bot(message):
  # Get response
  response = generate(model = '4o-mini',
                      system = message_editor_instructions,
                      query = message,
                      temperature = 0.0,
                      lastk = 5,
                      session_id = session_id_editor_bot,
                      rag_usage = False)['response']
  
  # Extract if ready to send
  send = (response.split('$'))[1].split('$')[0]
  response_text = (response.split('$'))[2]

  print("SEND: " + send)
  print("RESPONSE: " + response_text)

  # If not ready to send:
  response = ""
  if (send == "FALSE"):
    response = {
      "text": response_text,
      "attachments": [
        { 
          "actions": [
            {
              "type": "button",
              "text": "Send 📬",
              "msg": "Ready to send!",
              "msg_in_chat_window": True,
              "msg_processing_type": "sendMessage"
            }
          ]
        }
      ]
    }
  else:
    response = {"text": response_text}
  
  return send, response

def advisor_bot(message, user):
  response = ""

  ### CHECK FOR CORRECT INITIAL INPUT
  if ("Student:" not in message) or ("Question:" not in message) or ("Background:" not in message):
    response = {"text": "Sorry, I am unable to process your request."}
  
  ### GENERATE MESSAGE TO ADVISOR
  else: 
    response = generate(model = '4o-mini',
                            system = message_advisor_instructions,
                            query = message,
                            temperature = 0.0,
                            lastk = 0,
                            session_id = session_id_advisor_bot,
                            rag_usage = False)
    response = response['response']

    # Extract the first part of the response as the text portion
    response_text = response.split('RESPONSE1')[0]
    print("Response_text: " + response_text)

    # Extract the two responses
    choice1 = (response.split('%'))[1].split('%')[0]
    choice2 = (response.split('$'))[1].split('$')[0]

    # Create three buttons (2 pre-written responses, 1 write your own response)
    response = {
      "channel": "@sydney.bulatao", # hardcode to my user for now (would be the advisor's username in the future)
      "text": response_text + '\nSelect a response to work off of or draft your own!',
      "attachments": [
        { 
          "text": choice1,
          "actions": [
            {
              "type": "button",
              "text": "Select Response 📎",
              "msg": "student: " + user + " message: " + choice1,
              "msg_in_chat_window": True,
              "msg_processing_type": "sendMessage"
            }
          ]
        },
        {
          "text": choice2,
          "actions": [
            {
              "type": "button",
              "text": "Select Response 📎",
              "msg": "student: " + user + " message: " + choice2,
              "msg_in_chat_window": True,
              "msg_processing_type": "sendMessage"
            }
          ]
        },
        {
          "actions": [
            {
              "type": "button",
              "text": "Write Custom Message 📝",
              "msg": "student: " + user,
              "msg_in_chat_window": True,
              "msg_processing_type": "sendMessage"
            }
          ]
        }
      ]
    }

  return response

@app.route('/')
def hello_world():
   return jsonify({"text":'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():
  # Upload text context 
  upload_context()

  # Get data from user
  data = request.get_json()
  response = ""

  # Get bot message (initial input to generate message)
  if data.get("bot"): 
    print("GOT MESSAGE FROM BOT!")
    print(data.get("student") + "\n" + data.get("question") + "\n" + data.get("background"))

    # Get response from bot back
    student_username = data.get("student").split("Student: ")[1].strip()
    response = advisor_bot(data.get("student") + "\n" + data.get("question") + "\n" + data.get("background"), student_username)

    # Direct message to the advisor
    response = requests.post(url, json=response, headers=headers)
    response = {"text": "Sent with status code: " + str(response.status_code)}

  # Otherwise, interacting with the advisor
  else:
    print("GOT MESSAGE FROM ADVISOR!")
    
    message = data.get("text", "")
    print("message: " + message)

    send, response = editor_bot(message)

    # If ready to send, send it back to Erin's bot
    if (send == "TRUE"):
      # Extract the student's username and the message to send 
      response = response.get("text", "")
      student_username = (response.split('STUDENT: ')[1]).split('MESSAGE:')[0].strip()
      message = response.split('MESSAGE: ')[1].split('\n')[0].strip()

      # Grab the response from the chatbot to send back to the adivisor
      response = response.split('MESSAGE: ')[1].split('\n')[1].strip()
      response = {"text": response}

      print("sending advisor's response back to student: " + student_username)
      print("advisor's response: " + message)

      try:
        payload = {
          "student user_name": student_username, # this will be the student it should be sent back to
          "bot": "HumanAdvisor",
          "text": message
        }
        post_response = requests.post(
                "https://changing-egret-erinsarlak-af2a6dfd.koyeb.app/query", 
                json=payload,
                headers=headers
              )

        print("Sending this back to Erin's bot:")
        print(payload)
        print("Response from posting request to Erin's bot:")
        print(post_response)

      except Exception as e:
        response = {"text": f"Error occurred while sending the message: {e}"}

  # Send response back to advisor
  print(response)
  return jsonify(response)

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == '__main__':
  # Run app
  app.run()