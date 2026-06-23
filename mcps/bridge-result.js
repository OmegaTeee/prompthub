/**
 * Convert bridge-owned raw values and proxied MCP CallToolResult objects into
 * the response shape expected by tools/call.
 */
export function formatToolCallResult(result) {
  if (result && typeof result === 'object' && Array.isArray(result.content)) {
    return result;
  }

  return {
    content: [
      {
        type: 'text',
        text: typeof result === 'string' ? result : JSON.stringify(result, null, 2),
      },
    ],
  };
}
