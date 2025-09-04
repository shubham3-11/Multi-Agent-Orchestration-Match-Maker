# Matchmaking Multi-Agent Demo (Google ADK + Gemini + Streamlit)

A  multi-agent system using **Google ADK**, **Gemini** (via `GOOGLE_API_KEY`), and a **Streamlit** UI that supports **multiple users**. The orchestrator coordinates a conversational LLM agent with two Python function tools: memory (profile store) and matching (age-based).

Demonstration Video Link https://www.youtube.com/watch?v=pnV6qbG0G24

## Directory Structure


<img width="506" height="504" alt="image" src="https://github.com/user-attachments/assets/b685da33-169f-4f1e-9db9-728a4716e6ac" />



## Features
- **Orchestrator (LLM)**: Coordinator/dispatcher deciding when to ask for profile info, store it, find matches, and delegate to the conversational agent.

- **Conversational Agent (LLM)**: Friendly chat, personalized by name/age; summarizes matches.

- **Memory Tool (Function Tool)**: `store_profile`, `load_profile` storing name/age per user.

- **Matching Tool (Function Tool)**: `find_matches(age)` returns static profiles of the same age.

- **Streamlit UI**: Left pane has profile inputs and chat; right pane shows match results; bottom expander shows a debug log of internal events.

## Setup

1)Virtual environment

    python -m venv .venv

    source venv/bin/activate 

2)Install dependencies

    pip install -r requirements.txt

3) Set GOOGLE_API_KEY  in your .env  

4)Run the app

    streamlit run app.py
