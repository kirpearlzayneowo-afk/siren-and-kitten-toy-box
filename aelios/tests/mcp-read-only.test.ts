import assert from "node:assert/strict";
import test from "node:test";
import { handleMcp } from "../src/api/mcp";
import type { Env } from "../src/types";

const env = {
  DB: {} as D1Database,
  MEMORY_MCP_API_KEY: "mcp-key"
} as Env;

const ctx = {
  waitUntil() {}
} as unknown as ExecutionContext;

async function callMcp(body: Record<string, unknown>): Promise<Record<string, any>> {
  const response = await handleMcp(
    new Request("https://example.test/mcp", {
      method: "POST",
      headers: {
        authorization: "Bearer mcp-key",
        "content-type": "application/json"
      },
      body: JSON.stringify(body)
    }),
    env,
    ctx
  );
  return (await response.json()) as Record<string, any>;
}

test("tools/list exposes only read-only memory tools", async () => {
  const response = await callMcp({ jsonrpc: "2.0", id: 1, method: "tools/list" });
  const names = response.result.tools.map((tool: { name: string }) => tool.name);

  assert.deepEqual(names, [
    "memory_search",
    "memory_list",
    "memory_get",
    "memory_boot",
    "memory_recall",
    "diary_get"
  ]);
});

test("tools/call rejects disabled and unknown tools before touching storage", async () => {
  const disabledTools = [
    "memory_ingest",
    "memory_export",
    "memory_delete",
    "memory_upsert",
    "memory_supersede",
    "memory_archive",
    "memory_pin",
    "memory_create",
    "glossary_set",
    "not-a-tool"
  ];

  for (const name of disabledTools) {
    const response = await callMcp({
      jsonrpc: "2.0",
      id: name,
      method: "tools/call",
      params: { name, arguments: {} }
    });

    assert.equal(response.result.isError, true, name);
    assert.match(response.result.content[0].text, /read-only MCP mode/);
  }
});
