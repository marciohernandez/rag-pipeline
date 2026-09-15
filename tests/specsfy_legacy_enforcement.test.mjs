import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const projectRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const evidenceChecker = join(
  projectRoot,
  ".agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs",
);
const researchLoader = join(
  projectRoot,
  ".agents/skills/specsfy-03-specify/scripts/load_research.mjs",
);
const traceabilityChecker = join(
  projectRoot,
  ".agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs",
);
const markerToken = ["SPEC", "SFY"].join("");

function run(command, args, cwd) {
  return spawnSync(command, args, { cwd, encoding: "utf8" });
}

function runNode(script, args, cwd) {
  return run(process.execPath, [script, ...args], cwd);
}

function jsonResult(result) {
  assert.notEqual(result.stdout, "", result.stderr);
  return JSON.parse(result.stdout);
}

async function withTemp(prefix, callback) {
  const root = await mkdtemp(join(tmpdir(), prefix));
  try {
    await callback(root);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

function git(root, ...args) {
  const result = run("git", args, root);
  assert.equal(result.status, 0, result.stderr || result.stdout);
}

async function historicalEvidenceFixture(root, status) {
  await mkdir(join(root, "src"), { recursive: true });
  await writeFile(join(root, "src", "old.js"), "export const value = 1;\n");
  git(root, "init");
  git(root, "config", "user.email", "specsfy@example.invalid");
  git(root, "config", "user.name", "Specsfy Test");
  git(root, "add", "src/old.js");
  git(root, "commit", "-m", "add historical file");
  await mkdir(join(root, "src", "current"), { recursive: true });
  await rename(join(root, "src", "old.js"), join(root, "src", "current", "new.js"));
  git(root, "add", "-A");
  git(root, "commit", "-m", "move historical file");

  const spec = join(root, "spec.md");
  await writeFile(spec, `# Spec fixture

| Campo | Valor |
| --- | --- |
| ID | SPEC-0900 |
| Status | ${status} |
| Evidence Contract | 1 |

#### US-001 — História
#### AC-001 — Aceite
- **FR-001**: Requisito.
- **NFR-001**: Qualidade.

- [x] T004 [CODE] [US-001] Implementar fixture — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
  <!-- specsfy:evidence {"task":"T004","refs":["US-001","FR-001","NFR-001","AC-001"],"files":["src/old.js"],"commands":[{"run":"node --test","exit":0}]} -->
`);
  return spec;
}

function traceabilitySpec(id) {
  return `# Spec fixture

| Campo | Valor |
| --- | --- |
| ID | ${id} |

#### US-001 — História
#### AC-001 — Aceite
- **FR-001**: Requisito.
- **NFR-001**: Qualidade.

- [x] T001 [TEST] [US-001] Testar — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
`;
}

test("SPECSFY: SPEC-0017 US-001 FR-001 FR-003 NFR-001 NFR-002 AC-001 aceita arquivo histórico comprovado somente em spec concluída", async () => {
  await withTemp("specsfy-evidence-complete-", async (root) => {
    const spec = await historicalEvidenceFixture(root, "Complete");
    const result = runNode(evidenceChecker, [spec, root, "--json"], root);
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const report = jsonResult(result);
    assert.equal(report.result, "passed");
    assert.deepEqual(report.historical_files, ["src/old.js"]);

    await writeFile(spec, (await readFile(spec, "utf8")).replace("src/old.js", "../outside.js"));
    const unsafe = runNode(evidenceChecker, [spec, root, "--json"], root);
    assert.equal(unsafe.status, 1, unsafe.stderr || unsafe.stdout);
    assert.match(jsonResult(unsafe).errors.join("\n"), /arquivo inexistente ou inseguro/);
  });
});

test("SPECSFY: SPEC-0017 US-001 FR-001 FR-003 NFR-001 AC-002 mantém spec ativa estrita mesmo quando o Git conhece o path", async () => {
  await withTemp("specsfy-evidence-active-", async (root) => {
    const spec = await historicalEvidenceFixture(root, "Implementing");
    const result = runNode(evidenceChecker, [spec, root, "--json"], root);
    assert.equal(result.status, 1, result.stderr || result.stdout);
    const report = jsonResult(result);
    assert.match(report.errors.join("\n"), /arquivo inexistente ou inseguro: src\/old\.js/);
    assert.deepEqual(report.historical_files ?? [], []);
  });
});

test("SPECSFY: SPEC-0017 US-001 FR-002 FR-003 NFR-002 AC-003 aceita research vazio sem claim formal nem índice", async () => {
  await withTemp("specsfy-research-empty-", async (root) => {
    const directory = join(root, "specs", "defined", "0100-empty");
    await mkdir(directory, { recursive: true });
    const spec = join(directory, "spec.md");
    await writeFile(spec, `# Spec fixture

#### Researchs executados

- **R-001**: Nenhuma fonte externa foi necessária.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.
`);
    const result = runNode(researchLoader, [spec, "--json"], root);
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const report = jsonResult(result);
    assert.equal(report.result, "passed");
    assert.deepEqual(report.artifacts, []);
    assert.deepEqual(report.claims, []);
  });
});

test("SPECSFY: SPEC-0017 US-001 FR-002 NFR-001 NFR-002 AC-004 remapeia research de estado antigo apenas para a mesma spec", async () => {
  await withTemp("specsfy-research-relocated-", async (root) => {
    const slug = "0100-relocated";
    const directory = join(root, "specs", "completed", slug);
    await mkdir(join(directory, "research"), { recursive: true });
    await writeFile(join(directory, "research", "note.md"), "# Evidence\n");
    const spec = join(directory, "spec.md");
    await writeFile(spec, `# Spec fixture

#### Researchs executados

- **R-001**: Pesquisa local não formal.

#### Artefatos de pesquisa armazenados

- \`specs/review/${slug}/research/note.md\`: fonte local.
`);
    const result = runNode(researchLoader, [spec, "--json"], root);
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const report = jsonResult(result);
    assert.deepEqual(report.artifacts.map((item) => item.path), [
      `specs/completed/${slug}/research/note.md`,
    ]);

    await writeFile(
      spec,
      (await readFile(spec, "utf8")).replace(slug, "0101-other-spec"),
    );
    const crossSpec = runNode(researchLoader, [spec, "--json"], root);
    assert.equal(crossSpec.status, 1, crossSpec.stderr || crossSpec.stdout);
    assert.match(jsonResult(crossSpec).errors.join("\n"), /caminho inseguro ou symlink/);
  });
});

test("SPECSFY: SPEC-0017 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-002 AC-005 aceita full-chain legado sem evidence por ID", async () => {
  await withTemp("specsfy-chain-legacy-", async (root) => {
    const spec = join(root, "spec.md");
    await writeFile(spec, traceabilitySpec("SPEC-0901"));
    await mkdir(join(root, "tests"));
    await writeFile(
      join(root, "tests", "contract.test.mjs"),
      `// ${markerToken}: US-001 FR-001 NFR-001 AC-001\n`,
    );
    const result = runNode(traceabilityChecker, [
      spec,
      root,
      "--minimum-tests",
      "1",
      "--full-chain",
      "--json",
    ], root);
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const report = jsonResult(result);
    assert.equal(report.marker_mode, "legacy");
    assert.deepEqual(report.broken_chains, []);
  });
});

test("SPECSFY: SPEC-0017 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-002 AC-005 mantém evidence por ID obrigatória no full-chain namespaced", async () => {
  await withTemp("specsfy-chain-namespaced-", async (root) => {
    const spec = join(root, "spec.md");
    await writeFile(spec, traceabilitySpec("SPEC-0902"));
    await mkdir(join(root, "tests"));
    await writeFile(
      join(root, "tests", "contract.test.mjs"),
      `// ${markerToken}: SPEC-0902 US-001 FR-001 NFR-001 AC-001\n`,
    );
    const result = runNode(traceabilityChecker, [
      spec,
      root,
      "--minimum-tests",
      "1",
      "--full-chain",
      "--json",
    ], root);
    assert.equal(result.status, 1, result.stderr || result.stdout);
    const report = jsonResult(result);
    assert.equal(report.marker_mode, "namespaced");
    assert.ok(report.broken_chains.every((item) => item.missing.includes("evidence")));
  });
});
