# Qwen3 Hermes-Style Thinking Template

## Overview
This template implements a structured, Hermes-style thinking workflow for Qwen3 models in LM Studio. It enables clear reasoning and tool calling with minimal prompt bloat.

## Key Features
- ✅ Structured thinking flow (Thought → Action → Observation)
- ✅ Proper JSON formatting for tool calls
- ✅ Reduced prompt size by filtering historical thinking blocks
- ✅ Developer-friendly comments explaining each section

## Usage
Place this template in your LM Studio preset directory and use it with Qwen3 models.

## Development Notes
This template was developed to address common issues with large language model reasoning workflows, including:
- Excessive prompt length
- Unstructured thinking blocks
- Poor tool calling reliability

The design follows best practices from Hermes-style agent frameworks while being optimized for small Qwen3 models in LM Studio.

## Version History
- v1.0: Initial release with core Hermes-style structure
- v1.1: Improved prompt bloat reduction and developer documentation

## Related Resources
- [neil/qwen3-thinking](https://lmstudio.ai/neil/qwen3-thinking) - LM Studio Hub repository
- [Qwen3 Documentation](https://qwen.readthedocs.io/en/latest/framework/function_call.html) - Official Qwen3 function calling guide
