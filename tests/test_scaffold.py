import os

def test_offline_env_is_hermetic():
    # conftest forces an offline, keyless environment regardless of any on-disk .env
    assert os.environ["DEFAULT_PROVIDER"] == "mock"
    assert os.environ["AZURE_OPENAI_API_KEY"] == ""
    assert os.environ["OPENAI_API_KEY"] == ""
