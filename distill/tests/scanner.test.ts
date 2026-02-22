import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { scanEnvironment } from "../src/scanner/index.ts";

describe("scanEnvironment", () => {
  let tmpDir: string;

  before(() => {
    tmpDir = mkdtempSync(join(tmpdir(), "distill-scanner-test-"));
  });

  after(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  // Note: scanEnvironment always reads global ~/.claude/ too.
  // Tests for project-scope items check that project items are INCLUDED
  // rather than asserting exact total counts.

  it("returns valid inventory when project .claude/ does not exist", () => {
    const result = scanEnvironment(join(tmpDir, "nonexistent"));
    // Should not throw — may include global rules
    assert.ok(Array.isArray(result.rules));
    assert.ok(Array.isArray(result.skills));
    assert.ok(Array.isArray(result.agents));
    assert.ok(typeof result.summary.totalRules === "number");
    assert.ok(typeof result.summary.estimatedTokens === "number");
  });

  it("reads distill-prefixed rules with origin 'distill'", () => {
    const projectDir = join(tmpDir, "project-distill-rules");
    const rulesDir = join(projectDir, ".claude", "rules");
    mkdirSync(rulesDir, { recursive: true });
    writeFileSync(join(rulesDir, "distill-typescript.md"), "- Use strict mode");

    const result = scanEnvironment(projectDir);
    const match = result.rules.find((r) => r.name === "distill-typescript.md");
    assert.ok(match, "Should find distill-typescript.md");
    assert.equal(match.origin, "distill");
    assert.equal(match.type, "rule");
    assert.ok(match.content.includes("Use strict mode"));
    assert.ok(result.summary.distillRules >= 1);
  });

  it("reads non-distill rules with origin 'user'", () => {
    const projectDir = join(tmpDir, "project-user-rules");
    const rulesDir = join(projectDir, ".claude", "rules");
    mkdirSync(rulesDir, { recursive: true });
    writeFileSync(join(rulesDir, "contribution.md"), "# Contribution\n- Use conventional commits");

    const result = scanEnvironment(projectDir);
    const match = result.rules.find((r) => r.name === "contribution.md");
    assert.ok(match, "Should find contribution.md");
    assert.equal(match.origin, "user");
    assert.ok(result.summary.userRules >= 1);
  });

  it("reads both distill and user rules from same project", () => {
    const projectDir = join(tmpDir, "project-mixed-rules");
    const rulesDir = join(projectDir, ".claude", "rules");
    mkdirSync(rulesDir, { recursive: true });
    writeFileSync(join(rulesDir, "distill-style.md"), "- Use semicolons");
    writeFileSync(join(rulesDir, "contribution.md"), "- Use conventional commits");

    const result = scanEnvironment(projectDir);
    const distill = result.rules.find((r) => r.name === "distill-style.md");
    const user = result.rules.find((r) => r.name === "contribution.md");
    assert.ok(distill, "Should find distill-style.md");
    assert.ok(user, "Should find contribution.md");
    assert.equal(distill.origin, "distill");
    assert.equal(user.origin, "user");
    assert.ok(result.summary.totalRules >= 2);
  });

  it("ignores non-md files in rules directory", () => {
    const projectDir = join(tmpDir, "project-non-md");
    const rulesDir = join(projectDir, ".claude", "rules");
    mkdirSync(rulesDir, { recursive: true });
    writeFileSync(join(rulesDir, "distill-style.md"), "- rule content");
    writeFileSync(join(rulesDir, "notes.txt"), "not a rule");
    writeFileSync(join(rulesDir, "data.json"), "{}");

    const result = scanEnvironment(projectDir);
    const projectRules = result.rules.filter((r) => r.path.startsWith(projectDir));
    assert.equal(projectRules.length, 1);
    assert.equal(projectRules[0].name, "distill-style.md");
  });

  it("reads skill directories with SKILL.md", () => {
    const projectDir = join(tmpDir, "project-skills");
    const skillDir = join(projectDir, ".claude", "skills", "deploy-prod");
    mkdirSync(skillDir, { recursive: true });
    writeFileSync(join(skillDir, "SKILL.md"), "# Deploy to Production");

    const result = scanEnvironment(projectDir);
    const match = result.skills.find((s) => s.name === "deploy-prod");
    assert.ok(match, "Should find deploy-prod skill");
    assert.equal(match.origin, "user");
    assert.equal(match.type, "skill");
    assert.ok(match.content.includes("Deploy to Production"));
  });

  it("classifies distill-prefixed skills as 'distill' origin", () => {
    const projectDir = join(tmpDir, "project-distill-skills");
    const skillDir = join(projectDir, ".claude", "skills", "distill-build");
    mkdirSync(skillDir, { recursive: true });
    writeFileSync(join(skillDir, "SKILL.md"), "# Build procedure");

    const result = scanEnvironment(projectDir);
    const match = result.skills.find((s) => s.name === "distill-build");
    assert.ok(match, "Should find distill-build skill");
    assert.equal(match.origin, "distill");
    assert.ok(result.summary.distillSkills >= 1);
  });

  it("skips skill directories without SKILL.md", () => {
    const projectDir = join(tmpDir, "project-no-skill-md");
    const skillDir = join(projectDir, ".claude", "skills", "incomplete");
    mkdirSync(skillDir, { recursive: true });
    writeFileSync(join(skillDir, "README.md"), "not a skill file");

    const result = scanEnvironment(projectDir);
    const match = result.skills.find((s) => s.name === "incomplete");
    assert.equal(match, undefined, "Should not find incomplete skill");
  });

  it("reads agent YAML files with origin 'user'", () => {
    const projectDir = join(tmpDir, "project-agents");
    const agentsDir = join(projectDir, ".claude", "agents");
    mkdirSync(agentsDir, { recursive: true });
    writeFileSync(join(agentsDir, "reviewer.yaml"), "name: reviewer");

    const result = scanEnvironment(projectDir);
    const match = result.agents.find((a) => a.name === "reviewer.yaml");
    assert.ok(match, "Should find reviewer.yaml agent");
    assert.equal(match.origin, "user");
    assert.equal(match.type, "agent");
    assert.ok(result.summary.totalAgents >= 1);
  });

  it("reads .yml agent files too", () => {
    const projectDir = join(tmpDir, "project-yml-agents");
    const agentsDir = join(projectDir, ".claude", "agents");
    mkdirSync(agentsDir, { recursive: true });
    writeFileSync(join(agentsDir, "builder.yml"), "name: builder");

    const result = scanEnvironment(projectDir);
    const match = result.agents.find((a) => a.name === "builder.yml");
    assert.ok(match, "Should find builder.yml agent");
  });

  it("computes estimatedTokens including project content", () => {
    const projectDir = join(tmpDir, "project-tokens");
    const rulesDir = join(projectDir, ".claude", "rules");
    mkdirSync(rulesDir, { recursive: true });
    const content = "x".repeat(100);
    writeFileSync(join(rulesDir, "distill-test.md"), content);

    const result = scanEnvironment(projectDir);
    // Token estimate should be at least ceil(100/4) = 25 for project content
    assert.ok(result.summary.estimatedTokens >= 25);
  });

  it("handles null projectRoot gracefully", () => {
    const result = scanEnvironment(null);
    assert.ok(Array.isArray(result.rules));
    assert.ok(Array.isArray(result.skills));
    assert.ok(Array.isArray(result.agents));
  });

  it("includes absolute path for each item", () => {
    const projectDir = join(tmpDir, "project-paths");
    const rulesDir = join(projectDir, ".claude", "rules");
    mkdirSync(rulesDir, { recursive: true });
    writeFileSync(join(rulesDir, "distill-paths.md"), "content");

    const result = scanEnvironment(projectDir);
    const match = result.rules.find((r) => r.name === "distill-paths.md");
    assert.ok(match);
    assert.ok(match.path.startsWith("/"), "Path should be absolute");
    assert.ok(match.path.endsWith("distill-paths.md"));
  });
});
