---
description: Use Context7 as the canonical source for external library documentation, avoiding reliance on stale training data.
applyTo: "**"
---
# Context7: Library Documentation Guidelines

Purpose: ensure all contributors and MCP tools use Context7 as the canonical source for external library documentation, avoiding reliance on stale training data.

Policy

- Always use Context7 for library documentation before suggesting or generating
  code that depends on an external library (React, Next.js, Vue, Rails, etc.).
- Prefer versioned documentation when available; never assume API stability across
  major versions.
- If Context7 cannot resolve a library or there is no matching documentation,
  explicitly state the limitation and ask the user whether to proceed.

How to use (recommended sequence)

1. resolve-library-id

  - Use Context7's resolver to convert a human library name (and optional
    version hint) to a Context7-compatible library id.
  - Example (pseudo):

    ```text
    mcp.context7.resolve-library-id: { "query": "react useEffect React 18" }
    -> returns: "/reactjs/react" or "/reactjs/react/v18.2.0"
    ```

2. query docs

  - After resolving the library id, call the Context7 docs query endpoint to
    fetch the authoritative documentation or specific API page.
  - Example (pseudo):

    ```text
    mcp.context7.query-docs: { "libraryId": "/reactjs/react/v18.2.0", "query": "useEffect" }
    -> returns: HTML/markdown summary, usage examples, and API signatures
    ```

Best practices for MCP tool authors and agents

- Always pull docs first, then generate code. Use the docs to verify signatures,
  recommended patterns, and lifecycle differences (e.g., React 18 Strict Mode
  double-invocation behavior for effects in development).
- Prefer examples taken from the official docs or adapted minimally to the
  project's context; annotate any adaptation clearly.
- Cache docs responses per-version but include cache expiry and a cache-bypass
  mode for urgent updates.

Project notes

- This repository already includes a Context7 server entry in
- [configs/vscode-mcp.json](../configs/vscode-mcp.json).
- When adding new MCP servers or updating `configs/vscode-mcp.json`, ensure the
  Context7 server is present and reachable by local tooling.

Example: fetching React `useEffect` docs (high-level)

1. Call `resolve-library-id` with "react" and a version hint (e.g. "18").
2. Call `query-docs` with the returned library id and the query string
   "useEffect".
3. Use the returned doc content to verify semantics (cleanup functions,
   dependency array behavior, Strict Mode notes) and then produce sample code.

Appendix: Minimal verbatim instruction (copyable)

> Always use Context7 for library documentation:

- Before suggesting code for any external library, call `resolve-library-id` and
  then `query-docs` (or the MCP equivalents).
- Never rely solely on training data for framework APIs.
- Pull docs first, then generate code. Use version-specific documentation when
  available.
