import assert from "node:assert/strict";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";

const projectRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const checker = join(
  projectRoot,
  ".agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs",
);
const fixtureMarker = ["SPEC", "SFY"].join("");
let invocation = 0;

function specText(id = "SPEC-0100", extraRequirement = false) {
  return `# Especificação de teste

| Campo | Valor |
| --- | --- |
| ID | ${id} |

#### US-001 — História

#### AC-001 — Aceite

- **FR-001**: Requisito.
${extraRequirement ? "- **FR-002**: Outro requisito.\n" : ""}
- **NFR-001**: Qualidade.
`;
}

async function fixture(spec, lines) {
  const root = await mkdtemp(join(tmpdir(), "specsfy-traceability-"));
  const specPath = join(root, "spec.md");
  const testsDirectory = join(root, "tests");
  await mkdir(testsDirectory);
  await writeFile(specPath, spec);
  await writeFile(join(testsDirectory, "contract.test.mjs"), `${lines.join("\n")}\n`);
  return { root, specPath };
}

async function runChecker(specPath, root, ...options) {
  const originalArgv = process.argv;
  const originalExitCode = process.exitCode;
  const originalLog = console.log;
  const originalError = console.error;
  const stdout = [];
  const stderr = [];
  process.argv = [process.execPath, checker, specPath, root, "--minimum-tests", "1", ...options];
  process.exitCode = undefined;
  console.log = (...items) => stdout.push(items.join(" "));
  console.error = (...items) => stderr.push(items.join(" "));
  try {
    invocation += 1;
    await import(`${pathToFileURL(checker).href}?test-run=${invocation}`);
    return {
      status: process.exitCode ?? 0,
      stdout: stdout.length ? `${stdout.join("\n")}\n` : "",
      stderr: stderr.length ? `${stderr.join("\n")}\n` : "",
    };
  } finally {
    process.argv = originalArgv;
    process.exitCode = originalExitCode;
    console.log = originalLog;
    console.error = originalError;
  }
}

async function withFixture(spec, lines, callback) {
  const created = await fixture(spec, lines);
  try {
    await callback(created);
  } finally {
    await rm(created.root, { recursive: true, force: true });
  }
}

test("SPECSFY: SPEC-0016 US-001 FR-001 FR-003 NFR-001 NFR-002 AC-001 isola o namespace alvo", async () => {
  await withFixture(
    specText(),
    [
      `// ${fixtureMarker}: SPEC-0100 US-001 FR-001 NFR-001 AC-001`,
      `// ${fixtureMarker}: SPEC-0200 US-999 FR-999 NFR-999 AC-999`,
    ],
    async ({ root, specPath }) => {
      const result = await runChecker(specPath, root, "--json");
      assert.equal(result.status, 0, result.stderr || result.stdout);
      const report = JSON.parse(result.stdout);
      assert.equal(report.spec_id, "SPEC-0100");
      assert.equal(report.marker_mode, "namespaced");
      assert.deepEqual(report.orphan_markers, []);
      assert.deepEqual(report.uncovered, []);
      assert.equal("US-999" in report.locations, false);
    },
  );
});

test("SPECSFY: SPEC-0016 US-001 FR-001 FR-002 NFR-001 NFR-002 AC-004 não mistura marcador legado", async () => {
  await withFixture(
    specText("SPEC-0100", true),
    [
      `// ${fixtureMarker}: SPEC-0100 US-001 FR-001 NFR-001 AC-001`,
      `// ${fixtureMarker}: FR-002`,
    ],
    async ({ root, specPath }) => {
      const result = await runChecker(specPath, root, "--json");
      assert.equal(result.status, 1);
      const report = JSON.parse(result.stdout);
      assert.equal(report.marker_mode, "namespaced");
      assert.deepEqual(report.uncovered, ["FR-002"]);
      assert.equal("FR-002" in report.locations, false);
    },
  );
});

test("SPECSFY: SPEC-0016 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-002 AC-002 preserva fallback legado", async () => {
  await withFixture(
    specText(),
    [`// ${fixtureMarker}: US-001 FR-001 NFR-001 AC-001 FR-999`],
    async ({ root, specPath }) => {
      const result = await runChecker(specPath, root, "--json");
      assert.equal(result.status, 0, result.stderr || result.stdout);
      const report = JSON.parse(result.stdout);
      assert.equal(report.marker_mode, "legacy");
      assert.deepEqual(report.uncovered, []);
      assert.deepEqual(report.orphan_markers, []);
      assert.deepEqual(report.legacy_orphan_warnings, ["FR-999"]);
    },
  );
});

test("SPECSFY: SPEC-0016 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-002 AC-003 mantém órfão alvo bloqueante", async () => {
  await withFixture(
    specText(),
    [`// ${fixtureMarker}: SPEC-0100 US-001 FR-001 NFR-001 AC-001 FR-999`],
    async ({ root, specPath }) => {
      const result = await runChecker(specPath, root, "--json");
      assert.equal(result.status, 1);
      const report = JSON.parse(result.stdout);
      assert.equal(report.marker_mode, "namespaced");
      assert.deepEqual(report.orphan_markers, ["FR-999"]);
      assert.deepEqual(report.legacy_orphan_warnings, []);
    },
  );
});

test("SPECSFY: SPEC-0016 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-002 AC-005 preserva contrato e informa modo humano", async () => {
  await withFixture(
    specText(),
    [`// ${fixtureMarker}: SPEC-0100 US-001 FR-001 NFR-001 AC-001`],
    async ({ root, specPath }) => {
      const result = await runChecker(specPath, root);
      assert.equal(result.status, 0, result.stderr || result.stdout);
      assert.match(result.stdout, /Namespace: SPEC-0100; modo: namespaced\./);
      assert.match(result.stdout, /Rastreabilidade: 4\/4 IDs cobertos/);
      assert.match(result.stdout, /RESULTADO: OK/);
    },
  );
});

test("SPECSFY: SPEC-0016 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-002 AC-005 rejeita spec sem ID válido", async () => {
  await withFixture(
    "# Spec sem metadado de identidade\n",
    [`// ${fixtureMarker}: SPEC-0100 US-001`],
    async ({ root, specPath }) => {
      const result = await runChecker(specPath, root);
      assert.equal(result.status, 2);
      assert.match(result.stderr, /ID.*SPEC-NNNN/i);
      assert.equal(result.stdout, "");
    },
  );
});
