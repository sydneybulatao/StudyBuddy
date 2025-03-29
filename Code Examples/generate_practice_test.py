# Assignment 2: Chatbot/program that focuses on a healthcare or education application

from llmproxy import generate
import time
import os

if __name__ == '__main__':
  # Starting screen and information
  print("--- Practice Test Generator ---")
  print("This program allows you to generate practice tests based on what you are currently studying.")
  print("")
  input("Press Enter to proceed...")
  os.system('clear')

  # Prompt for test information
  print("--- Input Test Content ---")
  validInfo = False
  while (not validInfo):
    # Ask for subject and three main study points
    print("Please input information about what you are studying, including three main study points that you would like the test to focus on.")
    subject = input("Subject / Class Name: ")
    p1 = input("Focus Point 1: ")
    p2 = input("Focus Point 2: ")
    p3 = input("Focus Point 3: ")
    input("Press Enter to proceed...")
    os.system('clear')

    # Verify information
    print("--- Verify Test Content ---")
    print("Generating test content summary...")
    system = "First, output a sentence that says 'Based on the information you provided, the practice test will focus on the following points.'" + \
      "Output a newline. For each of the three focus points provided, output the name of the focus point, a newline, and then a one sentence summary about that topic." 
    query = "Focus point one: " + p1 + ". Focus point two: " + p2 + ". Focus point three: " + p3 + ". Subject: " + subject + "."
    response = generate(model = 'azure-phi3',
      system = system,
      query = query,
      temperature=0.0,
      lastk=0,
      session_id='genericsession')
    print(response)
    print("")

    # Ask if user wants to proceed
    valid = False
    while (not valid):
      answer = input("Would you like to proceed with the above content or make changes to the content? (proceed / change): ")
      if (answer == "proceed"):
        valid = True
        validInfo = True
        os.system('clear')
      if (answer == "change"):
        valid = True
        os.system('clear')
      elif (answer != "change" and answer != "proceed"):
        print("Please only input either 'proceed' or 'change'.")

  # Ask user for number of questions and type of questions
  print("--- Customize Your Test ---")
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
    format = input("Question format (multiple choice / short answer): ")
    if (format in validFormats):
      validFormat = True
    else:
      print("Invalid format type.")

  # Generate test 
  os.system('clear')
  print("--- Generating Your Test ---")
  print("This may take a moment...")
  
  # Format system
  system = "Use the context provided by the query" + \
    " to generate a practice test. Do not use information that comes from outside of the specified focus points." \
    + " For the first line of output, please output a test name based on the subject and output this name in all caps." \
    + "Next, output text in all caps that says '--- QUESTIONS ---' " \
    + "Then, following the name, please output the specified number and format of questions based on the content in the context. After each question output a blank line." \
    + " Finally, output text in all caps that says '--- ANSWER KEY ---'. Following this, please output the correct answers for each question. After each correct answer output a blank line."

  # Format query
  query = "Generate a practice test based on the focus points provided." \
    + "Give the test " + str(numQ) + " questions that are " + format + " format." + \
    "Focus point one: " + p1 + ". Focus point two: " + p2 + ". Focus point three: " + p3 + ". Subject: " + subject + "."

  response = generate(model = 'azure-phi3',
    system = system,
    query = query,
    temperature=0.0,
    lastk=0,
    session_id='genericsession')
  os.system('clear')
  print(response)