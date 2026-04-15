#!/usr/bin/env node
/**
 * W2A MCP Server
 * 
 * Exposes any W2A-enabled site's skills as MCP tools.
 * Works with Claude Desktop, Cursor, Cline, and any MCP client.
 * 
 * Install:
 *   npm install -g w2a-mcp
 * 
 * Add to Claude Desktop config (~/.claude/claude_desktop_config.json):
 *   {
 *     "mcpServers": {
 *       "w2a": {
 *         "command": "npx",
 *         "args": ["w2a-mcp", "--url", "https://yoursite.com"]
 *       }
 *     }
 *   }
 * 
 * Or discover multiple sites:
 *   {
 *     "mcpServers": {
 *       "w2a-stripe": {
 *         "command": "npx",
 *         "args": ["w2a-mcp", "--url", "stripe.com"]
 *       },
 *       "w2a-mysite": {
 *         "command": "npx",
 *         "args": ["w2a-mcp", "--url", "mysite.com"]
 *       }
 *     }
 *   }
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const W2A_HEADERS = {
  "Accept": "application/json",
  "Agent-W2A": "1.0",
  "User-Agent": "W2A-MCP-Server/0.1.0 (+https://w2a-protocol.org)",
};

// ── Argument parsing ─────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const config = { url: null, validate: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--url" && args[i + 1]) config.url = args[++i];
    if (args[i] === "--validate") config.validate = true;
  }
  if (!config.url) {
    console.error("Usage: w2a-mcp --url <site-url>");
    console.error("Example: w2a-mcp --url stripe.com");
    process.exit(1);
  }
  return config;
}

// ── W2A discovery ─────────────────────────────────────────────────────────────

function normaliseUrl(url) {
  if (!url.startsWith("http")) url = "https://" + url;
  const parsed = new URL(url);
  return parsed.origin;
}

async function discoverSite(origin) {
  const manifestUrl = `${origin}/.well-known/agents.json`;
  const res = await fetch(manifestUrl, { headers: W2A_HEADERS });

  if (!res.ok) {
    throw new Error(
      `No W2A manifest found at ${manifestUrl} (HTTP ${res.status}). ` +
      `This site hasn't adopted W2A yet. ` +
      `Generate a manifest at https://w2a-protocol.org/tools`
    );
  }

  const manifest = await res.json();
  const skills = manifest.skills || manifest.capabilities || [];

  return {
    name: manifest.site?.name || origin,
    type: manifest.site?.type || "other",
    origin,
    skills,
    manifest,
  };
}

// ── MCP tool schema builders ─────────────────────────────────────────────────

function w2aTypeToJsonSchema(typeStr) {
  const map = {
    "string": { type: "string" },
    "string?": { type: "string" },
    "int": { type: "integer" },
    "int?": { type: "integer" },
    "float": { type: "number" },
    "float?": { type: "number" },
    "bool": { type: "boolean" },
    "bool?": { type: "boolean" },
    "object": { type: "object" },
    "object?": { type: "object" },
    "string[]": { type: "array", items: { type: "string" } },
    "int[]": { type: "array", items: { type: "integer" } },
    "object[]": { type: "array", items: { type: "object" } },
  };
  return map[typeStr] || { type: "string" };
}

function buildToolSchema(skill) {
  const properties = {};
  const required = [];

  for (const [name, type] of Object.entries(skill.input || {})) {
    properties[name] = {
      ...w2aTypeToJsonSchema(type),
      description: `${name} (${type})`,
    };
    if (!type.endsWith("?")) required.push(name);
  }

  return {
    type: "object",
    properties,
    required,
  };
}

// ── Skill execution ───────────────────────────────────────────────────────────

async function callSkill(site, skill, args) {
  const method = skill.action.split(" ")[0].toUpperCase();
  const path = skill.action.split(" ")[1] || "/";

  // Replace :param with actual values from args
  const resolvedPath = path.replace(/:([a-zA-Z_]+)/g, (_, name) => {
    if (args[name] !== undefined) {
      const val = args[name];
      const { [name]: _, ...rest } = args;
      args = rest;
      return encodeURIComponent(val);
    }
    return `:${name}`;
  });

  let url = `${site.origin}${resolvedPath}`;

  const init = {
    method,
    headers: {
      ...W2A_HEADERS,
      "Content-Type": "application/json",
    },
  };

  if (method === "GET" || method === "DELETE") {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(args)) {
      if (v !== undefined && v !== null) params.set(k, String(v));
    }
    const qs = params.toString();
    if (qs) url += `?${qs}`;
  } else {
    init.body = JSON.stringify(args);
  }

  const res = await fetch(url, init);
  const text = await res.text();

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = { response: text };
  }

  return {
    status: res.status,
    ok: res.ok,
    data,
  };
}

// ── Server setup ──────────────────────────────────────────────────────────────

async function main() {
  const config = parseArgs();
  const origin = normaliseUrl(config.url);

  let site;
  try {
    site = await discoverSite(origin);
  } catch (err) {
    console.error(`[W2A MCP] Discovery failed: ${err.message}`);
    process.exit(1);
  }

  const server = new Server(
    {
      name: `w2a-${site.name.toLowerCase().replace(/[^a-z0-9]/g, "-")}`,
      version: "0.1.0",
    },
    {
      capabilities: { tools: {} },
    }
  );

  // List tools — one per W2A skill
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    const tools = site.skills.map((skill) => ({
      name: skill.id,
      description: `${skill.intent} (${skill.action}) [auth: ${skill.auth}]`,
      inputSchema: buildToolSchema(skill),
    }));

    // Always add a discovery tool so the agent can see the full manifest
    tools.push({
      name: "w2a_site_info",
      description: `Get full W2A manifest and capability list for ${site.name}`,
      inputSchema: { type: "object", properties: {} },
    });

    return { tools };
  });

  // Call tool
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    if (name === "w2a_site_info") {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                site: site.name,
                type: site.type,
                origin: site.origin,
                skills: site.skills.map((s) => ({
                  id: s.id,
                  intent: s.intent,
                  action: s.action,
                  auth: s.auth,
                })),
                a2a_compatible: !!site.manifest.a2a_profile,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    const skill = site.skills.find((s) => s.id === name);
    if (!skill) {
      return {
        content: [
          {
            type: "text",
            text: `Skill '${name}' not found. Available: ${site.skills.map((s) => s.id).join(", ")}`,
          },
        ],
        isError: true,
      };
    }

    try {
      const result = await callSkill(site, skill, args || {});
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result.data, null, 2),
          },
        ],
        isError: !result.ok,
      };
    } catch (err) {
      return {
        content: [{ type: "text", text: `Error: ${err.message}` }],
        isError: true,
      };
    }
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error(
    `[W2A MCP] Connected to ${site.name} — ${site.skills.length} skills available`
  );
}

main().catch((err) => {
  console.error("[W2A MCP] Fatal error:", err);
  process.exit(1);
});
