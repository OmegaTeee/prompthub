import assert from 'node:assert/strict';
import test from 'node:test';

import { formatToolCallResult } from './bridge-result.js';

test('preserves structured content from proxied tool results', () => {
  const result = {
    content: [{ type: 'text', text: '{"ok":true}' }],
    structuredContent: { ok: true },
  };

  assert.deepEqual(formatToolCallResult(result), result);
});

test('wraps plain objects as text content for legacy tools', () => {
  assert.deepEqual(formatToolCallResult({ ok: true }), {
    content: [
      {
        type: 'text',
        text: '{\n  "ok": true\n}',
      },
    ],
  });
});
