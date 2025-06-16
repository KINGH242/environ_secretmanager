from unittest.mock import MagicMock, patch

import pytest

from environ_secretmanager.env_secrets import EnvironSecretManager


@pytest.fixture
def esm():
    with patch(
        "environ_secretmanager.env_secrets.secretmanager.SecretManagerServiceClient"
    ):
        yield EnvironSecretManager(GOOGLE_CLOUD_PROJECT_ID="test-project")


def test_get_env_secret_from_env(monkeypatch, esm):
    monkeypatch.setenv("MY_SECRET", "env_value")
    assert esm.get_env_secret("MY_SECRET", "latest") == "env_value"


def test_get_env_secret_from_gsm(monkeypatch, esm):
    monkeypatch.delenv("MY_SECRET", raising=False)
    with patch.object(
        esm, "access_secret_version", return_value="gsm_value"
    ) as mock_access:
        assert esm.get_env_secret("MY_SECRET", "latest") == "gsm_value"
        mock_access.assert_called_once_with("MY_SECRET", "latest")


def test_access_secret_version_success(esm):
    mock_response = MagicMock()
    mock_response.payload.data.decode.return_value = "secret_data"
    esm.client.access_secret_version.return_value = mock_response
    result = esm.access_secret_version("secret_id", "1")
    assert result == "secret_data"
    esm.client.access_secret_version.assert_called_once()


def test_access_secret_version_exception(esm, caplog):
    esm.client.access_secret_version.side_effect = Exception("fail")
    with caplog.at_level("ERROR"):
        assert esm.access_secret_version("secret_id", "1") is None
        assert "fail" in caplog.text


def test_list_secrets(esm):
    mock_secret = MagicMock()
    mock_secret.name = "projects/test-project/secrets/secret1"
    esm.client.list_secrets.return_value = [mock_secret]
    secrets = esm.list_secrets()
    assert secrets == ["secret1"]


def test_write_env_file(tmp_path, esm):
    from unittest.mock import mock_open

    secrets = ["SECRET1", "SECRET2"]
    esm.access_secret_version = MagicMock(side_effect=["val1", "val2"])
    m = mock_open()
    with patch("builtins.open", m):
        esm.write_env_file(secrets)
    handle = m()
    written = "".join(call.args[0] for call in handle.write.call_args_list)
    assert "SECRET1='val1'" in written
    assert "SECRET2='val2'" in written


def test_create_dot_env_file(esm):
    esm.list_secrets = MagicMock(return_value=["A", "B"])
    esm.write_env_file = MagicMock()
    esm.create_dot_env_file()
    esm.write_env_file.assert_called_once_with(["A", "B"])
