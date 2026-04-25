# Qwen3-4B tool schema templates for LM Studio
This directory contains JSON Schema templates for LM Studio enhancement prompts, designed to align with the Qwen3-4B-Thinking-2507 model's capabilities and your bridge's tool schema style. These templates are meant to be used in PromptHub's enhancement rules to rewrite user prompts into structured formats that the model can use for intent classification and tool routing.

## Baseline version

- This is the **general baseline** I’d use to get on the right track with Qwen3-4B-Instruct-2507 or Qwen3-4B-Thinking-2507 in LM Studio. It matches your Hermes-style tool call envelope and your bridge’s minified schema style. [docs/architecture/mcp-transport-adapters.md](../../../../docs/architecture/mcp-transport-adapters.md)
- Keep only a few high-value tools exposed at first, because your own bridge docs emphasize tool-count reduction and recursive schema minification for smaller models. [mcps/README.md](../../../../mcps/README.md)

```json
[
  {
    "type": "function",
    "function": {
      "name": "desktop-commander_read_file",
      "description": "Read a text file.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1
          }
        },
        "required": ["path"],
        "additionalProperties": false
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "desktop-commander_write_file",
      "description": "Write text to a file.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1
          },
          "content": {
            "type": "string"
          }
        },
        "required": ["path", "content"],
        "additionalProperties": false
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "desktop-commander_run_command",
      "description": "Run a shell command.",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {
            "type": "string",
            "minLength": 1
          },
          "working_directory": {
            "type": "string"
          },
          "timeout_ms": {
            "type": "integer",
            "minimum": 1
          }
        },
        "required": ["command"],
        "additionalProperties": false
      }
    }
  }
]
```

## Comet + optimized desktop-commander

- This is the version I think best matches your stated goal: **Comet exposed in the right shape**, plus a deliberately small desktop-commander set optimized for practical agent work. Your Perplexity guidance says Comet is best for multi-source research, concise synthesis, and structured comparisons; your MCP docs show desktop-commander is for file ops and terminal commands. [clients/lm-studio/configs/perplexity_tool_guidance.md](../perplexity_tool_guidance.md)
- I would keep desktop-commander to only **read_file**, **write_file**, and **run_command** at first. That gives the model enough to inspect, patch, and execute without handing it a giant tool menu. [docs/architecture/mcp-transport-adapters.md](../../../../docs/architecture/mcp-transport-adapters.md)

```json
[
  {
    "type": "function",
    "function": {
      "name": "perplexity-comet_research",
      "description": "Do multi-source web research in Comet and return concise findings.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "minLength": 3
          },
          "multi_source": {
            "type": "boolean"
          },
          "output_format": {
            "type": "string",
            "enum": ["bullets", "table", "summary"]
          }
        },
        "required": ["query"],
        "additionalProperties": false
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "perplexity-comet_compare_sources",
      "description": "Research a topic and compare entities in a structured way.",
      "parameters": {
        "type": "object",
        "properties": {
          "topic": {
            "type": "string",
            "minLength": 3
          },
          "entities": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "minItems": 2
          },
          "output_format": {
            "type": "string",
            "enum": ["table", "bullets"]
          }
        },
        "required": ["topic", "entities"],
        "additionalProperties": false
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "desktop-commander_read_file",
      "description": "Read a text file.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1
          }
        },
        "required": ["path"],
        "additionalProperties": false
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "desktop-commander_write_file",
      "description": "Write text to a file.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1
          },
          "content": {
            "type": "string"
          }
        },
        "required": ["path", "content"],
        "additionalProperties": false
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "desktop-commander_run_command",
      "description": "Run a shell command.",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {
            "type": "string",
            "minLength": 1
          },
          "working_directory": {
            "type": "string"
          },
          "timeout_ms": {
            "type": "integer",
            "minimum": 1
          }
        },
        "required": ["command"],
        "additionalProperties": false
      }
    }
  }
]
```

## Canonical reference version

- This is the **reference version with comments** — useful as a design artifact even if you never deploy it. It reflects the same architecture you documented: server-prefixed tool names, short schemas, and a clean split between research tools and local execution tools. [clients/lm-studio/configs/perplexity_tool_guidance.md](../perplexity_tool_guidance.md)
- JSON itself does not allow comments, so this is technically **JSONC** style for human reference, not raw JSON. [docs/architecture/mcp-transport-adapters.md](../../../../docs/architecture/mcp-transport-adapters.md)

```jsonc
[
  {
    // Comet for general research. Keep query natural-language and explicit.
    "type": "function",
    "function": {
      "name": "perplexity-comet_research",
      "description": "Use Comet for multi-source web research and concise synthesis.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": { "type": "string", "minLength": 3 },
          "multi_source": { "type": "boolean" },
          "output_format": {
            "type": "string",
            "enum": ["bullets", "table", "summary"]
          },
          "context_aware": { "type": "boolean" }
        },
        "required": ["query"],
        "additionalProperties": false
      }
    }
  },
  {
    // Best when the user asks for a structured comparison table.
    "type": "function",
    "function": {
      "name": "perplexity-comet_compare_sources",
      "description": "Compare tools, vendors, papers, or approaches using structured output.",
      "parameters": {
        "type": "object",
        "properties": {
          "topic": { "type": "string", "minLength": 3 },
          "entities": {
            "type": "array",
            "items": { "type": "string", "minLength": 1 },
            "minItems": 2
          },
          "output_format": {
            "type": "string",
            "enum": ["table", "bullets"]
          }
        },
        "required": ["topic", "entities"],
        "additionalProperties": false
      }
    }
  },
  {
    // Smallest useful desktop-commander file inspection tool.
    "type": "function",
    "function": {
      "name": "desktop-commander_read_file",
      "description": "Read a text file from disk.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": { "type": "string", "minLength": 1 }
        },
        "required": ["path"],
        "additionalProperties": false
      }
    }
  },
  {
    // Only needed when the model is allowed to patch or create files.
    "type": "function",
    "function": {
      "name": "desktop-commander_write_file",
      "description": "Write or overwrite a text file.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": { "type": "string", "minLength": 1 },
          "content": { "type": "string" }
        },
        "required": ["path", "content"],
        "additionalProperties": false
      }
    }
  },
  {
    // Keep command execution available, but schema small and literal.
    "type": "function",
    "function": {
      "name": "desktop-commander_run_command",
      "description": "Run a shell command in a working directory.",
      "parameters": {
        "type": "object",
        "properties": {
          "command": { "type": "string", "minLength": 1 },
          "working_directory": { "type": "string" },
          "timeout_ms": { "type": "integer", "minimum": 1 }
        },
        "required": ["command"],
        "additionalProperties": false
      }
    }
  },
  {
    // Nice optional future addition if you later want safe directory inspection.
    "type": "function",
    "function": {
      "name": "desktop-commander_list_directory",
      "description": "List files in a directory.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": { "type": "string", "minLength": 1 }
        },
        "required": ["path"],
        "additionalProperties": false
      }
    }
  }
]
```

## Recommended use

- Use the **baseline version** first if you want the fastest route to a stable LM Studio setup. It stays close to your bridge’s minified-schema philosophy and avoids overexposing tools. [mcps/README.md](../../../../mcps/README.md)
- Use the **Comet + optimized desktop-commander** version when you want your main everyday config, because it reflects your own Comet guidance and keeps local execution narrow and useful. [clients/lm-studio/configs/perplexity_tool_guidance.md](../perplexity_tool_guidance.md)
- Keep the **canonical reference** around only as documentation, because your own template and bridge design both favor short, stripped schemas over verbose “perfect” definitions for real inference-time use. [clients/lm-studio/configs/qwen-thinking-hermes-style-improvements-2.j2](../qwen-thinking-hermes-style-improvements.j2)

## Two important notes

- These schemas are **architecturally aligned** with your files, but they are still canonical shapes, not guaranteed byte-for-byte upstream MCP signatures, because the attached docs describe capabilities and bridge behavior, not the exact live `tools/list` payload from `desktop-commander` or `perplexity-comet`. [mcps/README.md](../../../../mcps/README.md)
- The truly exact production version should be generated from the actual cached `tools/list` output your router already stores, since your bridge fetches and preserves the important JSON Schema fields recursively and caches them for reuse. [docs/architecture/mcp-transport-adapters.md](../../../../docs/architecture/mcp-transport-adapters.md)

My strongest recommendation: start with the **Comet + optimized desktop-commander** version and pair it with Qwen3-4B-Instruct-2507 first, then move to Thinking-2507 once you like the tool surface.
