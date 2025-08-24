# Onboarding Agent

This project is a conversational AI agent designed to help onboard new members of a web development team. It acts as a friendly team lead, "Alex," who guides the new hire through their initial setup and introduces them to team processes.

The application is built with a **FastAPI** backend and a **Streamlit** frontend.

## Project Structure

```
.
├── backend/
│   ├── main.py             # FastAPI application
│   └── requirements.txt    # Python dependencies for the backend
├── frontend/
│   ├── app.py              # Streamlit application
│   └── requirements.txt    # Python dependencies for the frontend
├── prompt.md               # The system prompt defining the AI's persona and duties
└── README.md               # This file
```

## Getting Started

Follow these steps to get the application running locally.

### 1. Prerequisites

*   Python 3.8+
*   `pip` for package management

### 2. Backend Setup

First, set up and run the FastAPI server.

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install the required packages
pip install -r requirements.txt

# Run the FastAPI server
# The --reload flag will automatically restart the server on code changes.
uvicorn main:app --reload
```

The backend API will be available at `http://127.0.0.1:8000`.

### 3. Frontend Setup

In a **new terminal window**, set up and run the Streamlit frontend.

```bash
# Navigate to the frontend directory
cd frontend

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install the required packages
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app.py
```

The frontend application will open in your browser, and you can start chatting with the onboarding agent!

### 4. How It Works

1.  The **Streamlit** frontend captures the user's message.
2.  It sends the entire conversation history to the **FastAPI** backend's `/api/chat` endpoint.
3.  The backend (currently) has placeholder logic to echo the message back. In a real application, this is where you would integrate a Large Language Model (LLM). You would:
    *   Load the system prompt from `prompt.md`.
    *   Combine the system prompt with the conversation history.
    *   Send the combined text to the LLM.
    *   Return the LLM's response to the frontend.
4.  The frontend displays the agent's response, and the conversation continues. 