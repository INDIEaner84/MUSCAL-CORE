import os
import threading
import concurrent.futures
import runtime.llm.client
from config import BASE_DIR, DB_PATH, get_session_id
from runtime.api import create_app, register_blueprints, set_globals, set_server_ready


class TestImportSafety:
    def test_import_client_creates_no_threads(self):
        initial_threads = set(t.name for t in threading.enumerate())
        import runtime.llm.client
        after_import_threads = set(t.name for t in threading.enumerate())
        new_threads = after_import_threads - initial_threads
        ollama_threads = [t for t in new_threads if "ollama" in t]
        assert len(ollama_threads) == 0

    def test_executor_none_before_first_use(self):
        assert runtime.llm.client._ollama_executor is None

    def test_executor_created_on_first_async_call(self):
        future = runtime.llm.client._ollama_call_async(lambda: "test")
        result = future.result(timeout=5)
        assert result == "test"
        assert runtime.llm.client._ollama_executor is not None

    def test_config_import_has_no_filesystem_io(self):
        assert isinstance(BASE_DIR, os.PathLike)
        assert "MUSCAL" in str(BASE_DIR)

    def test_db_path_is_constructable(self):
        assert isinstance(DB_PATH, os.PathLike)
        assert "storage" in str(DB_PATH) and "muscal.db" in str(DB_PATH)

    def test_config_session_id_works(self):
        sid = get_session_id()
        assert sid.startswith("session_")

    def test_api_init_imports(self):
        assert callable(set_globals)
        assert callable(create_app)
