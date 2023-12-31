from flaml import autogen
from flaml.autogen.retrieve_utils import create_vector_db_from_dir, query_vector_db, get_file_from_url, get_files_from_dir
import chromadb


# Configuration for GPT-4
config_list_gpt4 = autogen.config_list_from_json(
    "../OAI_CONFIG_LIST.json",
    filter_dict={
        "model": ["gpt-4-0613, gpt-4-32k, gpt-4, gpt-4-0314"],
    },
)

gpt4_config = {
    "seed": 42,
    "temperature": 0,
    "config_list": config_list_gpt4,
    "request_timeout": 1200,
}

def access_document(filepath: str) -> str:
    """
    Access and read the content of a local document.

    Args:
    - filepath (str): Path to the local document or file to access.

    Returns:
    - str: Content of the document.
    """
    try:
        with open(filepath, 'r') as file:
            content = file.read()
        return content
    except Exception as e:
        return f"Error accessing the document: {str(e)}"


working_directory = "software_project_files"  # Common working directory for relevant agents

# DevManager
dev_manager = autogen.UserProxyAgent(
    name="DevManager",
    system_message="DevManager: Define requirements, design the architecture, and review code. Collaborate with the Developer for refining the software. Remember to stay in character.",
    code_execution_config={
        "work_dir": working_directory,
        "use_docker": False,
        "timeout": 120,
        "last_n_messages": 1,
    },
)

# Developer with function to access documents
developer = autogen.AssistantAgent(
    name="Developer",
    system_message="Developer: Develop the software, refer to documentation, and ask questions when needed. Remember to stay in character.",
    llm_config={
        "request_timeout": 600,
        "seed": 42,
        "config_list": gpt4_config,  # assuming the gpt4_config is defined elsewhere in your code
        "model": "gpt-4-0613",  # make sure the endpoint you use supports the model
        "temperature": 0,
        "functions": [
            {
                "name": "access_document",
                "description": "Access local documents and files as required during development.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to the local document or file to access.",
                        },
                    },
                    "required": ["filepath"],
                },
            }
        ],
    }
)


# Executor-Tester
executor_tester = autogen.UserProxyAgent(
    name="Executor-Tester",
    system_message="Executor-Tester: Execute and test the developed software. Report outcomes and possible issues. Remember to stay in character.",
    code_execution_config={
       "work_dir": working_directory,
        "use_docker": False,
        "timeout": 120,
        "last_n_messages": 1,
    },
    human_input_mode="ALWAYS",
)

# Researcher with web interactions
researcher = autogen.UserProxyAgent(
    name="Researcher",
    system_message="Researcher: Fetch online resources, best practices, or any other relevant information. Remember to stay in character.",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "web"},
    llm_config=gpt4_config,
)

# FileManager with local file interactions
file_manager = autogen.UserProxyAgent(
    name="FileManager",
    system_message="FileManager: Manage files, save code, retrieve past versions, and organize the workspace. Remember to stay in character.",
    code_execution_config={
        "work_dir": working_directory,
        "use_docker": False,
        "timeout": 120,
        "last_n_messages": 1,
    },
    human_input_mode="NEVER",
)

# Group Chat Setup
groupchat = autogen.GroupChat(
    agents=[dev_manager, developer, executor_tester, researcher, file_manager], 
    messages=[], 
    max_round=150  # Increased max_round for extended interaction
)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)

# Initiating Chat
dev_manager.initiate_chat(
    manager,
    message="Let's build a simple help world webpage using nextjs 13.4 with app router"
)
