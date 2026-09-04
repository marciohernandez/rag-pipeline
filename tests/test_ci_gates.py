import subprocess
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci.yml"
SPEC_PATH = next(
    (ROOT / "specs").glob("*/0007-ruff-e-esteira-de-integracao-continua/spec.md")
)
PREVIOUS_SPEC_PATH = (
    ROOT
    / "specs"
    / "completed"
    / "0006-gate-qualidade-chunks-metadados"
    / "spec.md"
)


def _pyproject() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)


def _run_ruff(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "ruff", "check", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _workflow_text() -> str:
    assert WORKFLOW_PATH.is_file(), ".github/workflows/ci.yml ainda não existe"
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _workflow() -> dict:
    return yaml.load(_workflow_text(), Loader=yaml.BaseLoader)


def _workflow_commands() -> list[str]:
    jobs = _workflow().get("jobs", {})
    return [
        step["run"]
        for job in jobs.values()
        for step in job.get("steps", [])
        if "run" in step
    ]


def _spec_text() -> str:
    return SPEC_PATH.read_text(encoding="utf-8")


def _manual_evidence_row(acceptance_id: str) -> str:
    rows = [
        line
        for line in _spec_text().splitlines()
        if f"| {acceptance_id} |" in line and "| Manual |" in line
    ]
    assert len(rows) == 1, f"linha manual única para {acceptance_id} não encontrada"
    return rows[0]


# SPECSFY: US-001 FR-001 NFR-003 AC-001
def test_ruff_is_a_pinned_development_dependency() -> None:
    dependencies = _pyproject()["dependency-groups"]["dev"]

    assert "ruff==0.16.5" in dependencies


# SPECSFY: US-001 FR-001 AC-002
def test_ruff_extends_the_default_rule_set() -> None:
    ruff = _pyproject()["tool"]["ruff"]
    lint = ruff["lint"]

    assert ruff.get("line-length") == 100
    assert lint.get("extend-select") == ["E501", "I", "UP", "B", "SIM"]
    assert "select" not in ruff
    assert ruff.get("extend-exclude") == [".agents"]


# SPECSFY: US-001 FR-002 AC-003
def test_ruff_check_runs_cleanly_over_the_repository() -> None:
    executed = _run_ruff()

    assert executed.returncode == 0, executed.stdout + executed.stderr


# SPECSFY: US-001 FR-002 AC-004
def test_ruff_reports_no_known_semantic_findings() -> None:
    executed = _run_ruff(
        "--select",
        "TRY004,PIE810,ISC004",
        "quality.py",
        "src/pipeline/quality.py",
    )

    assert executed.returncode == 0, executed.stdout + executed.stderr


# SPECSFY: US-001 FR-001 FR-002 AC-005
def test_ruff_line_length_passes_without_reducing_guard_scope() -> None:
    guard = (ROOT / "tests" / "test_client_neutrality.py").read_text(
        encoding="utf-8"
    )
    protected_tools = {"chat.py", "demo_rag.py", "search.py"}
    protected_terms = {
        "c6 bank",
        "c6 empresas",
        "rag c6",
        "conta pj",
        "cheque especial",
        "vivo fibra",
        "vivo gold",
        "vivo_gold",
    }
    executed = _run_ruff(
        "--select",
        "E501",
        "chat.py",
        "search.py",
        "src/pipeline/validation.py",
        "upsert_from_chunks.py",
        "tests/test_client_neutrality.py",
    )

    assert protected_tools <= {item for item in protected_tools if item in guard}
    assert protected_terms <= {item for item in protected_terms if item in guard.lower()}
    assert executed.returncode == 0, executed.stdout + executed.stderr


# SPECSFY: US-002 FR-003 AC-006
def test_ci_runs_on_push_for_phase_branches() -> None:
    triggers = _workflow().get("on", {})

    assert "push" in triggers


# SPECSFY: US-002 FR-003 AC-007
def test_ci_runs_on_pull_requests() -> None:
    triggers = _workflow().get("on", {})

    assert "pull_request" in triggers


# SPECSFY: US-002 FR-003 NFR-001 NFR-002 AC-008
def test_ci_uses_the_same_named_local_commands() -> None:
    commands = _workflow_commands()

    assert "uv run ruff check" in commands
    assert "uv run pytest" in commands


# SPECSFY: US-002 FR-003 NFR-002 AC-009
def test_ci_does_not_receive_project_secrets() -> None:
    workflow = _workflow_text().lower()
    forbidden = (
        "secrets.",
        "openai_api_key",
        "openrouter_api_key",
        "qdrant_api_key",
        "pinecone_api_key",
    )

    assert not any(item in workflow for item in forbidden)


# SPECSFY: US-003 FR-004 AC-010
def test_failed_required_check_has_manual_blocking_evidence() -> None:
    row = _manual_evidence_row("AC-010")

    assert "Pending" not in row
    assert "responsável:" in row.lower()
    assert "evidência:" in row.lower()


# SPECSFY: US-003 FR-004 AC-011
def test_successful_required_check_has_manual_release_evidence() -> None:
    row = _manual_evidence_row("AC-011")

    assert "Pending" not in row
    assert "responsável:" in row.lower()
    assert "evidência:" in row.lower()


# SPECSFY: US-003 FR-004 NFR-001 AC-012
def test_branch_protection_procedure_is_reproducible() -> None:
    documentation = (ROOT / "docs" / "testing.md").read_text(encoding="utf-8").lower()
    required = (
        "proteção de branch",
        "verificação obrigatória",
        "pull request reprovado",
        "pull request aprovado",
    )

    assert all(item in documentation for item in required)


# SPECSFY: US-001 FR-001 NFR-003 AC-013
def test_ruff_pin_is_locked_at_the_measured_version() -> None:
    dependencies = _pyproject()["dependency-groups"]["dev"]
    lockfile = (ROOT / "uv.lock").read_text(encoding="utf-8")

    assert dependencies.count("ruff==0.16.5") == 1
    assert 'name = "ruff"' in lockfile
    assert 'version = "0.16.5"' in lockfile


# SPECSFY: US-002 FR-003 NFR-002 AC-014
def test_ci_commands_do_not_log_sensitive_configuration() -> None:
    workflow = _workflow_text().lower()
    forbidden = (
        "printenv",
        "set -x",
        "qdrant_url",
        "pinecone_host",
        "openai_api_key",
        "openrouter_api_key",
    )

    assert not any(item in workflow for item in forbidden)


# SPECSFY: US-001 FR-005 AC-015
def test_previous_spec_records_the_ruff_gap_as_closed() -> None:
    previous_spec = PREVIOUS_SPEC_PATH.read_text(encoding="utf-8")
    definition_of_done = previous_spec.split("### 18. Definition of Done", 1)[1]
    open_ruff_items = [
        line
        for line in definition_of_done.splitlines()
        if line.startswith("- [ ]") and "uv run ruff check" in line
    ]

    assert open_ruff_items == []
    assert "SPEC-0007" in definition_of_done


# SPECSFY: US-001 FR-005 NFR-001 AC-016
def test_testing_documentation_publishes_the_available_ruff_command() -> None:
    documentation = (ROOT / "docs" / "testing.md").read_text(encoding="utf-8")

    assert "uv run ruff check" in documentation
    assert "Ruff 0.16.5" in documentation
    assert "ainda não está instalado" not in documentation


# SPECSFY: US-001 FR-005 NFR-003 AC-017
def test_stack_records_pinned_ruff_and_github_actions() -> None:
    stack = (ROOT / ".specsfy" / "STACK.md").read_text(encoding="utf-8")

    assert "Ruff 0.16.5" in stack
    assert "GitHub Actions" in stack
    assert "Ruff efêmero" not in stack


# --- SPEC-0008: regressão da migração da fronteira interna ---

_BASELINE_DOCS = ("docs/architecture.md", "docs/testing.md")
_BASELINE_MINIMA = 238


# SPECSFY: US-002 FR-001 FR-005 FR-006 NFR-001 NFR-003 AC-012
def test_migration_baseline_and_boundary_modules_are_recorded() -> None:
    for nome in ("test_application_boundaries.py", "test_pipeline_service.py"):
        assert (ROOT / "tests" / nome).is_file(), f"módulo de regressão ausente: {nome}"

    textos = [
        (ROOT / doc).read_text(encoding="utf-8")
        for doc in _BASELINE_DOCS
        if (ROOT / doc).is_file()
    ]
    baseline_declarada = any(
        str(_BASELINE_MINIMA) in texto and "baseline" in texto.lower() for texto in textos
    )
    assert baseline_declarada, (
        "a baseline de regressão da migração precisa estar declarada em documentação "
        f"versionada ({', '.join(_BASELINE_DOCS)})"
    )


# --- SPEC-0009: regressão do isolamento da carga do .env ---

_SPEC0009_BASELINE = 255
_SPEC0009_DOCS = ("docs/architecture.md", "docs/testing.md")


# SPECSFY: US-002 US-003 FR-001 FR-006 NFR-001 NFR-003 AC-006
def test_env_bootstrap_module_and_regression_baseline_are_recorded() -> None:
    modulo = ROOT / "tests" / "test_env_bootstrap.py"
    assert modulo.is_file(), "tests/test_env_bootstrap.py ausente"
    fonte = modulo.read_text(encoding="utf-8")
    for helper in ("dotenv_violations_in_pipeline", "entrypoints_sem_load_env"):
        assert f"def {helper}(" in fonte, f"scanner de fronteira ausente: {helper}"

    textos = [
        (ROOT / doc).read_text(encoding="utf-8")
        for doc in _SPEC0009_DOCS
        if (ROOT / doc).is_file()
    ]
    baseline_declarada = any(
        str(_SPEC0009_BASELINE) in texto and "baseline" in texto.lower() for texto in textos
    )
    assert baseline_declarada, (
        "a baseline de regressão da SPEC-0009 precisa estar declarada em documentação "
        f"versionada ({', '.join(_SPEC0009_DOCS)})"
    )
