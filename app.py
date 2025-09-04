import streamlit as st
from uuid import uuid4

from adk_runner import get_or_create_session, run_user_message, get_session

# Streamlit recommends calling set_page_config first.
st.set_page_config(page_title="Matchmaker using MultiAgent orchestration", layout="wide")

# Initialize session state for multi-user support
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid4())
    st.session_state["session_id"] = None
    st.session_state["chat"] = []
    st.session_state["debug_log"] = []
    st.session_state["profile_synced"] = False
    st.session_state["matches"] = []
    st.session_state["name"] = ""          
    st.session_state["age"] = None          
    st.session_state["apply_ui_profile"] = False  
    # widget state defaults
    st.session_state["name_input"] = ""
    st.session_state["age_input"] = 0

# Before rendering widgets, optionally mirror canonical profile into widget state
if st.session_state.get("apply_ui_profile", False):
    st.session_state["name_input"] = st.session_state["name"] or ""
    st.session_state["age_input"] = int(st.session_state["age"]) if st.session_state["age"] is not None else 0
    st.session_state["apply_ui_profile"] = False

# Two-column layout: left = chat & inputs, right = match results
left, right = st.columns([2, 1])

with left:
    # Profile input fields (widgets use *_input keys)
    st.text_input("Name", key="name_input")
    # IMPORTANT: do not pass a `value=` when you also use a key; it causes the yellow warning
    st.number_input("Age", min_value=0, step=1, format="%d", help="Optional", key="age_input")

    # Update canonical values from widgets
    st.session_state["name"] = st.session_state.get("name_input", "") or ""
    st.session_state["age"] = None if st.session_state.get("age_input", 0) == 0 else int(st.session_state["age_input"])

    # Display existing chat messages
    for role, message in st.session_state["chat"]:
        st.chat_message(role).markdown(message)

    # Chat input box for new user message
    prompt = st.chat_input("Type a message…")

    if prompt:
        # Add user message to chat history
        st.session_state["chat"].append(("user", prompt))

        # Ensure ADK session exists for this user
        session = get_or_create_session(st.session_state["user_id"])
        st.session_state["session_id"] = session.id

        # If profile inputs were provided before chat and not synced yet, sync them ONCE
        if (
            not st.session_state["profile_synced"]
            and (st.session_state["name"] or st.session_state["age"] is not None)
        ):
            # Deterministic sync sentence so the orchestrator calls store_profile immediately
            sync_bits = []
            if st.session_state["name"]:
                sync_bits.append(f"my name is {st.session_state['name']}")
            if st.session_state["age"] is not None:
                sync_bits.append(f"my age is {int(st.session_state['age'])}")
            sync_prompt = (
                "Please sync my profile: " + ", ".join(sync_bits)
                if sync_bits
                else "Please sync my profile."
            )

            sync_events = run_user_message(st.session_state["user_id"], session.id, sync_prompt)
            for event in sync_events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if getattr(part, "function_call", None):
                            fc = part.function_call
                            args = fc.args or {}
                            st.session_state["debug_log"].append(f"Called tool {fc.name}({args})")
                        if getattr(part, "function_response", None):
                            fr = part.function_response
                            resp = fr.response or {}
                            st.session_state["debug_log"].append(f"Tool result: {resp}")
                            if "stored_profile" in resp:
                                current_session = get_session(st.session_state["user_id"], session.id)
                                current_session.state["user_profile"] = resp["stored_profile"]
                                # Update canonical profile
                                if resp["stored_profile"].get("name"):
                                    st.session_state["name"] = resp["stored_profile"]["name"]
                                if resp["stored_profile"].get("age") is not None:
                                    st.session_state["age"] = resp["stored_profile"]["age"]
                                st.session_state["profile_synced"] = True
                                # Ask to mirror into widgets on a later run (no rerun now)
                                st.session_state["apply_ui_profile"] = True
                if getattr(event, "actions", None) and getattr(event.actions, "state_delta", None):
                    st.session_state["debug_log"].append(
                        f"State change: {event.actions.state_delta}"
                    )
            

        # Now run the user's actual message in the same run
        try:
            events = run_user_message(st.session_state["user_id"], session.id, prompt)
        except Exception as e:
            st.session_state["debug_log"].append(f"Runner error: {e!r}")
            st.error("The agent runner encountered an error. Check Debug Log.")
            events = []

        assistant_placeholder = None
        assistant_content = ""

        for event in events:
            if event.content:
                parts = event.content.parts or []
                for part in parts:
                    # 1) Normal text tokens
                    if getattr(part, "text", None):
                        if assistant_placeholder is None:
                            assistant_placeholder = st.chat_message("assistant")
                        assistant_content += part.text

                    # 2) Tool calls (for Debug Log only)
                    if getattr(part, "function_call", None):
                        fc = part.function_call
                        args = fc.args or {}
                        st.session_state["debug_log"].append(f"Called tool {fc.name}({args})")

                    # 3) Tool responses
                    if getattr(part, "function_response", None):
                        fr = part.function_response
                        resp = fr.response or {}
                        st.session_state["debug_log"].append(f"Tool result: {resp}")

                        # If the conversational_agent (AgentTool) responded, its text is in resp["result"]
                        if getattr(fr, "name", "") == "conversational_agent":
                            result_text = resp.get("result")
                            if result_text:
                                # Skip stale “need age” prompts if age is already present
                                if (
                                    st.session_state.get("age") is not None
                                    and "need to know your age" in str(result_text).lower()
                                ):
                                    st.session_state["debug_log"].append("Skipped stale age prompt from agent.")
                                else:
                                    if assistant_placeholder is None:
                                        assistant_placeholder = st.chat_message("assistant")
                                    assistant_content += (
                                        result_text if isinstance(result_text, str) else str(result_text)
                                    )

                        # If profile stored, update canonical state and mark synced
                        if "stored_profile" in resp:
                            current_session = get_session(st.session_state["user_id"], session.id)
                            current_session.state["user_profile"] = resp["stored_profile"]
                            if resp["stored_profile"].get("name"):
                                st.session_state["name"] = resp["stored_profile"]["name"]
                            if resp["stored_profile"].get("age") is not None:
                                st.session_state["age"] = resp["stored_profile"]["age"]
                            st.session_state["profile_synced"] = True
                            st.session_state["apply_ui_profile"] = True  # mirror into widgets next run

                        # If matches found, update right panel immediately and add a short note in chat
                        if "matches" in resp:
                            st.session_state["matches"] = resp["matches"]
                            try:
                                current_session = get_session(st.session_state["user_id"], session.id)
                                current_session.state["matches"] = resp["matches"]
                            except Exception as e:
                                st.session_state["debug_log"].append(f"mirror matches to ADK state failed: {e!r}")

                            names = ", ".join([m.get("name", "Unknown") for m in resp["matches"]]) or "no one"
                            if assistant_placeholder is None:
                                assistant_placeholder = st.chat_message("assistant")
                            assistant_content += f"\n\n(I also listed your matches on the right: {names}.)"

            if getattr(event, "actions", None) and getattr(event.actions, "state_delta", None):
                st.session_state["debug_log"].append(f"State change: {event.actions.state_delta}")

        # Render the accumulated assistant text once
        if assistant_placeholder:
            assistant_placeholder.markdown(assistant_content)
            st.session_state["chat"].append(("assistant", assistant_content))

        # Final confirm: mirror any updated profile/matches from ADK session (non-blocking)
        session = get_session(st.session_state["user_id"], session.id)
        if "user_profile" in session.state:
            profile = session.state["user_profile"]
            if profile.get("name"):
                st.session_state["name"] = profile["name"]
            if profile.get("age") is not None:
                st.session_state["age"] = profile["age"]
            if profile.get("name") and profile.get("age") is not None:
                session.state["need_info"] = False
        if "matches" in session.state:
            st.session_state["matches"] = session.state["matches"]

with right:
    st.subheader("Match Results")
    if st.session_state["matches"]:
        for match in st.session_state["matches"]:
            st.write(f"{match.get('name', 'Unknown')} - {match.get('age', '?')}")
    else:
        st.write("No matches yet.")

# Expandable debug log panel
with st.expander("Debug Log"):
    for log in st.session_state["debug_log"]:
        st.write(log)
