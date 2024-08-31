import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from openai import AzureOpenAI
import os
import requests
import base64
import json
import tempfile

st.set_page_config(layout="wide", page_title="Agent Workflow Generator")

# Load environment variables from .env file
load_dotenv(override=True)

# Initialize Azure OpenAI Client
client = AzureOpenAI(azure_endpoint=os.environ['AOAI_ENDPOINT'], 
                     api_version=os.environ['AOAI_API_VERSION'], 
                     api_key=os.environ['AOAI_KEY'])

gpt_model_deployment = os.getenv("AOAI_GPT_MODEL")
embedding_model = os.getenv("AOAI_EMBEDDING_MODEL")

sys_msg = f"""You help people develop agent-based workflows based on their workflow process descriptions.
You will be provided with an image showcasing a business process.

1.) First, you should identify what agents are needed to replicate this process.
You can do this by using the `get_agents()` tool you have access to.

2.) Then you need to retrieve a script template that can be used to create the agentic workflow.
You can do this by using the `retrieve_template_script()` tool you have access to.

3.) Then, you will create an agentic workflow based on the process description and the script template.
You can do this by using the `create_agentic_workflow()` tool you have access to.

4.) Finally, you will submit the agentic workflow to the client for review and corrections.
You can do this by using the `review_agentic_workflow()` tool you have access to.

By using these tools, in the order described above, you will complete the task successfully.
"""

def get_agents(img_path, dir_name):
    with open(img_path, "rb") as image_file:
        img = base64.b64encode(image_file.read()).decode('utf-8')
    
    sys_msg = """
    You help people develop agent-based workflows based on their process descriptions. 
    Each node in the workflow should represent an agent. 
    Describe these agents and what their goals are.
    Describe the workflow process for how the agents should be used.
    """
    messages = [{"role": "system", "content": sys_msg}]
    user_content = {
        "role": "user",
        "content": [
            {
            "type": "image_url",
            "image_url": {
                    "url": f"data:image/jpeg;base64,{img}"
                     , "detail": "high"
                }
            }  
        ]
    }
    messages.append(user_content)
    completion = client.chat.completions.create(
        model=gpt_model_deployment,
        messages=messages,
        max_tokens = 2000,
        temperature = 0.0
    )
    api_base = os.environ['AOAI_ENDPOINT']
    api_key = os.environ['AOAI_KEY']
    deployment_name = os.environ['AOAI_GPT_MODEL']

    base_url = f"{api_base}openai/deployments/{deployment_name}" 
    headers = {   
        "Content-Type": "application/json",   
        "api-key": api_key 
    } 
    endpoint = f"{base_url}/chat/completions?api-version=2023-12-01-preview" 
    data = { 
        "messages": messages, 
        "temperature": 0.0,
        "top_p": 0.95,
        "max_tokens": 2048
    }   
    response = requests.post(endpoint, headers=headers, data=json.dumps(data)) 
    resp_str = response.json()['choices'][0]['message']['content']

    os.makedirs(dir_name, exist_ok=True)
    with open(f'{dir_name}/agents.txt', 'w') as f:
        f.write(str(resp_str))
        
    return resp_str

def retrieve_template_script():
    return '../templates/functionapp.py'

def create_agentic_workflow(agents, dir_name, template_script_path):
    with open(template_script_path, 'r') as f:
        template_script = f.read()
    sys_msg = f"""
    You help people create agentic workflows using Azure Durable Functions.
    You will be provided with a list of agents, and a sequence in which they should be executed.
    You will also be provided with a durable function template.
    Use this template to create an agent workflow.
    The run_agent_orchestrator function should be used for agent orchestration.
    Each call to an agent should be done using a call_activity function.
    Your code should include activities for each agent. 
    If there is conditional logic in the agent workflow, include this in the agent activity function.

    YOUR RESPONSE SHOULD CONSIST OF ONLY PYTHON CODE.

    ### TEMPLATE: {template_script}
    """
    usr_msg = f'## AGENTS DESCRIPTION: {agents}'
    messages = [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr_msg}]
    completion = client.chat.completions.create(
        model=gpt_model_deployment,
        messages=messages,
        max_tokens = 4000,
        temperature = 0.0
    )
    os.makedirs(dir_name, exist_ok=True)
    with open(f'{dir_name}/functionapp.py', 'w') as f:
        f.write(completion.choices[0].message.content.replace('```python', '').replace('```', ''))
    
    return f'{dir_name}/functionapp.py'

def review_agentic_workflow(template_script_path):
    with open(template_script_path, 'r') as f:
        template_script = f.read()
    sys_msg = f"""
    You will review and improve an agentic workflow built using Azure Durable Functions.
    Review the code and move any loops in the main orchestrator function, to a separate activity function.
    Ensure that the code is clean and follows best practices.

    YOUR RESPONSE SHOULD CONSIST OF ONLY PYTHON CODE.
    """
    usr_msg = f'## DURABLE FUNCTIONS AGENTIC WORKFLOW: {template_script}'
    messages = [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr_msg}]
    completion = client.chat.completions.create(
        model=gpt_model_deployment,
        messages=messages,
        max_tokens = 4000,
        temperature = 0.0
    )
    with open(template_script_path, 'w') as f:
        f.write(completion.choices[0].message.content.replace('```python', '').replace('```', ''))
    
    return completion.choices[0].message.content

# App title
st.title("Azure OpenAI – Agentic Workflow Template Generator")

# File uploader
uploaded_file = st.file_uploader("Upload a workflow image", type=["jpg", "jpeg", "png"])

# Create a chat input box for user input  
user_message = st.chat_input("Type something...") 

if "messages" not in st.session_state:  
    st.session_state.messages = []  

# Define a function to update messages in the Streamlit session state  
def update_messages():  
    # Iterate over each message in the session state's messages list  
    for message in st.session_state.messages:  
        # Check if the message role is 'image'  
        if message['role'] == 'image':  
            # Create a chat message block with the role 'assistant'  
            with st.chat_message('assistant'):  
                # Display the image content of the message  
                st.image(message['content'])  
  
        # Check if the message role is 'schema'  
        elif message['role'] =='schema':  
            # Create an expandable section titled "Database Schema"  
            with st.expander("Database Schema"):  
                # Display the dataframe content of the message  
                st.dataframe(message['content'])  
  
        # Check if the message role is 'schemaerror'  
        elif message['role'] =='schemaerror':  
            # Create an expandable section titled "Database Schema"  
            with st.expander("Database Schema"):  
                # Write the error content of the message  
                st.write(message['content'])  
  
        # Check if the message role is 'sqlquery'  
        elif message['role'] =='sqlquery':  
            # Create an expandable section titled "SQL Query"  
            with st.expander("SQL Query"):  
                # Write the SQL query content of the message as a code block  
                st.write(f"```{message['content']}")  
  
        # Check if the message role is 'sqldata'  
        elif message['role'] =='sqldata':  
            # Create an expandable section titled "SQL Data"  
            with st.expander("SQL Data"):  
                # Display the dataframe content of the message  
                st.dataframe(message['content'])  
  
        # Check if the message role is 'sqlerror'  
        elif message['role'] =='sqlerror':  
            # Create an expandable section titled "SQL Data"  
            with st.expander("SQL Data"):  
                # Write the error content of the message  
                st.write(message['content'])  
  
        # If the message role is anything else  
        else:  
            # Create a chat message block with the role specified in the message  
            with st.chat_message(message['role']):  
                # Display the content of the message using markdown formatting  
                st.markdown(message['content'])  

def run_conversation(sys_msg, img, dir_name, history=[]):
    if len(history)==0:
        messages = [{"role": "system", "content": sys_msg}, {"role": "user", "content": 'Workflow image at ' + img}]
    else:
        pass
    tools = [  
    {  
        "type": "function",  
        "function": {  
            "name": "get_agents",  
            "description": "Interprets an image of a business process workflow diagram and creates a description of a set of agents that could complete the task",  
            "parameters": {  
                "type": "object",  
                "properties": {  
                    "img": {  
                        "type": "string",  
                        "description": "Path to the image of the business process workflow diagram"  
                    }  
                },  
                "required": ["img"]  
            }  
        }  
    },  
    {  
        "type": "function",  
        "function": {  
            "name": "retrieve_template_script",  
            "description": "Retrieve a path to a sample Azure Durable Function python script to be used as the basis for a function-based agent workflow"  
        }  
    },  
    {  
        "type": "function",  
        "function": {  
            "name": "generate_agentic_workflow",  
            "description": "Develops an Azure Durable Function based agentic workflow using provided agent descriptions, and a template script. Saves the file and returns the path.",  
            "parameters": {  
                "type": "object",  
                "properties": {  
                    "agents_description": {  
                        "type": "string",  
                        "description": "A textual description of all agents and their tasks"  
                    },  
                    "dir_name": {  
                        "type": "string",  
                        "description": "Directory name where the generated workflow will be saved"  
                    },  
                    "template_script_path": {  
                        "type": "string",  
                        "description": "A path to a template script to be used as the basis for the workflow"  
                    }  
                },  
                "required": ["agents_description", "dir_name", "template_script_path"]  
            }  
        }  
    },
    {  
        "type": "function",  
        "function": {  
            "name": "review_agentic_workflow",  
            "description": "Reviews an Azure Durable Function based agentic workflow and makes revisions as needed",  
            "parameters": {  
                "type": "object",  
                "properties": {  
                    "script_path": {  
                        "type": "string",  
                        "description": "The path to the Azure Durable Function agentic workflow script to be reviewed"  
                    }  
                },  
                "required": ["script_path"]  
            }  
        }  
    }  
]  

    # First API call: Ask the model to use the functions
    response = client.chat.completions.create(
        model=gpt_model_deployment,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.0
    )

    response_message = response.choices[0].message
    messages.append(response_message)

    is_done = False

    while not is_done:
        # Handle function calls
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
  
                if function_name == "get_agents":
                    st.write('Get Agents')
                    with st.spinner('Reviewing Diagram and Creating Agentic Workflow'):
    
                        function_response = get_agents(function_args['img'], dir_name)
                    st.write(function_response)
                elif function_name == "retrieve_template_script":
                    st.write('Get Templates')
                    with st.spinner('Gathering Agent Templates'):
                        function_response = retrieve_template_script()
                    
                elif function_name == "generate_agentic_workflow":
                    st.write('Authoring Workflow')
                    with st.spinner('Authoring Template Agent Workflow'):
                        function_response = create_agentic_workflow(
                            agents=function_args["agents_description"],
                            dir_name=dir_name,
                            template_script_path=function_args["template_script_path"]
                        )
                    # st.write(function_response)
                elif function_name == "review_agentic_workflow":
                    st.write('Reviewing Workflow')
                    with st.spinner('Revising Template Agent Workflow'):
                        function_response = review_agentic_workflow(
                            template_script_path=function_args["script_path"]
                        )
                    st.write(function_response)
                else:
                    function_response = json.dumps({"error": "Unknown function"})
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
        else:
            print("No tool calls were made by the model.")  

        # Second API call: Get the final response from the model
        response = client.chat.completions.create(
            model=gpt_model_deployment,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.0
        )

        response_message = response.choices[0].message
        messages.append(response_message)
        if response_message.tool_calls:
            pass
        else:
            is_done = True
    

    return response_message.content

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Workflow Diagram', use_column_width=False, width=600)
    
    with tempfile.TemporaryDirectory() as dir_name:
        img_path = f'{dir_name}/workflow.jpg'
        image = image.convert('RGB')
        image.save(img_path, format='JPEG')
        response = run_conversation(sys_msg, img_path, dir_name)
        st.write(response)
