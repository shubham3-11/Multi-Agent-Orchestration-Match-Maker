# filepath: adk_runner.py
import asyncio
import uuid
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agents import orchestrator

load_dotenv()

APP_NAME = "matchmaker_app"

_session_service = InMemorySessionService()
_runner = Runner(agent=orchestrator, session_service=_session_service, app_name=APP_NAME)

# cache user_id -> session_id
_session_ids: dict[str, str] = {}


def get_runner():
    return _runner


async def _async_get_session(user_id: str, session_id: str):
    return await _session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)


async def _async_create_session(user_id: str):
    new_id = str(uuid.uuid4())
    session = await _session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=new_id)
    # prime default state
    session.state.setdefault("user_profile", {"name": None, "age": None})
    session.state.setdefault("matches", [])
    session.state.setdefault("need_info", False)
    return session


def get_or_create_session(user_id: str):
    """Sync wrapper that returns a real Session (awaits internally)."""
    if user_id in _session_ids:
        sid = _session_ids[user_id]
        return asyncio.run(_async_get_session(user_id, sid))
    session = asyncio.run(_async_create_session(user_id))
    _session_ids[user_id] = session.id
    return session


async def _async_run_user_message(user_id: str, session_id: str, text: str):
    from google.genai import types
    content = types.Content(role="user", parts=[types.Part(text=text)])
    # ADK exposes an async stream
    async for event in _runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        yield event


def run_user_message(user_id: str, session_id: str, text: str):
    """Sync generator: collects async stream into a list so Streamlit can iterate easily."""
    async def _collect():
        items = []
        async for ev in _async_run_user_message(user_id, session_id, text):
            items.append(ev)
        return items
    return asyncio.run(_collect())


def get_session(user_id: str, session_id: str):
    """Sync wrapper to fetch the latest Session."""
    return asyncio.run(_async_get_session(user_id, session_id))
