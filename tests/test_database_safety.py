"""Regressões da pré-condição que protege o banco durante a T017."""

import pytest

from tests._database_safety import configure_testing_environment, database_identity

TEST_URL = "postgresql+psycopg://test:secret@localhost:55432/rag_pipeline_test"


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    (tmp_path / ".env.testing").write_text(f"APP_ENV=testing\nAPP_DATABASE_URL={TEST_URL}\n")
    return tmp_path


def test_destino_explicito_separado_e_aceito(environment):
    """SPECSFY: SPEC-0022 US-001 FR-002 AC-002"""
    assert configure_testing_environment(environment) == TEST_URL


def test_credencial_e_driver_nao_mascaram_mesmo_banco(environment):
    """SPECSFY: SPEC-0022 US-001 FR-002 AC-002"""
    (environment / ".env").write_text(
        "APP_DATABASE_URL=postgresql://another:password@127.0.0.1:55432/rag_pipeline_test\n"
    )
    with pytest.raises(RuntimeError, match="coincide"):
        configure_testing_environment(environment)


def test_destino_herdado_divergente_e_recusado(environment, monkeypatch):
    """SPECSFY: SPEC-0022 US-001 FR-002 AC-002"""
    monkeypatch.setenv("APP_DATABASE_URL", "postgresql://dev:secret@localhost:5432/rag_pipeline")
    with pytest.raises(RuntimeError, match="herdada diverge"):
        configure_testing_environment(environment)


def test_arquivo_de_teste_ausente_e_recusado(tmp_path):
    with pytest.raises(RuntimeError, match="Crie .env.testing"):
        configure_testing_environment(tmp_path)


def test_exemplo_substitui_arquivo_ausente_somente_no_github_actions(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    (tmp_path / ".env.testing.example").write_text(
        f"APP_ENV=testing\nAPP_DATABASE_URL={TEST_URL}\n"
    )
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(RuntimeError, match="Crie .env.testing"):
        configure_testing_environment(tmp_path)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert configure_testing_environment(tmp_path) == TEST_URL


def test_exemplo_no_github_actions_ainda_recusa_destino_de_desenvolvimento(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    (tmp_path / ".env.testing.example").write_text(
        f"APP_ENV=testing\nAPP_DATABASE_URL={TEST_URL}\n"
    )
    (tmp_path / ".env").write_text(f"APP_DATABASE_URL={TEST_URL}\n")
    with pytest.raises(RuntimeError, match="coincide"):
        configure_testing_environment(tmp_path)


def test_app_env_diferente_de_testing_e_recusado(environment):
    (environment / ".env.testing").write_text(f"APP_ENV=development\nAPP_DATABASE_URL={TEST_URL}\n")
    with pytest.raises(RuntimeError, match="APP_ENV=testing"):
        configure_testing_environment(environment)


def test_url_sem_destino_e_recusada():
    with pytest.raises(RuntimeError, match="inválido"):
        database_identity("postgresql://")
