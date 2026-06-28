import importlib

def test_ui_module_imports():
    mod = importlib.import_module("ui.streamlit_app")
    assert hasattr(mod, "api_url")
    assert mod.api_url("/health").endswith("/health")

def test_callout_helpers_exist():
    mod = importlib.import_module("ui.streamlit_app")
    for fn in ("banner", "exercise", "checkpoint", "watchout", "scaffold_link", "hint"):
        assert callable(getattr(mod, fn))

def test_tab_renderers_exist():
    mod = importlib.import_module("ui.streamlit_app")
    for fn in ("tab_overview", "tab_6a", "tab_6b", "tab_6c", "tab_6d", "tab_capstone"):
        assert callable(getattr(mod, fn))
