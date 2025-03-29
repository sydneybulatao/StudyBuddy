from llmproxy import generate, retrieve,text_upload
import requests
import os
import re
import ast
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

GOOGLE_API_KEY = os.getenv("googleSearch")
SEARCH_ENGINE_ID = os.getenv("googleCSEId")
# GOOGLE_API_KEY = "AIzaSyA9aWt3R251o7VlMv2mzRoqgjIS2t_wrio"
# SEARCH_ENGINE_ID = "c43b2b31e407e4d17"

# Session variables:

RAG_CONTEXT_SESSION = "RagSessionTest_7"
ADVISOR_SESSION = "mini-project"

def extract_tool(text):
    """
    Extracts the function name and parameters separately.

    Args:
        text (str): The input text containing the function call.

    Returns:
        tuple: (function_name, parameters) if found, otherwise (None, None).
    """
    match = re.search(r'(\w+)\(([\s\S]*)\)', text)
    if match:
        function_name = match.group(1)  # Extract function name
        params = match.group(2)  # Extract parameters as a string
        return function_name, params.strip()  # Return as a tuple
    return None, None  # Return None if no function call is found

def parse_params(params):
    """
    Safely parses function parameters from a string, handling cases 
    where multi-line text arguments contain escaped newline characters.

    Args:
        params (str): The string representation of function parameters.

    Returns:
        list: A list of parsed parameters.
    """
    try:
        # Convert the parameters string into a Python tuple safely
        parsed_params = ast.literal_eval(f"({params})")

        # Ensure the result is a list
        if isinstance(parsed_params, tuple):
            return list(parsed_params)
        return [parsed_params]
    
    except SyntaxError as e:
        print(f"Syntax error while parsing parameters: {e}")
    except Exception as e:
        print(f"Error parsing parameters: {e}")

    return []

def advisor(query: str, user: str, bot: bool):

    rag_context = "No relevant rag context!"
    try:
        rag_context = retrieve(
            query=query,
                session_id=RAG_CONTEXT_SESSION,
                rag_threshold= 0.5,
                rag_k=10
        )
        print('Rag Context:', rag_context)
    except Exception as e:
        rag_context = "No relevant rag context!"
        print('Error retrieving rag context:', e)

    rag_context = rag_context_string_simple(rag_context)
    if should_search_web(query, rag_context, user):
        parsed_query = parse_query(user, query)
        print(f"parsed query: {parsed_query}")
        web_context = google_search(parsed_query)
        print(f"web context: {web_context}")
        store_context(web_context)
        query = f"Query:\n{query}. Information from web: \n{web_context}"
    else:
        if not bot:
            if not rag_context or rag_context == "No relevant information found on web!":
                query = f"Query:\n{query}"
            else:
                query = f"Query:\n{query}. Some additional context: \n{rag_context}" 

             
    """
    AI Advisor for Tufts CS Students.

    This function provides guidance to Tufts University Computer Science students.
    It differentiates between handling user queries (including escalation) and 
    transmitting a response from a human advisor.

    Args:
        query (str): The user's query.
        user (str): The user's session ID.
        advisor_response (bool): Flag indicating if this response is from a human advisor.

    Returns:
        str: The AI's response.
    """

    # Original system prompt (unchanged)
    system_prompt = f"""
        You are a friendly, knowledgeable, and helpful AI advisor dedicated to assisting 
        Tufts University Computer Science students. Your goal is to provide accurate, 
        practical, and engaging responses on topics such as course selection, research 
        opportunities, career guidance, and department policies. Feel free to add a bit of fun 
        with emojis and a lighthearted tone 😊.

        # Important:
        IF the student sends you a greeting message (e.g., hello) or a casual conversation that 
        has nothing to do with the CS department, strictly include $FAQS$ at the 
        end of your response, so that another agent can add some FAQs for the user. 

        If a student asks about something outside your scope or needs further assistance, 
        you will either ask clarifying questions or escalate the query to a human 
        advisor when appropriate using the escalation tool described below:
        ----------
        How You Help Students
        Your areas of expertise include:
        1. Course selection and prerequisites (e.g., "COMP 160 requires COMP 15 and either COMP/MATH 22 or 61.")
        2. Research opportunities (e.g., "Prof. Smith's lab is accepting undergrad researchers in machine learning.")
        3. Career advice related to internships, job applications, networking, and career fairs
        4. CS department policies (e.g., "To transfer a CS course, you need approval from the undergraduate director.")
        ----------
        Your responses should be:
        1. Conversational yet professional and friendly, sprinkled with fun emojis 😄
        2. Personalized by referencing Tufts-specific buildings, traditions, and resources when relevant
        3. Concise (three to five sentences) unless a more detailed explanation is necessary
        4. Actionable by providing clear next steps whenever possible
        ----------
        Boundaries and Limitations
        You do not:
        1. Complete assignments or coding tasks
        2. Advise on non-CS departments or general university matters
        3. Speculate on professor preferences or grading policies
        4. Guarantee outcomes of petitions or policy exceptions
        ----------
        Handling Complex or Unclear Questions
        If a student's question is unclear or requires more details, guide the conversation naturally:
        1. Ask for clarification: "Could you clarify what aspect of [topic] you're most interested in?" 🤔
        2. Break down the question: "Are you asking about prerequisites, workload, or professor recommendations for this course?"
        ----------
        ### Escalating to a Human Advisor
        If the question requires human input, you are unable to answer the query
        confidently, or the user seems unsatisfied with the answer, then smoothly transition:
        "This is a great question. I can give some general advice, 
        but for official confirmation, would you like me to forward this to a human advisor?" 
        If the student agrees: "Got it. I'll summarize your question as: [summary]. Does that sound right?"
        If confirmed, send a request to the department chair using the escalation tool.
        If you want to use the escalation tool, strictly respond only with the 
        tool as explained below:
    
        Escalation Tool: send_message
        Purpose: Notifies the CS department chair about the student's inquiry
        Parameters: All parameters below are strings.
        Student: "{user}"
        Question: <student's question>
        Background: <context to help the advisor>
        Example usage:
        send_message(f"Student: {user}", "Question: What are the prerequisites for COMP 160?", "Background: Jane is a sophomore considering taking the course next semester.")
        ----------
        Final Guidelines
        Encourage students and make them feel supported and excited about their journey at Tufts 🎉
        Provide helpful, approachable, and engaging responses that feel like a real conversation. Use fun emojis and a friendly tone to make your responses inviting and easy to understand.
        When in doubt, guide students to resources or a human advisor rather than making assumptions.  
        """

    # Prompt for transmitting a human advisor's response
    transmit_response_prompt = """
    You have received a response from a **human advisor**.  
    Use this response to provide a clear and direct answer to the student.

    Respond in the following format:
    - _"I checked with a human advisor, and here's the guidance: [advisor's response]. 
    Let me know if you have any further questions!"_
    """

    try:
        if bot == "HumanAdvisor":
            print(f"Human advisor with query: {query}")
            # If this is a response from a human advisor, format it accordingly
            response = generate(model='4o-mini',
                                system=transmit_response_prompt,
                                query=f"Human Advisor Response:\n\n{query}",
                                lastk=5,
                                temperature=0.7,
                                session_id=user + ADVISOR_SESSION)
        else:
            print(f"Not human advisor with query: {query}")
            # Standard AI response handling (including escalation if needed)
            response = generate(model='4o-mini',
                                system=system_prompt,
                                lastk=5,
                                query=query,
                                temperature=0.7,
                                session_id=user + ADVISOR_SESSION)
                        
        return response['response']
    
    except Exception as e:
        print(f"Error occurred with parsing output: {e}")
        return "An error occurred while processing your request."

def send_message(student: str, question: str, background: str):
    """
    Sends an email to the CS department's human advisor with the student's query.

    Args:
        student (str): Information about the student.
        question (str): The student's question.
        background (str): Additional context about the inquiry.

    Returns:
        str: A message indicating the success or failure of the email sending process.
    """
    try:
        # Compose the email message
        # Properly format the JSON payload as a dictionary (not a set)
        payload = {
            "bot": "AI Advisor",
            "student": student,
            "question": question,
            "background": background
        }
        
        # Send the email
        response = requests.post(
            "https://institutional-galina-tufts-077937b9.koyeb.app/query", 
            json=payload
        )

        # Ensure a valid response
        if response.status_code == 200:
            return "Your query has been forwarded to the department chair for further assistance. I will notify you once a response is received."

        return f"Error: Received response code {response.status_code}, Response: {response.text}"

    except Exception as e:
        return f"Error occurred while sending the message: {e}"
    
def generate_response(query: str, user: str, bot=False):
    print("Received query:", query)
    print("User:", user)
    """
    Generates a response to a user query and executes any extracted tool call.

    Args:
        query (str): The user's query.
        user (str): The user's session ID.

    Returns:
        str: The generated response.
    """    

    response = advisor(query, user, bot)
    print("Generated response:", response)

    # Extract tool name and parameters
    tool_name, params = extract_tool(response)

    if tool_name == "send_message":
        print("Entered here!")
        param_list = parse_params(params)  # Use safer parsing
        if len(param_list) == 3:  
            try:
                tool_response = send_message(*param_list) 
                print(f"Tool Output: {tool_response}\n")
                return tool_response  # Return tool's response instead of LLM's
            except Exception as e:
                print(f"Error occurred with tool execution: {e}")
                return "An error occurred while forwarding your query."
        else:
            print("Error: Incorrect number of parameters for send_message.")
            return "Error: Incorrect function parameters."
    return response


def rag_context_string_simple(rag_context):

    context_string = ""

    i=1
    for collection in rag_context:
    
        if not context_string:
            context_string = """The following is additional context that may be helpful in answering the user's query. """

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


def should_search_web(query: str, context: str, user: str) -> bool:
    response = generate(
        model='4o-mini',
        system="""
        You are an AI knowledge base assistant for Tufts CS students. You are provided with:
          - The user's query,
          - Relevant internal knowledge (RAG), and 
          - Context from previous messages.
          
        Your task is to determine if the internal knowledge is sufficient to answer 
        the query or if additional web search is needed. Follow these guidelines:
        
        1. If the query is simply a greeting (e.g., "Hello", "Hi") or a casual
        conversation that is not a CS department question, return "NO_SEARCH_NEEDED".
        2. If the query is not related to CS department topics (such as course details, 
        research opportunities, or policies), return "NO_SEARCH_NEEDED".
        3. If the user wants to get in touch with a human advisor, return "NO_SEARCH_NEEDED"
        4. Only if the query is clearly about a CS department topic and the provided 
        internal knowledge does not fully answer it, return "SEARCH_NEEDED".
        5. If the query is ambiguous, refer to previous messages for additional context before deciding.
        
        Return exactly one of the following responses, with no extra text:
          - "NO_SEARCH_NEEDED"
          - "SEARCH_NEEDED"
        """,
        query=f"Query: {query}\nContext: {context}",
        temperature=0.0,
        lastk=1,
        session_id=user + ADVISOR_SESSION,
        rag_usage=False
    )   
    print("Error can be here" , response) 
              
    return response['response'] == "SEARCH_NEEDED"


def parse_query(user:str, query: str) -> str:
    response = generate(
        model='4o-mini',
        system="""
        You are an AI assistant that reformulates search queries specifically for
        Tufts University's Computer Science department. Your task is to rewrite
        any given query into a concise, search-friendly format that retrieves
        accurate information on Tufts Computer Science topics—such as courses,
        degree requirements, faculty, research, internships, funding (including
        travel requests), and related subjects. Always ensure that the “Tufts
        Computer Science” context is explicitly included in your reformulated 
        query, even if the original query omits it. If the query is ambiguous 
        or lacks sufficient details, refer to previous messages for additional
        context and adjust your output accordingly.
        """,
        query=f"Reformulate this query for a Google search:\n\n{query}",
        temperature=0.0,
        lastk=3,
        session_id=user + ADVISOR_SESSION,
        rag_usage=False
    )
    return response['response']

def fetch_full_content(url: str, timeout: int = 10) -> str:
    html = ""
    # try:
    #     # Try using Selenium to fetch the full rendered page
    #     chrome_options = Options()
    #     chrome_options.add_argument("--headless")
    #     driver = webdriver.Chrome(options=chrome_options)
    #     driver.get(url)
    #     html = driver.page_source
    #     driver.quit()
    # except Exception as e:
    #     print(f"Selenium error fetching {url}: {e}\nFalling back to requests/BeautifulSoup.")
    try:
        # Fallback to a simple requests-based approach
        fallback_response = requests.get(url, timeout=timeout)
        fallback_response.raise_for_status()
        html = fallback_response.content
    except Exception as fallback_e:
        print(f"Fallback error fetching {url} using requests: {fallback_e}")
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove unwanted elements to clean up the page
    for unwanted in soup(["script", "style", "header", "footer", "nav", "aside"]):
        unwanted.extract()
    
    text = soup.get_text(separator=" ", strip=True)
    clean_text = " ".join(text.split())
    return clean_text

def format_results_for_llm(results):
    """Format a list of dictionaries into a string for LLM input"""
    formatted_results = "\n\n".join(
        [f"Link: {item['link']}\nSummary: {item['summary']}" for item in results]
    )
    return formatted_results

def google_search(query: str, num_results: int = 5) -> str:
    search_url = "https://www.googleapis.com/customsearch/v1"
    print(f"Perfoming google search with: {search_url}")
    params = {
        "key": GOOGLE_API_KEY, 
        "cx": SEARCH_ENGINE_ID, 
        "q": query.replace('"', ''), 
        "num": num_results
    }
    try:
        response = requests.get(search_url, params=params, timeout=30)
        print(f"Response: {response}")
        response.raise_for_status()
        data = response.json()
    
        # Extract URLs and summaries (snippets) from search result items
        results = [
            {"link": item["link"], "summary": item.get("snippet", "No summary available")}
            for item in data.get("items", [])
        ]
        for item in data.get("items", []):
            print(f"\n\nDEBUGGING: {item["link"]}\n\n")

        if not results:
            return "No relevant information found on web!"

        results = format_results_for_llm(results)
    
        system=f"""
                You will be given urls and summaries. Your job is to use this
                information to pick the url which you think has the most useful
                information to answer a query that will also be given to you.
                Once you identified the url, strictly, just respond with the url
                and nothing else.
                """
        response = generate(
            model='4o-mini',
            system=system,
            query=f"query:{query}urls:{results}",
            temperature=0.1,
            lastk=1,
            session_id="GenericSessionId",
            rag_usage=False
        )
        print(f"[Debugging] This is the url: {response['response']}")
        
        web_content = fetch_full_content(response['response'])
        return web_content
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def store_context(context: str) -> None:
    """Evaluates and stores meaningful information into RAG for future use."""
    response = generate(
        model='4o-mini',
        system="""
        You are an AI assistant managing a knowledge base for Tufts CS students. Your role is twofold:

        1. Relevance Determination:

        - Analyze the provided information and decide whether it is valuable 
        for future reference.
        - Consider the following topics as high-priority: academic advising, courses, 
        research, careers, and university policies.
        - Also consider if the information is relevant to 

        2. Summarization or Discarding:

        - If the information is relevant:
            - Generate a concise and structured summary that preserves key details and insights.
        - If the information is too general, redundant, or not useful for our knowledge base:
            - Strictly respond only with: $DISCARD$
        Your response should contain either the structured summary (if relevant) 
        or the exact text $DISCARD$ (if not). Do not include any additional commentary or explanation.
        """,
        query=f"Evaluate and summarize the following information for storage:\n\n{context}",
        temperature=0.0,
        lastk=0,
        session_id=RAG_CONTEXT_SESSION,
        rag_usage=False
    )

    summary = response.get("response", "$DISCARD$")

    if summary != "$DISCARD$":
        print(f"\n\nStoring in RAG: {summary}\n\n")
        text_upload(text=summary, session_id=RAG_CONTEXT_SESSION, strategy='fixed')
