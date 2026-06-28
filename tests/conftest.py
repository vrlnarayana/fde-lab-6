"""Hermetic offline test env — set before api.config is imported.

pydantic-settings lets real env vars override .env; pytest imports conftest first,
so blanking keys + forcing mock here keeps the suite offline regardless of on-disk .env.
"""
import os

os.environ["DEFAULT_PROVIDER"] = "mock"
os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["AUTH_MODE"] = "key"
