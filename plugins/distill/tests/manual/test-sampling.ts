#!/usr/bin/env node

/**
 * Manual MCP Sampling verification script.
 *
 * Registers a minimal MCP server with a single tool that tests
 * whether the client (Claude Code) supports MCP Sampling
 * (server.createMessage / sampling/createMessage).
 *
 * Usage:
 *   1. Register as MCP server:
 *      claude mcp add test-sampling -- node --import tsx/esm tests/manual/test-sampling.ts
 *
 *   2. In a Claude Code conversation, call the "test_sampling" tool.
 *
 *   3. Check the response:
 *      - "Sampling works! ..." → MCP Sampling is supported
 *      - "Sampling FAILED: ..." → MCP Sampling is NOT supported
 *
 *   4. Clean up:
 *      claude mcp remove test-sampling
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const mcpServer = new McpServer({
  name: "test-sampling",
  version: "0.1.0",
});

mcpServer.tool(
  "test_sampling",
  "Test if MCP Sampling (server.createMessage) works with this client",
  {},
  async () => {
    const rawServer = mcpServer.server;

    try {
      const result = await rawServer.createMessage({
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: "Reply with exactly: SAMPLING_OK",
            },
          },
        ],
        systemPrompt:
          "You are a test helper. Reply with exactly the text requested, nothing else.",
        modelPreferences: {
          hints: [{ name: "claude-haiku-4-5-20251001" }],
          costPriority: 1.0,
          speedPriority: 1.0,
          intelligencePriority: 0.0,
        },
        maxTokens: 50,
      });

      const text =
        result.content.type === "text" ? result.content.text : "NO_TEXT_CONTENT";

      return {
        content: [
          {
            type: "text" as const,
            text: [
              `Sampling works!`,
              `Response: ${text}`,
              `Model: ${result.model}`,
              `Stop reason: ${result.stopReason}`,
            ].join("\n"),
          },
        ],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        content: [
          {
            type: "text" as const,
            text: [
              `Sampling FAILED.`,
              `Error: ${message}`,
              ``,
              `This means the client does not support MCP Sampling.`,
              `Distill's learn/crystallize features require MCP Sampling.`,
            ].join("\n"),
          },
        ],
      };
    }
  },
);

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
}

main().catch((error) => {
  console.error("test-sampling server error:", error);
  process.exit(1);
});
