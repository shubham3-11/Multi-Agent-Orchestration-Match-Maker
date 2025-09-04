# filepath: agents/orchestrator.py
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from agents.conversational_agent import conversational_agent
from agents.tools.memory_tools import store_profile, load_profile
from agents.tools.matching_tools import find_matches

orchestrator = LlmAgent(
    model="gemini-2.0-flash",
    name="orchestrator",
    description="Coordinator agent that orchestrates profile collection and match-finding.",
    instruction="""You are the coordinator agent for a matchmaking assistant. Decide which actions to take and which tool or agent to use.

Profile collection:
- If 'user_profile' is missing name or age, delegate to conversational_agent to ask ONLY for the missing fields.
- When the user provides new values, call store_profile(user_id, name, age). Use "" for unknown name and -1 for unknown age.
- After storing, update 'user_profile' in state and clear 'need_info' when both fields are present.

Match intent:
- If the user asks for matches and age is unknown, collect age first.
- If age is known, call find_matches(age), store results in 'matches', then delegate to conversational_agent to summarize.

General chat:
- Otherwise, delegate to conversational_agent for a normal response using any available profile context.

Tools:
- store_profile(user_id, name, age)  # pass "" or -1 for fields you are not updating
- load_profile(user_id)
- find_matches(current_age)
- conversational_agent (AgentTool) for all user-facing replies

Always speak to the user via conversational_agent; do not respond directly.""",
    tools=[
        store_profile,
        load_profile,
        find_matches,
        AgentTool(agent=conversational_agent, skip_summarization=True),
    ],
)
