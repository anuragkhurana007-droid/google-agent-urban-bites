# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.load_memory_tool import LoadMemoryTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "delhi" in query.lower() or "india" in query.lower():
        return "It's 85 degrees Fahrenheit and clear."
    return "It's 90 degrees Fahrenheit and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city/query to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "delhi" in query.lower() or "india" in query.lower():
        tz_identifier = "Asia/Kolkata"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from app.tools import (
    add_menu_item,
    calculate_recipe_margins,
    fetch_website_content,
    find_nearby_places,
    generate_item_image,
    generate_item_video,
    generate_marketing_image,
    generate_marketing_video,
    geocode_address,
    get_menu_items,
    search_recipe_inspiration,
    search_web,
)


def _get_code_executor() -> AgentEngineSandboxCodeExecutor | None:
    metadata_path = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path) as f:
                data = json.load(f)
                agent_engine_id = data.get("remote_agent_runtime_id")
                if agent_engine_id:
                    return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_id)
        except Exception as e:
            print(f"Notice: Failed to load sandbox code executor: {e}")
    return None


def _get_memory_service() -> VertexAiMemoryBankService | None:
    metadata_path = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path) as f:
                data = json.load(f)
                agent_engine_id = data.get("remote_agent_runtime_id", "").split("/")[-1]
                if agent_engine_id:
                    return VertexAiMemoryBankService(
                        project="qwiklabs-gcp-01-7a15d6c92f07",
                        location="us-central1",
                        agent_engine_id=agent_engine_id,
                    )
        except Exception as e:
            print(f"Notice: Failed to load memory service: {e}")
    return None


memory_service = _get_memory_service()



_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = _schema_manager.generate_system_prompt(
    role_description="You are Urban Bites Co's Chef Assistant AI, helping the head chef at Urban Bites Co in Valley View, SA manage burger recipes, menu items, costs, social media marketing images/videos, local geocoding & nearby supplier lookup, running sandboxed Python code, and restaurant operations. You have memory enabled: always remember and retrieve user dietary restrictions, preferences, and user allergies (such as peanuts, gluten, dairy, shellfish, etc.) across sessions, and ensure all recipe recommendations and menu suggestions strictly avoid any allergens stated by the user.",
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    after_model_callback=a2ui_callback,
    code_executor=_get_code_executor(),
    tools=[
        PreloadMemoryTool(),
        LoadMemoryTool(),
        get_menu_items,
        add_menu_item,
        calculate_recipe_margins,
        generate_item_image,
        generate_item_video,
        generate_marketing_image,
        generate_marketing_video,
        search_recipe_inspiration,
        search_web,
        fetch_website_content,
        geocode_address,
        find_nearby_places,
        get_weather,
        get_current_time,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)

