import json  # To handle JSON data
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from snowflake.snowpark import Session
import pandas as pd
import streamlit as st  # Streamlit library for building the web app
from snowflake.snowpark.exceptions import SnowparkSQLException
import warnings
warnings.filterwarnings('ignore')
# import snowflake.cortex as cortex
# import logger
import re

# List of available semantic model paths in the format: <DATABASE>.<SCHEMA>.<STAGE>/<FILE-NAME>
# Each path points to a YAML file defining a semantic model
AVAILABLE_SEMANTIC_MODELS_PATHS = [
    'KIPI_POC_DB.KIPI_POC_STG.KIPI/Customer_Support_Analytics.yaml'
]
API_ENDPOINT = "/api/v2/cortex/analyst/message"
API_TIMEOUT = 100000  # in milliseconds

# Initialize a Snowpark session for executing queries
#session = get_active_session()
connection_parameters = {
  "account": os.environ.get("ACCOUNT"),
  "user": os.environ.get("USER"),
  "password": os.environ.get("PASSWORD"),
  "role": os.environ.get("ROLE"),  # optional
  "warehouse": "COMPUTE_WH",  # optional
    "database": "KIPI_POC_DB",  # optional
    "schema": "KIPI_POC_STG",  # optional
}

session = Session.builder.configs(connection_parameters).create()


st.set_page_config(layout='wide')
# st.write(st.session_state)
# st.write(st.session_state)
def main():
    # Initialize session state
    if "messages" not in st.session_state:
        reset_session_state()
    show_header_and_sidebar()
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # if len(st.session_state.messages) == 0:
    #     process_user_input("What questions can I ask?")
    display_suggested_questions()
    display_conversation()
    handle_user_inputs()
    handle_error_notifications()


def reset_session_state():
    """Reset only necessary elements to avoid full restart."""
    if "selected_semantic_model_path" not in st.session_state:
        st.session_state.selected_semantic_model_path = "KIPI_POC_DB.KIPI_POC_STG.KIPI/Customer_Support_Analytics.yaml"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_suggestion" not in st.session_state:
        st.session_state.active_suggestion = None
    if "content" not in st.session_state:
        st.session_state.content = {}
    if "insight_generation" not in st.session_state:
        st.session_state.insight_generation = False
    if "follow_up_suggestions" not in st.session_state:
        st.session_state.follow_up_suggestions = False
            ## GP-->
    if "raw_data_generation" not in st.session_state:
        st.session_state.raw_data_generation = False
    if "display_viz" not in st.session_state:
        st.session_state.display_viz = False
    if "active_feedback_index" not in st.session_state:
        st.session_state.active_feedback_index = None

def enable_insight_generation():
    st.session_state.insight_generation = not st.session_state.insight_generation
    
def enable_follow_up_suggestions():
    st.session_state.follow_up_suggestions = not st.session_state.follow_up_suggestions

def enable_raw_data_generation():
    st.session_state.raw_data_generation = not st.session_state.raw_data_generation

def enable_data_viz():
    st.session_state.display_viz = not st.session_state.display_viz

def show_header_and_sidebar():
    """Display the enhanced header and sidebar with a React-like UI, including the Logitech logo and subtitle positioned below the title."""

    #current_user=st.experimental_user['email']
    current_user="Nikhil Singh"
    # st.logo('https://images.seeklogo.com/logo-png/26/1/logitech-logo-png_seeklogo-268713.png',size='large')
    # st.write(current_user)
    # 🔹 Modern Header Section with Logitech Logo, Title, and Subtitle
    st.markdown("""
        <style>
            .title-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;           
                color: black;
                #box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
                text-align: center;
            }
            .logo-title {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .logo-title img {
                width: 120px;
                height: 100px;
            }
            .title-text {
                font-size: 30px;
                font-weight: bold;
                margin: 0;
            }
            .subtitle {
                font-size: 16px;
                color: black;
                margin-top: 1px;
                text-align: center;
                font-style: italic;
            }
        </style>
        <div class="title-container">
            <div class="logo-title">
                <img src="https://framerusercontent.com/images/dZwik4TB65oJehGA8raaTK3cepw.png?scale-down-to=1024" alt="Customer Logo">
                <h1 class="title-text">⚡ Customer Support Analytics</h1>
            </div>
            <p class="subtitle">
                Gain powerful insights into customer support ticketing with interactive analytics.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 🔹 Enhanced Sidebar
    with st.sidebar:
        st.markdown(f"""
            <style>
                .sidebar-container {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 8px;
                    border-radius: 8px;
                    background: linear-gradient(135deg, #1e3c72, #2a5298);
                    color: white;
                    margin-bottom: 15px;
                }}
                .user-avatar {{
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    font-weight: bold;
                    color: #1e3c72;
                    margin-bottom: 6px;
                }}
                .user-email {{
                    font-size: 15px;
                    font-weight: 500;
                    text-align: center;
                    color: white;
                    opacity: 0.9;
                }}
                .blur-divider {{
                    width: 100%;
                    height: 1px;
                    background: rgba(255, 255, 255, 0.1);
                    margin: 8px 0;
                }}
                .clear-chat-btn button {{
                    background-color: #ff6666 !important;
                    color: white !important;
                    font-weight: bold;
                    width: 100%;
                    border-radius: 5px;
                }}
                .custom-toggle label span {{
                    color: white !important;
                }}
                .clear-chat-btn button:hover {{
                    background-color: #ff3333 !important;
                }}
                .stToggleSwitch [data-baseweb="toggle"] {{
                    background-color: #00cc44 !important;
                }}
                .custom-divider {{
                    border-top: 1px solid #ddd;
                    margin: 8px 0;
                }}
                
            </style>
            <div class="sidebar-container">
                <div class="user-avatar">👤</div>
                <p class="user-email">{current_user}</p>
            </div>
        """,unsafe_allow_html=True)
        
        # st.markdown(f"""
        #     <div class="user-info">
        #         <p>👤 Logged in as: <b>{current_user}</b></p>
        #     </div>
        # """, unsafe_allow_html=True)
        st.markdown(
            "<h3 style='text-align: center; color: #1e3c72;'>⚙️ Settings & Controls</h3>",
            unsafe_allow_html=True
        )

        # 🎯 Select Semantic Model with Dropdown
        # selected_model = st.selectbox(
        #     "📁 Select Data Model:",
        #     AVAILABLE_SEMANTIC_MODELS_PATHS,
        #     format_func=lambda s: s.split("/")[-1],
        #     key="selected_semantic_model_path",
        #     on_change=reset_session_state
        # )

        # st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
        # st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)


        # 🔍 Insight Generation Toggle
        enable_insights = st.toggle("💡 Enable Insight Generation", key="toggle_insights",on_change=enable_insight_generation)
        if enable_insights:
            st.session_state.insight_generation = True

            # 🎛️ Slider for Max Rows (Only Visible When Insights are Enabled)
            st.slider(
                "📊 Max Rows for Insights:",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
                key="max_rows_for_llm",
                help="Limits the number of rows passed to the LLM for generating insights to avoid token size limits"
            )

        # st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
        st.markdown("<div class='blur-divider'></div>", unsafe_allow_html=True)


        

        # 🔄 Enable to display raw data Toggle
        enable_raw_data = st.toggle("💻 Enable to view Raw Data", key="toggle_raw_data",on_change=enable_raw_data_generation)
        if enable_raw_data:
            st.session_state.raw_data_generation = True 

        # st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
        st.markdown("<div class='blur-divider'></div>", unsafe_allow_html=True)

        # 🔄 Enable the Vizualization toggle
        enable_viz = st.toggle("📊 Enable The Vizualization", key="toggle_viz",on_change=enable_data_viz)
        if enable_viz:
            st.session_state.display_viz = True

        # st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
        st.markdown("<div class='blur-divider'></div>", unsafe_allow_html=True)

        # 🔄 Follow-up Suggestions Toggle
        enable_followups = st.toggle("🔁 Enable Follow-up Suggestions", key="toggle_followups",on_change=enable_follow_up_suggestions)
        if enable_followups:
            st.session_state.follow_up_suggestions = True

        # st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
        # st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

        # 🧹 Clear Chat History Button
        # st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        # if st.button("🧹 Clear Chat History", use_container_width=True):
        #     reset_session_state()
        # st.markdown("</div>", unsafe_allow_html=True)
        # 🧹 Clear Chat History Button - Styled with Light Red Background
        # 🧹 Clear Chat History Button - Styled with Light Red Background
        st.markdown("<div class='clear-chat-btn' style='text-align: center;'>", unsafe_allow_html=True)
        if st.button("🧹 Clear Chat History", use_container_width=True):
            reset_session_state()
        st.markdown("</div>", unsafe_allow_html=True)

def generate_uuid():
    generate_uuid= f"""SELECT UUID_STRING()"""
    uuid=session.sql(generate_uuid).collect()[0][0]
    # st.write(st.session_state)
    if "uuid" not in st.session_state:
        st.session_state.uuid = uuid

def handle_user_inputs():
    """Handle user inputs from the chat interface."""
    # Handle chat input
    user_input = st.chat_input("What is your question?")
    if user_input:
        process_user_input(user_input)
    # Handle suggested question click
    elif st.session_state.active_suggestion is not None:
        suggestion = st.session_state.active_suggestion
        st.session_state.active_suggestion = None
        process_user_input(suggestion)


def handle_error_notifications():
    if st.session_state.get("fire_API_error_notify"):
        st.toast(f"An API error has occured! : {st.session_state['content']}", icon="🚨")
        st.session_state["fire_API_error_notify"] = False


def process_user_input(prompt: str):
    """
    Process user input and update the conversation history.

    Args:
        prompt (str): The user's input.
    """
    
    
    # Create a new message, append to history and display immediately
    new_user_message = {
        "role": "user",
        "content": [{"type": "text", "text": prompt}],
    }
    st.session_state.messages.append(new_user_message)
    with st.chat_message("user"):
        #st.markdown(f"**💬 You:** {prompt}")
        user_msg_index = len(st.session_state.messages) - 1
        display_message(new_user_message["content"], user_msg_index)


    
    with st.chat_message("analyst"):
        with st.spinner("🤖 Thinking... Generating insights..."):
            # time.sleep(1)
            
            # Pass the entire conversation history (including previous messages) to the API
            try:
                response, error_msg = get_analyst_response(st.session_state.messages)
            except:
                response = {"content":"Something went Wrong!","request_id":"NO ID"}
                error_msg = "Error - Something went wrong!"

            # st.write(response)
            
            if error_msg is None:
                analyst_message = {
                    "role": "analyst",
                    "content": response["content"],
                    "request_id": response["request_id"],
                }
            else:
                analyst_message = {
                    "role": "analyst",
                    "content": [{"type": "text", "text": error_msg}],
                    "request_id": response["request_id"],
                }
                st.session_state["fire_API_error_notify"] = True
            
            # Append the analyst response to the conversation history
            st.session_state.messages.append(analyst_message)

            if st.session_state.follow_up_suggestions:
                # Show additional followup questions if the last message contains SQL, and the proper feature flag is set
                if (last_chat_message_contains_sql()):
                    get_and_display_smart_followup_suggestions()
    st.rerun()


def get_analyst_response(messages: List[Dict]) -> Tuple[Dict, Optional[str]]:
    """
    Send chat history to the Cortex Analyst API and return the response.

    Args:
        messages (List[Dict]): The conversation history.

    Returns:
        Optional[Dict]: The response from the Cortex Analyst API.
    """
    # Prepare the request body with the user's prompt and full conversation history
    # -> Only process the latest question which doesnt have the result df saved.
    filtered_messages = [{k: v for k,v in d.items() if k not in ["summary_insights","judge_result","llm_insights","result_df","insights_enabled"]} for d in messages]
    request_body = {
        "messages": filtered_messages,  # Pass the entire conversation history here
        "semantic_model_file": f"@{st.session_state.selected_semantic_model_path}",
    }

    # Send a POST request to the Cortex Analyst API endpoint
    # Adjusted to use positional arguments as per the API's requirement
    # resp = _snowflake.send_snow_api_request(
    #     "POST",  # method
    #     API_ENDPOINT,  # path
    #     {},  # headers
    #     {},  # params
    #     request_body,  # body
    #     None,  # request_guid
    #     API_TIMEOUT,  # timeout in milliseconds
    # )

    analyst_response = session.sql(f"CALL ANALYST_CALL(PARSE_JSON('''{json.dumps(request_body)}'''))").collect()
    analyst_response = json.loads(analyst_response[0]["ANALYST_CALL"]) 
    print("ANALYSTREPONSE: ",analyst_response)

    resp = analyst_response["message"]
    print("resp: ",resp)

    status = 400
    # Content is a string with serialized JSON object
    try:
        parsed_content = resp
        status = 200
        parsed_content["request_id"] = analyst_response['request_id']
    except:
        status = 400

    # Check if the response is successful
    if status < 400:
        # Return the content of the response as a JSON object
        return parsed_content, None
    else:
        st.session_state.content['resp'] = resp
        st.session_state.content['parsed_content'] = resp
        
        # Craft readable error message
        error_msg = f"""
🚨 An Analyst API error has occurred 🚨

* response code: `{status}`
* request-id: `{analyst_response['request_id']}`
* error code: `ERROR`

Message:

        """
        # st.write(parsed_content)
        return parsed_content, error_msg

### Set of functions to display suggestions for follow up questions

def get_last_chat_message_idx() -> str:
    """Get message index for the last message in chat."""
    #st.write(f"get_last_chat_message_idx : {len(st.session_state.messages) - 1}")
    return len(st.session_state.messages) - 1
    
def last_chat_message_contains_sql() -> str:
    """Check if the last message in chat contains SQL content."""
    last_msg = st.session_state.messages[get_last_chat_message_idx()]
    msg_content_types = {c["type"] for c in last_msg["content"]}
    return "sql" in msg_content_types

def message_idx_to_question(idx: int) -> str:
    """
    Retrieve the question text from a message in the session state based on its index.

    This function checks the role of the message and returns the appropriate text:
    * If the message is from the user, it returns the prompt content
    * If the message is from the analyst and contains an interpretation of the question, it returns
    the interpreted question
    * Otherwise, it returns the previous user prompt

    Args:
        idx (int): The index of the message in the session state.

    Returns:
        str: The question text extracted from the message.
    """
    msg = st.session_state.messages[idx]

    # if it's user message, just return prompt content
    if msg["role"] == "user":
        return str(msg["content"][0]["text"])

    # If it's analyst response, if it's possibleget question interpretation from Analyst
    if msg["content"][0]["text"].startswith(
        "This is our interpretation of your question:"
    ):
        return str(
            msg["content"][0]["text"]
            .strip("This is our interpretation of your question:\n")
            .strip("\n")
            .strip("_")
        )

    # Else just return previous user prompt
    return str(st.session_state.messages[idx - 1]["content"][0]["text"])

def get_semantic_model_desc_from_messages() -> str:
    """Retrieve semantic model description from chat history.

    It assumes that in history there was a descritpion provided by Cortex Analyst,
    and it starts with "This semantic data model contains information about".
    """
    for msg in st.session_state.messages:
        for content in msg["content"]:
            if content["type"] == "text" and content["text"].startswith(
                "This semantic data model contains information about"
            ):
                return content["text"]
    return ""

def get_question_suggestions(
    previous_question: str, semantic_model_desc: str, requested_suggestions: int = 3
) -> Tuple[List[str], Optional[str]]:
    """
    Generate follow-up questions based on the previous question asked by the user and the semantic model description.

    This function utilizes the Snowflake Cortex Compleate to generate follow-up questions that encourage the user
    to explore the data in more depth.

    Args:
        previous_question (str): The last question asked by the user.
        semantic_model_desc (str): The description of the underlying semantic model provided by the analyst.
        requested_suggestions (int, optional): The number of follow-up questions to generate. Defaults to 3.

    Returns:
        Tuple[List[str], Optional[str]]: A tuple containing a list of generated follow-up questions and an optional error message.
                                         If an error occurs, the list of suggestions will be empty and the error message will be provided.
    """
    global session
    prompt = f"""
You will suggest follow-up questions to the Business User who is interacting with data via Cortex Analyst - "Talk to your data" solution from Snowflake. Here is the description provided by Analyst on the underlying semantic model:
{semantic_model_desc}

The user's goal is to gain insights into underlying data. They have previously asked:
{previous_question}

Now generate {requested_suggestions} follow-up questions that encourage the user to explore the data in more depth. The tone should be formal and concise. Please provide questions that are precise and non-ambiguous.

Some examples of good follow-up questions might include: "What are the top 3 factors contributing to [specific trend]?" or "How does [specific variable] affect [outcome]?"

Output your answer as a JSON list of strings, like this:
["suggestion 1", "suggestion 2", "suggestion 3"]

Refrain from adding any other text before or after the generated list.
Here is the answer:
[
"""
    try:
        
        # completion_response_raw = snowflake.cortex.complete(
        #     model="llama3.1-70b",
        #     prompt=prompt,
        #     session=session,
        #     #options=cortex.CompleteOptions(temperature=0.2),
        # )
        prompt=prompt.replace("'", "")
        completion_response_raw = session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{prompt}')").collect()[0][0]
    
        completion_response_parsed = json.loads(completion_response_raw)
        #st.write(f"completion_response_parsed : {completion_response_parsed}")
        # https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex#returns
        # parsed_sugggedtions = json.loads(
        #     completion_response_parsed["choices"][0]["messages"]
        # )
    except SnowparkSQLException as e:
        err_msg = f"Error while generating suggestions thtough cortex.Complete: {e}"
        return [], err_msg
    except json.JSONDecodeError as e:
        err_msg = f"Error while parsing reponse from cortex.Compleate: {e}"
        return [], err_msg

    return completion_response_parsed, None
    
def get_and_display_smart_followup_suggestions():
    """Get smart followup questions for the last message and update the session state."""
    with st.spinner("Generating followup questions..."):
        question = message_idx_to_question(get_last_chat_message_idx())
        sm_description = get_semantic_model_desc_from_messages()
        suggestions, error_msg = get_question_suggestions(question, sm_description)
        # If suggestions were successfully generated update the session state
        if error_msg is None:
            st.session_state.messages[-1]["content"].append(
                {"type": "text", "text": "__Suggested followups:__"}
            )
            st.session_state.messages[-1]["content"].append(
                {"type": "suggestions", "suggestions": suggestions}
            )
        # Else show notification containing error message
        # else:
        #     add_to_notification_queue(error_msg, "error")
            
def display_conversation():
    """
    Display the conversation history between the user and the assistant.
    """
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]
        with st.chat_message(role):
            display_message(content, idx)


def display_message(content: List[Dict[str, str]], message_index: int):
    """
    Display a single message content.

    Args:
        content (List[Dict[str, str]]): The message content.
        message_index (int): The index of the message.
    """
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "suggestions":
            # Display suggestions as buttons
            for suggestion_index, suggestion in enumerate(item["suggestions"]):
                if st.button(
                    suggestion, key=f"suggestion_{message_index}_{suggestion_index}"
                ):
                    st.session_state.active_suggestion = suggestion
        elif item["type"] == "sql":
            # Display the SQL query and results
            returned_df, returned_summary=display_sql_query(item, message_index)
            # st.text(returned_df)
            # st.write(session.get_current_user())
             ## --> GP , bring back later
            # Add thumbs-up and thumbs-down buttons for feedback
            #thumbs_up, thumbs_down = st.columns([1, 1])
            thumbs_up, thumbs_down, feedback_form_col = st.columns([1, 1, 8])
            generate_uuid()
            # st.write(st.session_state.uuid)
            if "request_id" in st.session_state.messages[message_index]:
                save_query("NIKHIL",
                           st.session_state.uuid,
                        st.session_state.messages[message_index]["content"][0]["text"],
                        item["statement"],
                        st.session_state.messages[message_index-1]["content"][0]["text"]
                    )
            else:
                 save_query("NIKHIL",
                            st.session_state.uuid,
                        st.session_state.messages[message_index-1]["content"][0]["text"],
                        item["statement"],
                        st.session_state.messages[message_index-1]["content"][0]["text"])
            # save_query(st.experimental_user["user_name"],
            #             st.session_state.messages[message_index]["content"][0]["text"],
            #             item["statement"],st.session_state.messages[message_index-1]["content"][0]["text"]
            #         )

            # with thumbs_up:
            #     if st.button("👍", key=f"thumbs_up_{message_index}"):
            #         st.session_state.messages[message_index]["feedback"] = "thumbs_up"
            #         # save_query(st.experimental_user,
            #         #     st.session_state.messages[message_index]["content"][0]["text"],
            #         #     item["statement"],st.session_state.messages[message_index-1]["content"][0]["text"]
            #         # )
            # with thumbs_down:
            #     if st.button("👎", key=f"thumbs_down_{message_index}"):
            #         st.session_state.messages[message_index]["feedback"] = "thumbs_down"
            #         ####################################################################################
            #         # st.write(message_index)
            #         # st.write(st.session_state.messages[message_index-1]["content"][0]["text"])
            #         save_feedback(st.experimental_user["user_name"],
            #             st.session_state.messages[message_index]["content"][0]["text"],
            #             item["statement"],st.session_state.messages[message_index-1]["content"][0]["text"]
            #         )
            with thumbs_up:
                if st.button("👍", key=f"thumbs_up_{message_index}",help="Good response"):
                    st.session_state.messages[message_index]["feedback"] = "thumbs_up"
                    save_feedback(returned_df,returned_summary,message_index,"NIKHIL",
                        st.session_state.messages[message_index-1]["content"][0]["text"],
                        item["statement"],st.session_state.messages[message_index-1]["content"][0]["text"],
                                  feedback_type="thumbs_up",feedback_text=''
                    )
                    st.rerun()
                    # save_query(st.experimental_user,
                    #     st.session_state.messages[message_index]["content"][0]["text"],
                    #     item["statement"],st.session_state.messages[message_index-1]["content"][0]["text"]
                    # )
            with thumbs_down:
                if st.button("👎", key=f"thumbs_down_{message_index}",help="Bad response"):
                    st.session_state.messages[message_index]["feedback"] = "thumbs_down"
                    st.session_state.active_feedback_index = message_index
                    st.rerun()
                    ####################################################################################
                    # st.write(message_index)
                    # st.write(st.session_state.messages[message_index-1]["content"][0]["text"])
            # st.write(st.session_state.active_feedback_index)
            if st.session_state.active_feedback_index == message_index:
                            
                with feedback_form_col:
                    feedback_key = f"feedback_text_{message_index}"
                    
                    st.text_area(
                              "Please provide specific feedback:",
                              key=feedback_key,
                              placeholder="What was wrong with this response?"
                         )
                    submit_key = f"submit_feedback_{message_index}"
                    if st.button("Submit Feedback", key=submit_key):
                        
                        feedback_text = st.session_state.get(feedback_key, "").strip() # Get text, default to "", strip whitespace
                        if feedback_text:
                            # st.write(feedback_text)
                            
                            st.success('Saving the feedback to the table!')
                            save_feedback(returned_df,returned_summary,message_index,"NIKHIL",
                                        st.session_state.messages[message_index-1]["content"][0]["text"],
                                        item["statement"],st.session_state.messages[message_index-1]["content"][0]["text"],
                                                  feedback_type="thumbs_down", feedback_text=feedback_text
                                    )
                            st.session_state.active_feedback_index = None
                            st.rerun()
                        else:
                            st.warning('Please enter some feedback before submitting')
                                # st.success('Write to table')
                                # with st.container():
                                #     feedback_text = st.session_state.get(feedback_key, "").strip() # Get text, default to "", strip whitespace
                                #     if feedback_text: # Only save if text is not empty
                                #         st.session_state.messages[message_index]["feedback"] = {"rating": "thumbs_down", "detail": feedback_text}
                                #     st.session_state.active_feedback_index = None
    
                                #     st.success('Write to table')
                                #     save_feedback(message_index,st.experimental_user["user_name"],
                                #         st.session_state.messages[message_index-1]["content"][0]["text"],
                                #         item["statement"],st.session_state.messages[message_index-1]["content"][0]["text"],
                                #                   feedback_type="thumbs_down"
                                #     )
                    

def display_sql_query(item: dict, message_index: int):
    """
    Executes the SQL query and displays the results in form of data frame and charts.

    Args:
        sql (str): The SQL query.
        message_index (int): The index of the message.
    """
    sql = item["statement"]
    # Display the SQL query
    with st.expander("SQL Query", expanded=False):
        st.code(sql, language="sql")

    # Display the results of the SQL query
    with st.expander("Results", expanded=True):
        content = st.session_state.messages[message_index]['content']
        with st.spinner("Running SQL..."):
            has_result_df = any("result_df" in d for d in content)
            if has_result_df is False:        
                df, err_msg = get_query_exec_result(sql, message_index)
            else:
                # Will get the value of 'result_df' if it exists, else None
                df = next((d["result_df"] for d in content if "result_df" in d), None)
                df = pd.read_json(df)
                
            if df is None:
                st.error(f"Could not execute generated SQL query. Error: {err_msg}")
                return

            if df.empty:
                st.write("Query returned no data")
                return

            # Show query results in three tabs - added insights tab
            # data_tab, chart_tab,insights_tab,LLM_Judge_Rating_tab = st.tabs(["Data 📄", "Chart 📈", "Insights 💡", "LLM_Judge_Rating :star:"])
            summary_tab,insights_tab,chart_tab,data_tab = st.tabs(["Summary 📓","Insights 💡", "Chart 📈","Data 📄"])

            with summary_tab:
                user_query = st.session_state.messages[message_index-1]["content"][0]["text"]

                with st.spinner("Generating summary..."):
                    has_summary_insights = any("summary_insights" in d for d in content)
                    if has_summary_insights is False:
                        summary = generate_natural_language_summary(df, user_query,message_index)
                    else:
                        # Will get the value of 'result_df' if it exists, else None
                        summary = next((d["summary_insights"] for d in content if "summary_insights" in d), None)  
                    st.markdown(summary)
            
            with data_tab:
                ## GP->
                if st.session_state.raw_data_generation:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.markdown("Please enable the toggle to view the Raw Data")

            with chart_tab:
                if st.session_state.display_viz:
                    display_charts_tab(df, message_index)
                else:
                    st.markdown("Please enable the toggle to Vizualize the Data")
                
            with insights_tab:
                # Get the original user query from the message history
                # st.write(st.session_state.messages)
                user_query = st.session_state.messages[message_index-1]["content"][0]["text"]
                
                # Generate and display insights usng Snoiwflake COMPLETE
                with st.spinner("Generating insights..."):
                    has_llm_insights = any("llm_insights" in d for d in content)
                    if has_llm_insights is False:
                        if st.session_state.insight_generation:
                            #if item["insights_enabled"] is True: # or item["insights_enabled"].lower() == "true":
                            if st.session_state.insight_generation:
                                insights = generate_insights_with_snowflake_complete(df, user_query, message_index)
                            else:
                                insights = "Insights generation has been disabled during this conversation"
                        else:
                            insights = "Insights generation has been disabled during this conversation"
                    else:
                        # Will get the value of 'result_df' if it exists, else None
                        insights = next((d["llm_insights"] for d in content if "llm_insights" in d), None)  
                    st.markdown(insights)
        df_json=df.to_json()   
        return df_json, summary   
            # with LLM_Judge_Rating_tab:
            #      with st.spinner("Evaluating insights..."):
            #         has_judge_result = any("judge_result" in d for d in content)
            #         if has_judge_result is False: 
            #             if st.session_state.insight_generation:
            #                 if item["insights_enabled"] is True:
            #                     rating=judge_LLM(df,insights,user_query,message_index)
            #                 else:
            #                     rating = "Rating generation has been disabled during this conversation"
            #             else:
            #                 rating = "Rating generation has been disabled during this conversation"
            #         else:
            #             # Will get the value of 'result_df' if it exists, else None
            #             rating = next((d["judge_result"] for d in content if "judge_result" in d), None)  
            #         st.markdown(rating)
                     

def generate_natural_language_summary(df: pd.DataFrame, user_query: str,message_index: int) -> str:
    """
    Uses LLM to generate a natural language response based on the retrieved data.

    Args:
        df (pd.DataFrame): Dataframe containing query results.
        user_query (str): Original question asked by the user.

    Returns:
        str: AI-generated summary.
    """
    global session
    content = st.session_state.messages[message_index]['content']
    context = df.to_json(orient="records")  # Convert DataFrame to JSON for LLM
    # summary_prompt = f"""
    # You are an AI assistant summarizing database query results. 
    # A user asked: {user_query}
    
    # Based on the retrieved data: {context}, generate a short and clear answer.
    # Avoid raw data references unless necessary. Be precise, user-friendly, and insightful.

    # Give the response in Natural language just responding to user question and nothing extra. It should be to the point of the user question.
    # """
    summary_prompt = f"""
    You are an AI assistant summarizing database query results in a highly relevant, concise, and user-friendly manner. 

    **User Query:** {user_query}
    **Retrieved Data Context:** {context}

    ### 🔹 **Response Guidelines:**
    - Ensure the response is **precise, highly relevant**, and **directly answers the users question**.
    - The answer should be **clear, structured**, and **not exceed 300 words**.
    - Avoid unnecessary explanations or raw data references **unless required for clarity**.
    - If the data spans **multiple time periods**, summarize trends in a **business-friendly way**.
    - If the dataset contains **many records**, condense the response by summarizing the **top 10 results**.
    - Use **bullet points, short paragraphs, or key takeaways** for **better readability**.
    
    **⚡ Generate a short, crisp, and insightful answer tailored to the users query.**
"""

    # Use Snowflake Cortex or OpenAI for NLP Generation
    # response = send_to_llm(prompt)  # Replace with actual LLM API call
    summary_result = session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', '{summary_prompt}')").collect()[0][0]
    
        
    # Store the insights in the session state
    for item in content:
        if item.get("type") == "sql":
            item["summary_insights"] = summary_result
    st.session_state.messages[message_index]['content'] = content
    return summary_result




@st.cache_data(show_spinner=False)
def get_query_exec_result(query: str,message_index: int) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Execute the SQL query and convert the results to a pandas DataFrame.

    Args:
        query (str): The SQL query.

    Returns:
        Tuple[Optional[pd.DataFrame], Optional[str]]: The query results and the error message.
    """
    global session
    content = st.session_state.messages[message_index]['content']    
    try:
        df = session.sql(query).collect()
        df = pd.DataFrame(df)
       
        for item in content:
            if item.get("type") == "sql":
                item["result_df"] = df.to_json(orient="records")
                item["insights_enabled"] = st.session_state.insight_generation
        st.session_state.messages[message_index]['content'] = content
        return df, None
    except SnowparkSQLException as e:
        for item in content:
            if item.get("type") == "sql":
                item["result_df"] = None
                item["insights_enabled"] = st.session_state.insight_generation
        st.session_state.messages[message_index]['content'] = content
        return None, str(e)


def generate_insights_with_snowflake_complete(df: pd.DataFrame, user_query: str, message_index: int) -> str:
    """
    Generate insights from data using Snowflake COMPLETE function.
    
    Args:
        df (pd.DataFrame): The DataFrame containing the query results.
        
    Returns:
        str: The generated insights as text.
    """
    global session
    content = st.session_state.messages[message_index]['content']
    try:
        if df is None or df.empty:
            return "No data available to generate insights."
        
        # Convert the dataframe to JSON for the prompt
        json_data = df.to_json(orient='records')
        
        # Create a prompt for the Snowflake COMPLETE function
        insight_prompt = f"""
            You are a **Customer Support Business Analyst** specializing in **customer service analytics** for Logitechs **support ticket operations**.
        
        ## **About Logitech Customer Support Analytics**
        - This dataset contains information on **support tickets, customer complaints, issue resolution, and product service trends**.
        - It helps Logitech **analyze customer issues**, **improve support efficiency**, and **enhance customer satisfaction**.
        - The key business goals include:
          - **Identifying common customer issues** to improve product quality.
          - **Optimizing support resolution time** to enhance customer experience.
          - **Detecting trends in service requests** for proactive customer support strategies.
        
        ### **User Question:**  
        **Question Asked:**  
        "{user_query}"
        
        Given the following dataset in JSON format, summarize the key insights in **clear business language**.
        
        **JSON Data:**  
        **Support Ticket Data (in JSON format):**  
        "{json_data}"
        
        ---
        
        ### **Instructions for Response:**  
        Your response should be **business-focused**, **concise**, and written for **non-technical users** (Customer Service Managers, Operations Teams, and Business Decision-Makers).  
        Avoid unnecessary technical details. Focus on **practical insights** that Logitech can act upon.
        
        ---
        
        ### **1️⃣ Understanding the Data**  
        - Summarize **what this dataset represents** in **plain business language**.
        - Explain what the data reveals about **customer support efficiency**, **ticket resolution trends**, and **customer pain points**.
        - Answer key questions such as:
          - **What types of issues are most common?**
          - **Which product categories receive the highest number of complaints?**
          - **Which support channels (email, phone, web) are used the most?**
          - **Which regions have the highest volume of complaints?**
          - **Are there delays in resolving customer issues?**
        - Keep it in bullet points for **quick readability**.
        
        ---
        
        ### **2️⃣ Key Trends & Insights**  
        - Identify trends in **ticket volume** over time (daily, weekly, monthly).
        - Highlight **top reasons for customer complaints**.
        - Detect **patterns in order issues, product defects, or warranty claims**.
        - If there are **increasing** complaints for a product, suggest a possible reason.
        - Identify any delays in **ticket resolution times**.
        - Highlight **which support agents or teams handle the most cases**.
        - Compare **first-time resolution rates vs. reopened tickets**.
        - Identify **seasonality trends** (e.g., higher complaints during holiday sales).
        - If **NPS (Net Promoter Score) is available**, provide insights into **customer sentiment**.
        
        ---
        
        ### **3️⃣ Business Recommendations**  
        - If the dataset shows **clear trends that need action**, provide **data-driven recommendations**:
          - **Customer Experience Improvements:** Should Logitech optimize support channels or self-service options?
          - **Product Quality Enhancements:** Are some products frequently defective, requiring a **quality review**?
          - **Operational Efficiency:** Are ticket resolution times increasing? Should Logitech **optimize staffing or automation**?
          - **Warranty & Returns Strategy:** Are customers facing **delays in replacements or returns**?
          - **Regional Support Strategy:** Are **certain regions experiencing slower resolution times**? Should Logitech **allocate more resources**?
          - Examples of when to include prescriptive insights:
            - If **ticket resolution times are increasing**, suggest **adding automation, improving training, or increasing staffing**.
            - If **customers frequently complain about a product**, recommend a **product quality check or proactive communication**.
            - If **NPS scores are dropping**, suggest **customer satisfaction initiatives**.
          - If **no prescriptive insights can be derived**, **DO NOT** force recommendations.
        
        ---
        
        ### **4️⃣ Potential Business Challenges & Opportunities**  
        - Are **certain customer issues growing in frequency**?
        - Are there **bottlenecks in the support process** (e.g., long waiting times, unresolved tickets)?
        - Are some regions/customers **more likely to face repeated issues**?
        - Are there **gaps in customer education** leading to unnecessary support tickets?
        - Are there **high levels of product replacements** for specific SKUs?
        - Identify **opportunities for chatbot automation** or **proactive customer engagement**.
        
        ---
        
        ### **📌 Example Summary (For Reference):**
        - **Overview:** Customer complaints for **Webcam X100** increased by **20% in Q1**, with most issues related to **software compatibility**.
        - **Key Trend:** Tickets related to **warranty claims** peaked in **December due to holiday purchases**.
        - **(Prescriptive Analytics Applied)** First-time resolution rates dropped to **65%**, indicating a need for **agent training or better documentation**.
        - **(Potential Business Challenge)** Customers in **APAC** reported **longer wait times**, suggesting a **resource allocation review**.
        
        If **prescriptive analytics is not relevant**, exclude that section and focus only on **key insights**.
        
        ---
        
        ### **🔹 Important Guidelines:**
        1. **Be clear and to the point** – responses should be **concise and actionable**.
        2. **Do NOT force recommendations** – only suggest actions if **data supports it**.
        3. **Focus on business impact** – insights should help **Logitech improve customer experience**.
        4. **Use bullet points & structured responses** to improve readability.
        
        Now, summarize the dataset **based on the provided structure.**
        """
        
        # Call Cortex complete function
        # completion_response = snowflake.cortex.complete(
        #     model="llama3.1-8b",
        #     prompt=insight_prompt,
        #     session=session,
        #     options=cortex.CompleteOptions(temperature=0.2),
        # )

        summary_result = session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{insight_prompt}')").collect()[0][0]
    
        
        # Store the insights in the session state
        for item in content:
            if item.get("type") == "sql":
                item["llm_insights"] = summary_result
        st.session_state.messages[message_index]['content'] = content
        
        return summary_result
    
    except Exception as e:
        error_message = f"Error generating insights: {str(e)}"
        for item in content:
            if item.get("type") == "sql":
                item["llm_insights"] = error_message
        st.session_state.messages[message_index]['content'] = content
        return error_message

def save_feedback(returned_df,returned_summary,message_index,user_id: str, user_query: str, sql_query: str, raw_query: str,feedback_type:str,feedback_text:str):
    """
    Save the feedback (user query and SQL query) into the feedback table.

    Args:
        user_id (str): The ID of the user providing feedback.
        user_query (str): The user's original query.
        sql_query (str): The SQL query generated by the analyst.
        raw_query (str): The raw query string.
        session (Session): The Snowflake session object.
    """
    
    sql_query=sql_query.replace("'",'')
    table_name = 'KIPI_POC_DB.KIPI_POC_STG.feedback_with_text_agent_response'
    feedback_type = feedback_type
    feedback_time = datetime.now()
    feedback_text=feedback_text.replace("'",'')
    returned_df=returned_df.replace("'",'')
    returned_summary=returned_summary.replace("'",'')
    

    # if st.session_state.active_feedback_index == message_index:
    #     with feedback_form_col:
    #         feedback_key = f"feedback_text_{message_index}"
    #         st.text_area(
    #                   "Please provide specific feedback:",
    #                   key=feedback_key,
    #                   placeholder="What was wrong with this response?"
    #              )
    #         submit_key = f"submit_feedback_{message_index}"
    #         if st.button("Submit Feedback", key=submit_key):
    #             feedback_text = st.session_state.get(feedback_key, "").strip() # Get text, default to "", strip whitespace
    #             if feedback_text: # Only save if text is not empty
    #                 st.session_state.messages[message_index]["feedback"] = {"rating": "thumbs_down", "detail": feedback_text}
    #             st.session_state.active_feedback_index = None
    # query = f"""
    #         INSERT INTO {table_name} (user_id, raw_query, refined_query, sql_query, feedback, feedback_time)
    #         VALUES ('{user_id}', '{raw_query}', '{user_query}', '{sql_query}','{feedback_type}','{feedback_time}')
    #     """
    query = f"""
            INSERT INTO {table_name} (user_id, raw_query, refined_query, sql_query,agent_response,agent_summary, feedback, feedback_text, feedback_time)
            VALUES ('{user_id}', '{raw_query}', '{user_query}', '{sql_query}','{returned_df}','{returned_summary}','{feedback_type}','{feedback_text}','{feedback_time}')
        """
    
    try:
        
        
        
        # Execute the parameterized query
        session.sql(query).collect()
        st.success("Thank you! Your feedback helps make the Assistant better")
    except SnowparkSQLException as e:
        st.error(f"Error saving feedback: {e}")

def save_query(user_id: str, uuid:str, user_query: str, sql_query: str, raw_query: str):
    """
    Save the user query and SQL query into the query history table.
    
    Args:
        user_id (str): The ID of the user saving the query.
        uuid(str) : The UUID of the session.
        user_query (str): The user's original query.
        sql_query (str): The SQL query generated by the analyst.
        raw_query (str): The raw query string.
        session (Session): The Snowflake session object.
    """
    table_name = 'KIPI_POC_DB.KIPI_POC_STG.QUERY_HISTORY'
    query_time = datetime.now()
    uuid=uuid.replace("'",'')
    user_query=user_query.replace("'",'')
    sql_query=sql_query.replace("'",'')
    
    try:
        query = f"""
            INSERT INTO {table_name} (user_id, uuid, raw_query, refined_query, sql_query, query_time)
            VALUES ('{user_id}', '{uuid}', '{raw_query}', '{user_query}', '{sql_query}','{query_time}')
        """
        
        # Execute the parameterized query
        session.sql(query).collect()
        # st.success("Query and SQL generated Saved")
    except SnowparkSQLException as e:
        st.error(f"Error saving query: {e}")

########

# def save_feedback(user_id: str, user_query: str, sql_query: str, raw_query: str):
#     """
#     Save the feedback (user query and SQL query) into the feedback table.

#     Args:
#         user_id (str): The ID of the user providing feedback.
#         user_query (str): The user's original query.
#         sql_query (str): The SQL query generated by the analyst.
#         raw_query (str): The raw query string.
#         session (Session): The Snowflake session object.
#     """
#     table_name = 'DEMO_DB.REVENUE_TIMESERIES.feedback'
#     feedback_type = 'thumbs_down'
#     feedback_time = datetime.now()

#     query = f"""
#             INSERT INTO {table_name} (user_id, raw_query, refined_query, sql_query, feedback, feedback_time)
#             VALUES ('{user_id}', '{raw_query}', '{user_query}', '{sql_query}','{feedback_type}','{feedback_time}')
#         """
    
#     try:
        
        
#         # Execute the parameterized query
#         session.sql(query).collect()
#         st.success("Thank you for your feedback! We will improve based on your input.")
#     except SnowparkSQLException as e:
#         st.error(f"Error saving feedback: {e}")

# def save_query(user_id: str, user_query: str, sql_query: str, raw_query: str):
#     """
#     Save the user query and SQL query into the query history table.
    
#     Args:
#         user_id (str): The ID of the user saving the query.
#         user_query (str): The user's original query.
#         sql_query (str): The SQL query generated by the analyst.
#         raw_query (str): The raw query string.
#         session (Session): The Snowflake session object.
#     """
#     table_name = 'DEMO_DB.REVENUE_TIMESERIES.QUERY_HISTORY'
#     query_time = datetime.now()
    
#     try:
#         query = f"""
#             INSERT INTO {table_name} (user_id, raw_query, refined_query, sql_query, query_time)
#             VALUES ('{user_id}', '{raw_query}', '{user_query}', '{sql_query}','{query_time}')
#         """
        
#         # Execute the parameterized query
#         session.sql(query).collect()
#         st.success("Query and SQL generated Saved")
#     except SnowparkSQLException as e:
#         st.error(f"Error saving query: {e}")








###### judge_LLM --> Bring this back for Judge LLM
# def judge_LLM(df: pd.DataFrame,  insights, user_query, message_index) -> str:
#     """
#     Judge the quality of the insights generated by the LLM.

#     Args:
#         original_question (str): The input question provided by the user.
#         modified_question (str): The question modified by the LLM.
#         sql_query (str): The SQL query generated by the Cortex Analyst.
#         dataframe (pd.DataFrame): The dataframe generated from the SQL execution.
#         insights (str): The insights generated by the LLM.

#     Returns:
#         str: The evaluation score or feedback from the LLM.
#     """
#     global session
#     content = st.session_state.messages[message_index]['content']
    
#     try:
#         if df is None or df.empty:
#             return "No data available to judge insights."
        
#         # Use only the number of rows specified in the slider
#         max_rows = st.session_state.get('max_rows_for_llm', 100)
#         df_limited = df.head(max_rows)
        
#         # Convert the dataframe to JSON for the prompt
#         json_data = df_limited.to_json(orient='records')
#         df=df.replace("'","",regex=True)
#         insights = insights.replace("'", "")
#         # Prepare the evaluation prompt
#         prompt = f"""
#             Carefully evaluate the generated summary using a multifaceted approach:
            
#             Evaluation Criteria:
#             1. Relevance (provide score only in between 0-2.5, dont score beyond 2.5):
#                - How directly does the summary address the original user query?
#                - Are key aspects of the query reflected in the insights?
            
#             2. Depth of Insight (provide score only in between 0-2.5, dont score beyond 2.5):
#                - Does the summary go beyond surface-level observations?
#                - Are there meaningful interpretations of the data?
            
#             3. Clarity and Readability (provide score only in between 0-2.5, dont score beyond 2.5):
#                - Is the summary clear and easy to understand?
#                - Are complex ideas explained coherently?
            
#             4. Actionability (provide score only in between 0-2.5, dont score beyond 2.5):
#                - Do the insights provide potential actions or recommendations?
#                - Can a decision-maker derive value from these insights?
            
#             User Query: {user_query}
#             SQL Output: {json_data}
#             Generated Summary: {insights}

#             FORMAT:
#                 Evaluation Summary
#                  1. Relevance
#                     - 2 sub points 
#                  2. Depth of Insight
#                     - 2 sub points 
#                  3. Clarity and Readability
#                     - 2 sub points 
#                  4. Actionability
#                     - 2 sub points 
    
#                 Total Score: 
    
#                 Breakdown of Scoring:
    
#                 Improvement Suggestions:
#                     - 2-3 sub points 
            
#             IMPORTANT: 
#             - Strictly always use new line for description.
#             - Strictly follow the given FORMAT only.
#             - Display heading in bold.
#             - Strictly display description in new line.
#             - Ensure the sum of score stays within score of 10.
#             - Provide a detailed breakdown of your scoring.
#             - Explain why you chose each point value.
#             - Avoid defaulting to the same score repeatedly for both score i.e total score and Evaluation Criteria scores 
#             - If the summary lacks critical elements, explain specific improvements
#             - Strictly display the scoring at the end in Scoring section, dont display them in the headers.
#         """
        
#         # Call Cortex complete function
#         # evaluation = snowflake.cortex.complete(
#         #     model="llama3.1-70b",
#         #     prompt=prompt,
#         #     session=session,
#         #     #options=cortex.CompleteOptions(temperature=0.1),
#         # )

#         evaluation = session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{prompt}')").collect()[0][0]
    
        
#         # Store the evaluation in the session state
#         for item in content:
#             if item.get("type") == "sql":
#                 item["judge_result"] = evaluation
        
#         return evaluation
        
#     except Exception as e:
#         error_message = f"Error judging insights: {str(e)}"
#         for item in content:
#             if item.get("type") == "sql":
#                 item["judge_result"] = error_message
#         return error_message


#########


def display_charts_tab(df: pd.DataFrame, message_index: int) -> None:
    """
    Display the charts tab.
    Args:
        df (pd.DataFrame): The query results.
        message_index (int): The index of the message.
    """
    # Allow user to limit the number of rows for chart rendering
    max_rows_for_chart = st.slider(
        "Max rows for chart", 
        min_value=10, 
        max_value=1000, 
        value=min(100, len(df)), 
        step=10,
        key=f"max_rows_chart_{message_index}"
    )
    
    # Apply the row limit for chart rendering
    df_limited = df.head(max_rows_for_chart)
    
    # Show the number of rows being displayed vs total
    st.caption(f"Showing {len(df_limited)} of {len(df)} rows in chart")
    
    # There should be at least 2 columns to draw charts
    if len(df_limited.columns) >= 2:
        all_cols_set = set(df_limited.columns)
        # col1, col2 = st.columns(2)
        # x_col = col1.selectbox(
        #     "X axis", list(all_cols_set), key=f"x_col_select_{message_index}"
        # )
        
        # # Make sure to update the available y-axis options when x-axis changes
        # y_options = list(all_cols_set.difference({x_col}))
        # y_col = col2.selectbox(
        #     "Y axis",
        #     y_options,
        #     key=f"y_col_select_{message_index}",
        # )
        
        # chart_type = st.selectbox(
        #     "Select chart type",
        #     options=["Line Chart 📈", "Bar Chart 📊", "Scatter Chart"],
        #     key=f"chart_type_{message_index}",
        # )
        col1, col2 , col3 = st.columns(3)
        x_col = col1.selectbox(
            "X axis", list(all_cols_set), key=f"x_col_select_{message_index}"
        )
        
        # Make sure to update the available y-axis options when x-axis changes
        y_options = list(all_cols_set.difference({x_col}))
        y_col = col2.selectbox(
            "Y axis",
            y_options,
            key=f"y_col_select_{message_index}",
        )
        
        chart_type = col3.selectbox(
            "Select chart type",
            options=["Line Chart 📈", "Bar Chart 📊", "Scatter Chart"],
            key=f"chart_type_{message_index}",
        )
        
        # Create the chart with the limited dataframe
        try:
            if chart_type == "Line Chart 📈":
                st.line_chart(data=df_limited, x=x_col, y=y_col)
            elif chart_type == "Bar Chart 📊":
                st.bar_chart(data=df_limited, x=x_col, y=y_col)
            elif chart_type == "Scatter Chart":
                st.scatter_chart(data=df_limited, x=x_col, y=y_col)
        except Exception as e:
            st.error(f"Error creating chart: {e}")
            st.info("Try selecting different columns or reducing the number of rows.")
    else:
        st.write("At least 2 columns are required to create a chart")

def display_suggested_questions():
    """Display suggested questions categorized into Descriptive & Predictive Analytics with a modern UI feel"""
    
    # Define suggested questions
    descriptive_questions = [
        "What are the top 5 most frequently reported quality issues by the customers?",
        "Which products have the highest number of in-warranty replacements?",
        "Which products were replaced most frequently overall?",
        "Which countries had the highest number of product replacements?",
        "Are there any spikes or trends in the number of tickets created over time?",
        "Which problem categories generate the most support tickets?"
    ]

   

    with st.expander("💡 **Suggested Questions**", expanded=False):
        st.markdown("""
            <div style="
                text-align: center; 
                font-size: 22px; 
                font-weight: bold;
                color: #4A90E2;
                margin-bottom: 10px;">
                📊 Descriptive Analytics
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        for idx, question in enumerate(descriptive_questions):
            col = col1 if idx % 2 == 0 else col2
            col.markdown(f"""
                <div style="
                    background-color: #f3f3f3; 
                    border-radius: 8px; 
                    padding: 10px; 
                    margin-bottom: 5px; 
                    font-size: 16px;
                    font-weight: 500;
                    color: #333;
                    text-align: center;">
                    🔹 {question}
                </div>
            """, unsafe_allow_html=True)

       

if __name__ == "__main__":
    main()