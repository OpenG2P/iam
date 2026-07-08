import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_main_module_exposes_app_and_initializer():
    mock_initializer = MagicMock()
    mock_app = MagicMock()
    mock_initializer.return_app.return_value = mock_app

    with (
        patch("iam_staff_portal_api.app.Initializer", return_value=mock_initializer),
        patch("openg2p_fastapi_common.ping.PingInitializer"),
    ):
        import importlib
        import iam_staff_portal_api.main as main_module

        importlib.reload(main_module)

    assert main_module.initializer is mock_initializer
    assert main_module.app is mock_app


def test_main_script_entrypoint_calls_initializer_main():
    main_path = Path(__file__).resolve().parents[1] / "src/iam_staff_portal_api/main.py"
    mock_initializer = MagicMock()
    mock_initializer.return_app.return_value = MagicMock()

    with (
        patch("iam_staff_portal_api.app.Initializer", return_value=mock_initializer),
        patch("openg2p_fastapi_common.ping.PingInitializer"),
    ):
        runpy.run_path(str(main_path), run_name="__main__")

    mock_initializer.main.assert_called_once()
