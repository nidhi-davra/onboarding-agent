import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(page_title="Onboarding Agent for InnovateTech", page_icon="🤖", layout="wide")

# --- Constants for Agent Personas ---
TEAM_LEAD = "Team Lead"
HR_AGENT = "HR"

# --- State Management ---
# Initialize user details and agent selection
if "details_submitted" not in st.session_state:
    st.session_state.details_submitted = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_designation" not in st.session_state:
    st.session_state.user_designation = ""
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = TEAM_LEAD  # Default to Team Lead

# Initialize separate states for each agent
if TEAM_LEAD not in st.session_state:
    st.session_state[TEAM_LEAD] = {
        "messages": [],
        "checklist": [
            {"topic": "Greeting and Welcome", "status": "pending"},
            {"topic": "Role Introduction & Setup", "status": "pending"},
            {"topic": "The 1-on-1 Meeting Cadence", "status": "pending"},
            {"topic": "Team Communication Policy", "status": "pending"},
        ],
    }
if HR_AGENT not in st.session_state:
    st.session_state[HR_AGENT] = {
        "messages": [],
        "checklist": [
            {"topic": "Welcome & Account Setup", "status": "pending"},
            {"topic": "Company Policies", "status": "pending"},
            {"topic": "Bond Agreement", "status": "pending"},
        ],
    }


# --- Backend API Configuration ---
BACKEND_URL = "http://127.0.0.1:8000/api/chat"

# --- Helper Functions ---
def get_initial_greeting(agent_type):
    """Calls the backend to get a personalized greeting for the selected agent."""
    agent_state = st.session_state[agent_type]
    initial_context = [{"sender": "user", "text": f"My name is {st.session_state.user_name} and I am joining as a {st.session_state.user_designation}."}]
    payload = {"messages": initial_context, "checklist": agent_state["checklist"], "agent_type": "team_lead" if agent_type == TEAM_LEAD else "hr"}
    try:
        with st.spinner(f"{agent_type} is getting ready..."):
            response = requests.post(BACKEND_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
            agent_state["messages"].append(data["reply"])
            agent_state["checklist"] = data["checklist"]
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the backend: {e}")

def display_checklist(agent_type):
    """Renders the checklist for the selected agent."""
    agent_state = st.session_state[agent_type]
    st.sidebar.title(f"{agent_type} Onboarding")
    st.sidebar.write("Here are the topics we'll cover:")
    status_icons = {"completed": "✅", "in_progress": "➡️", "pending": "◻️"}
    for item in agent_state["checklist"]:
        st.sidebar.markdown(f"{status_icons.get(item['status'], '◻️')} {item['topic']}")

# --- UI Rendering ---
# Step 1: Collect User Details
if not st.session_state.details_submitted:
    st.title("Welcome to InnovateTech! 👋")
    st.write("Before we begin, please tell us a little about yourself.")
    
    with st.form("user_details_form"):
        name = st.text_input("What is your name?")
        designation = st.text_input("What is your designation?")
        initial_agent = st.radio(
            "Who would you like to speak with first?",
            (TEAM_LEAD, HR_AGENT),
            horizontal=True,
        )
        submitted = st.form_submit_button("Start Onboarding")
        
        if submitted:
            if name and designation and initial_agent:
                st.session_state.user_name = name
                st.session_state.user_designation = designation
                st.session_state.selected_agent = initial_agent
                st.session_state.details_submitted = True
                st.rerun()
            else:
                st.warning("Please fill out all fields.")
else:
    # Step 2: Main Application Interface
    st.title("Onboarding Agent")
    
    # Persona Selector, with the default set by the initial form choice
    agent_type = st.selectbox(
        "Choose an agent to talk to:",
        (TEAM_LEAD, HR_AGENT),
        index=(TEAM_LEAD, HR_AGENT).index(st.session_state.selected_agent)
    )
    # Update the session state if the user changes the selection
    st.session_state.selected_agent = agent_type
    
    st.sidebar.header(f"Welcome, {st.session_state.user_name}!")
    display_checklist(agent_type)

    agent_state = st.session_state[agent_type]

    # Get initial greeting if chat is new for the selected agent
    if not agent_state["messages"]:
        get_initial_greeting(agent_type)
        st.rerun()

    # Display chat history for the selected agent
    for message in agent_state["messages"]:
        if message.get("text"):
            with st.chat_message("assistant" if message["sender"] != "user" else "user"):
                st.markdown(message["text"])

    # Chat input
    if prompt := st.chat_input(f"Your response to {agent_type}..."):
        # Show the user's message immediately in the UI
        with st.chat_message("user"):
            st.markdown(prompt)

        # Persist the user's message
        agent_state["messages"].append({"sender": "user", "text": prompt})

        # Assistant placeholder while waiting for backend
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("Thinking…")

            payload = {
                "messages": agent_state["messages"],
                "checklist": agent_state["checklist"],
                "agent_type": "team_lead" if agent_type == TEAM_LEAD else "hr"
            }

            try:
                response = requests.post(BACKEND_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
                response.raise_for_status()
                data = response.json()
                agent_state["messages"].append(data["reply"])
                agent_state["checklist"] = data["checklist"]
                placeholder.markdown(data["reply"]["text"])  # Replace placeholder with assistant reply
            except requests.exceptions.RequestException as e:
                placeholder.markdown(f"Could not connect to the backend: {e}")

        # Rerun to refresh sidebar checklist and persist full history rendering
        st.rerun()