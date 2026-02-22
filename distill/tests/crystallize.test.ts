import { describe, it, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { parseCrystallizeResponse, crystallize } from "../src/extractor/crystallize.ts";
import { CRYSTALLIZE_SYSTEM_PROMPT } from "../src/extractor/prompts.ts";
import { createMockServer } from "./helpers/mock-server.ts";
import { makeKnowledgeChunk } from "./helpers/factories.ts";

describe("parseCrystallizeResponse", () => {
  it("parses valid create action", () => {
    const text = `[{
      "topic": "typescript-style",
      "action": "create",
      "delivery": "rule",
      "rules": ["Use strict mode", "Prefer named exports"],
      "source_ids": ["id1", "id2"]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].topic, "typescript-style");
    assert.equal(result[0].action, "create");
    assert.equal(result[0].delivery, "rule");
    assert.deepEqual(result[0].rules, ["Use strict mode", "Prefer named exports"]);
    assert.deepEqual(result[0].source_ids, ["id1", "id2"]);
  });

  it("parses all valid actions", () => {
    const actions = ["create", "update", "remove", "downgrade"];
    for (const action of actions) {
      const text = `[{"topic":"t","action":"${action}","delivery":"rule","rules":["r"],"source_ids":["s"]}]`;
      const result = parseCrystallizeResponse(text);
      assert.equal(result.length, 1, `action "${action}" should be accepted`);
    }
  });

  it("parses update with existing_file", () => {
    const text = `[{
      "topic": "error-handling",
      "action": "update",
      "delivery": "rule",
      "rules": ["Updated rule"],
      "source_ids": ["id3"],
      "existing_file": "distill-error-handling.md"
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].existing_file, "distill-error-handling.md");
  });

  it("parses multiple results", () => {
    const text = `[
      {"topic":"a","action":"create","delivery":"rule","rules":["r1"],"source_ids":["s1"]},
      {"topic":"b","action":"update","delivery":"rule","rules":["r2"],"source_ids":["s2"]},
      {"topic":"c","action":"remove","delivery":"rule","rules":[],"source_ids":["s3"]}
    ]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 3);
  });

  it("filters entries with invalid action", () => {
    const text = `[{"topic":"t","action":"invalid","rules":["r"],"source_ids":["s"]}]`;
    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 0);
  });

  it("filters entries missing topic", () => {
    const text = `[{"action":"create","rules":["r"],"source_ids":["s"]}]`;
    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 0);
  });

  it("filters entries with non-array rules", () => {
    const text = `[{"topic":"t","action":"create","rules":"not-array","source_ids":["s"]}]`;
    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 0);
  });

  it("filters entries with non-array source_ids", () => {
    const text = `[{"topic":"t","action":"create","rules":["r"],"source_ids":"not-array"}]`;
    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 0);
  });

  it("returns empty array when no JSON found", () => {
    const result = parseCrystallizeResponse("No patterns detected.");
    assert.equal(result.length, 0);
  });

  it("returns empty array for malformed JSON", () => {
    const result = parseCrystallizeResponse("[{bad}]");
    assert.equal(result.length, 0);
  });

  it("handles JSON embedded in surrounding text", () => {
    const text = `Here are the results:

[{"topic":"embedded","action":"create","delivery":"rule","rules":["found it"],"source_ids":["e1"]}]

That's all.`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].topic, "embedded");
  });

  // Phase 1.5: Graduation Logic Tests
  it("parses downgrade action", () => {
    const text = `[{
      "topic": "low-confidence",
      "action": "downgrade",
      "delivery": "store",
      "rules": ["Old rule"],
      "source_ids": ["id1"]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].action, "downgrade");
  });

  it("parses delivery field for rule", () => {
    const text = `[{
      "topic": "high-confidence",
      "action": "create",
      "delivery": "rule",
      "rules": ["Always use this"],
      "source_ids": ["id1"]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].delivery, "rule");
  });

  it("parses delivery field for skill with metadata", () => {
    const text = `[{
      "topic": "deploy-workflow",
      "action": "create",
      "delivery": "skill",
      "rules": ["Deployment procedure"],
      "source_ids": ["id1"],
      "skill_metadata": {
        "description": "Deploy app to production",
        "when_to_use": "When deploying",
        "procedure": ["Step 1", "Step 2"],
        "examples": ["deploy api"]
      }
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].delivery, "skill");
    assert.ok(result[0].skill_metadata);
    assert.equal(result[0].skill_metadata?.description, "Deploy app to production");
    assert.equal(result[0].skill_metadata?.when_to_use, "When deploying");
    assert.deepEqual(result[0].skill_metadata?.procedure, ["Step 1", "Step 2"]);
    assert.deepEqual(result[0].skill_metadata?.examples, ["deploy api"]);
  });

  it("parses delivery field for store", () => {
    const text = `[{
      "topic": "niche-case",
      "action": "create",
      "delivery": "store",
      "rules": ["Rarely used"],
      "source_ids": ["id1"]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].delivery, "store");
  });

  it("filters entries with invalid delivery", () => {
    const text = `[{
      "topic": "test",
      "action": "create",
      "delivery": "invalid",
      "rules": ["rule"],
      "source_ids": ["id1"]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 0);
  });

  it("filters skill delivery without skill_metadata", () => {
    const text = `[{
      "topic": "test",
      "action": "create",
      "delivery": "skill",
      "rules": ["rule"],
      "source_ids": ["id1"]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 0);
  });

  it("filters skill delivery with incomplete skill_metadata", () => {
    const text = `[{
      "topic": "test",
      "action": "create",
      "delivery": "skill",
      "rules": ["rule"],
      "source_ids": ["id1"],
      "skill_metadata": {
        "description": "Missing procedure and when_to_use"
      }
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 0);
  });

  it("accepts skill delivery without examples (optional)", () => {
    const text = `[{
      "topic": "test",
      "action": "create",
      "delivery": "skill",
      "rules": ["rule"],
      "source_ids": ["id1"],
      "skill_metadata": {
        "description": "Test skill",
        "when_to_use": "When testing",
        "procedure": ["Do this"]
      }
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.ok(result[0].skill_metadata);
    assert.equal(result[0].skill_metadata?.examples, undefined);
  });

  // Phase 2: User Conflict Tests
  it("parses user_conflicts field", () => {
    const text = `[{
      "topic": "style",
      "action": "create",
      "delivery": "rule",
      "rules": ["Use tabs"],
      "source_ids": ["id1"],
      "user_conflicts": [{
        "user_rule_file": "contribution.md",
        "conflicting_content": "Use spaces for indentation",
        "suggestion": "Consider aligning tab vs space preference"
      }]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.ok(result[0].user_conflicts);
    assert.equal(result[0].user_conflicts!.length, 1);
    assert.equal(result[0].user_conflicts![0].user_rule_file, "contribution.md");
    assert.equal(result[0].user_conflicts![0].conflicting_content, "Use spaces for indentation");
    assert.equal(result[0].user_conflicts![0].suggestion, "Consider aligning tab vs space preference");
  });

  it("returns undefined user_conflicts when field is absent", () => {
    const text = `[{
      "topic": "style",
      "action": "create",
      "delivery": "rule",
      "rules": ["Use tabs"],
      "source_ids": ["id1"]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].user_conflicts, undefined);
  });

  it("filters invalid user_conflicts entries", () => {
    const text = `[{
      "topic": "style",
      "action": "create",
      "delivery": "rule",
      "rules": ["Use tabs"],
      "source_ids": ["id1"],
      "user_conflicts": [
        {"user_rule_file": "valid.md", "conflicting_content": "content", "suggestion": "fix it"},
        {"user_rule_file": "missing-fields"},
        "not-an-object",
        null
      ]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result.length, 1);
    assert.equal(result[0].user_conflicts!.length, 1);
    assert.equal(result[0].user_conflicts![0].user_rule_file, "valid.md");
  });

  it("parses multiple user_conflicts", () => {
    const text = `[{
      "topic": "style",
      "action": "create",
      "delivery": "rule",
      "rules": ["Use tabs"],
      "source_ids": ["id1"],
      "user_conflicts": [
        {"user_rule_file": "a.md", "conflicting_content": "c1", "suggestion": "s1"},
        {"user_rule_file": "b.md", "conflicting_content": "c2", "suggestion": "s2"}
      ]
    }]`;

    const result = parseCrystallizeResponse(text);
    assert.equal(result[0].user_conflicts!.length, 2);
  });
});

describe("crystallize", () => {
  let tmpRoot: string;

  beforeEach(() => {
    tmpRoot = mkdtempSync(join(tmpdir(), "distill-cryst-"));
    mkdirSync(join(tmpRoot, ".claude", "rules"), { recursive: true });
  });

  afterEach(() => {
    rmSync(tmpRoot, { recursive: true, force: true });
  });

  const createResponse = JSON.stringify([
    {
      topic: "typescript-style",
      action: "create",
      delivery: "rule",
      rules: ["Use strict mode", "Prefer named exports"],
      source_ids: ["id1", "id2"],
    },
  ]);

  it("returns empty report for empty chunks", async () => {
    const { server, calls } = createMockServer();

    const report = await crystallize({
      server,
      chunks: [],
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.deepEqual(report, {
      created: [],
      updated: [],
      removed: [],
      downgraded: [],
      skills_created: [],
      user_conflicts: [],
      total_rules: 0,
    });
    assert.equal(calls.length, 0);
  });

  it("sends correct createMessage params", async () => {
    const { server, calls } = createMockServer({ response: createResponse });
    const chunks = [makeKnowledgeChunk({ id: "c1", content: "Test rule" })];

    await crystallize({
      server,
      chunks,
      model: "claude-sonnet-4-5-20250929",
      projectRoot: tmpRoot,
    });

    assert.equal(calls.length, 1);
    assert.equal(calls[0].systemPrompt, CRYSTALLIZE_SYSTEM_PROMPT);
    assert.deepEqual(calls[0].modelPreferences?.hints, [
      { name: "claude-sonnet-4-5-20250929" },
    ]);
    assert.equal(calls[0].modelPreferences?.intelligencePriority, 0.9);
    assert.equal(calls[0].maxTokens, 4096);
  });

  it("creates rule files for create action", async () => {
    const { server } = createMockServer({ response: createResponse });
    const chunks = [makeKnowledgeChunk({ id: "c1" })];

    const report = await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.deepEqual(report.created, ["distill-typescript-style.md"]);
    assert.equal(report.total_rules, 2);

    const filePath = join(tmpRoot, ".claude", "rules", "distill-typescript-style.md");
    assert.ok(existsSync(filePath));

    const content = readFileSync(filePath, "utf-8");
    assert.ok(content.includes("# typescript-style"));
    assert.ok(content.includes("Use strict mode"));
    assert.ok(content.includes("Prefer named exports"));
  });

  it("updates rule files for update action", async () => {
    // Pre-create existing rule file
    writeFileSync(
      join(tmpRoot, ".claude", "rules", "distill-style.md"),
      "# style\n- Old rule",
    );

    const updateResponse = JSON.stringify([
      {
        topic: "style",
        action: "update",
        delivery: "rule",
        rules: ["Updated rule"],
        source_ids: ["u1"],
        existing_file: "distill-style.md",
      },
    ]);

    const { server } = createMockServer({ response: updateResponse });
    const chunks = [makeKnowledgeChunk({ id: "u1" })];

    const report = await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.deepEqual(report.updated, ["distill-style.md"]);
    const content = readFileSync(
      join(tmpRoot, ".claude", "rules", "distill-style.md"),
      "utf-8",
    );
    assert.ok(content.includes("Updated rule"));
    assert.ok(!content.includes("Old rule"));
  });

  it("removes rule files for remove action", async () => {
    const filePath = join(tmpRoot, ".claude", "rules", "distill-obsolete.md");
    writeFileSync(filePath, "# obsolete\n- Old rule");
    assert.ok(existsSync(filePath));

    const removeResponse = JSON.stringify([
      {
        topic: "obsolete",
        action: "remove",
        delivery: "rule",
        rules: [],
        source_ids: ["r1"],
        existing_file: "distill-obsolete.md",
      },
    ]);

    const { server } = createMockServer({ response: removeResponse });
    const chunks = [makeKnowledgeChunk({ id: "r1" })];

    const report = await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.deepEqual(report.removed, ["distill-obsolete.md"]);
    assert.ok(!existsSync(filePath));
  });

  it("reports created/updated/removed correctly", async () => {
    writeFileSync(
      join(tmpRoot, ".claude", "rules", "distill-old.md"),
      "# old\n- Rule",
    );
    writeFileSync(
      join(tmpRoot, ".claude", "rules", "distill-dead.md"),
      "# dead\n- Rule",
    );

    const mixedResponse = JSON.stringify([
      { topic: "new-topic", action: "create", delivery: "rule", rules: ["New rule"], source_ids: ["n1"] },
      { topic: "old", action: "update", delivery: "rule", rules: ["Better rule"], source_ids: ["o1"], existing_file: "distill-old.md" },
      { topic: "dead", action: "remove", delivery: "rule", rules: [], source_ids: ["d1"], existing_file: "distill-dead.md" },
    ]);

    const { server } = createMockServer({ response: mixedResponse });
    const chunks = [makeKnowledgeChunk({ id: "n1" }), makeKnowledgeChunk({ id: "o1" }), makeKnowledgeChunk({ id: "d1" })];

    const report = await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.deepEqual(report.created, ["distill-new-topic.md"]);
    assert.deepEqual(report.updated, ["distill-old.md"]);
    assert.deepEqual(report.removed, ["distill-dead.md"]);
    assert.equal(report.total_rules, 2); // 1 from create + 1 from update
  });

  it("handles mixed actions in single response", async () => {
    const mixedResponse = JSON.stringify([
      { topic: "a", action: "create", delivery: "rule", rules: ["r1", "r2"], source_ids: ["s1"] },
      { topic: "b", action: "create", delivery: "rule", rules: ["r3"], source_ids: ["s2"] },
    ]);

    const { server } = createMockServer({ response: mixedResponse });
    const chunks = [makeKnowledgeChunk()];

    const report = await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.equal(report.created.length, 2);
    assert.equal(report.total_rules, 3);
  });

  it("uses project rules dir when projectRoot is set", async () => {
    const { server } = createMockServer({ response: createResponse });
    const chunks = [makeKnowledgeChunk()];

    await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    const filePath = join(tmpRoot, ".claude", "rules", "distill-typescript-style.md");
    assert.ok(existsSync(filePath));
  });

  it("reads existing rules into prompt", async () => {
    // Pre-create a distill rule file
    writeFileSync(
      join(tmpRoot, ".claude", "rules", "distill-existing.md"),
      "# existing\n- Pre-existing rule",
    );

    const { server, calls } = createMockServer({ response: "[]" });
    const chunks = [makeKnowledgeChunk()];

    await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    const promptText = calls[0].messages[0].content.text;
    assert.ok(promptText?.includes("Pre-existing rule"));
  });

  it("returns empty report when LLM returns no patterns", async () => {
    const { server } = createMockServer({ response: "[]" });
    const chunks = [makeKnowledgeChunk()];

    const report = await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.deepEqual(report, {
      created: [],
      updated: [],
      removed: [],
      downgraded: [],
      skills_created: [],
      user_conflicts: [],
      total_rules: 0,
    });
  });

  it("propagates non-sampling server errors", async () => {
    const { server } = createMockServer({
      error: new Error("network timeout"),
    });
    const chunks = [makeKnowledgeChunk()];

    await assert.rejects(
      () => crystallize({ server, chunks, model: "test-model", projectRoot: tmpRoot }),
      { message: "network timeout" },
    );
  });

  it("wraps sampling-not-supported error with user-friendly message", async () => {
    const { server } = createMockServer({
      error: new Error("Method not found: sampling/createMessage"),
    });
    const chunks = [makeKnowledgeChunk()];

    await assert.rejects(
      () => crystallize({ server, chunks, model: "test-model", projectRoot: tmpRoot }),
      (err: Error) => {
        assert.ok(err.message.includes("MCP Sampling is not supported"));
        return true;
      },
    );
  });

  it("collects user_conflicts in report", async () => {
    const responseWithConflicts = JSON.stringify([
      {
        topic: "indent-style",
        action: "create",
        delivery: "rule",
        rules: ["Use tabs for indentation"],
        source_ids: ["c1"],
        user_conflicts: [
          {
            user_rule_file: "contribution.md",
            conflicting_content: "Use 2-space indentation",
            suggestion: "Align indentation preference between user rules and learned patterns",
          },
        ],
      },
    ]);

    const { server } = createMockServer({ response: responseWithConflicts });
    const chunks = [makeKnowledgeChunk({ id: "c1" })];

    const report = await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.equal(report.user_conflicts.length, 1);
    assert.equal(report.user_conflicts[0].user_rule_file, "contribution.md");
    assert.equal(report.user_conflicts[0].conflicting_content, "Use 2-space indentation");
    assert.ok(report.created.includes("distill-indent-style.md"));
  });

  it("returns empty user_conflicts when LLM returns none", async () => {
    const { server } = createMockServer({ response: createResponse });
    const chunks = [makeKnowledgeChunk({ id: "c1" })];

    const report = await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    assert.deepEqual(report.user_conflicts, []);
  });

  it("includes user rules in prompt context", async () => {
    // Create a user rule file (non-distill prefix)
    writeFileSync(
      join(tmpRoot, ".claude", "rules", "contribution.md"),
      "# Contribution\n- Use conventional commits",
    );

    const { server, calls } = createMockServer({ response: "[]" });
    const chunks = [makeKnowledgeChunk()];

    await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    const promptText = calls[0].messages[0].content.text;
    assert.ok(promptText?.includes("User Rules"), "Should include User Rules section");
    assert.ok(promptText?.includes("contribution.md"), "Should include user rule filename");
    assert.ok(promptText?.includes("conventional commits"), "Should include user rule content");
  });

  it("rule file follows expected format", async () => {
    const { server } = createMockServer({ response: createResponse });
    const chunks = [makeKnowledgeChunk()];

    await crystallize({
      server,
      chunks,
      model: "test-model",
      projectRoot: tmpRoot,
    });

    const content = readFileSync(
      join(tmpRoot, ".claude", "rules", "distill-typescript-style.md"),
      "utf-8",
    );

    // Check format: # topic, > Auto-generated, bullet rules, ## Sources
    assert.ok(content.startsWith("# typescript-style\n"));
    assert.ok(content.includes("> Auto-generated by Distill"));
    assert.ok(content.includes("- Use strict mode"));
    assert.ok(content.includes("- Prefer named exports"));
    assert.ok(content.includes("## Sources"));
    assert.ok(content.includes("- id1"));
    assert.ok(content.includes("- id2"));
  });
});
