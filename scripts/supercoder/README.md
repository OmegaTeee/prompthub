# Quick start

Open terminal in `scripts/supercoder/` and run `install.sh`. This will install via `homebrew` the `supercoder` CLI tool and set up the necessary environment variables.

[huytd/supercoder](https://github.com/huytd/supercoder)
supercoder is a terminal-based coding agent that allows you to interact with your codebase using natural language. It supports tool calling, which means it can use various tools to assist you in coding tasks.

If you're using LM Studio, you probably know that models supporting tool calling, like qwen2.5-instruct, weren't very good at coding. On the other hand, qwen2.5-coder is pretty solid on code, but doesn't support tool calling :(

I was able to build a terminal-based coding agent (see link below) that allows these models to use tools. You can even use it with some free models on OpenRouter.

# LM Studio model recommendations:

| ARCH      | PARAMS  | LLM                             | USE CASE |
|-----------|---------|---------------------------------|--------|
| Qwen2     | 7B      | qwen2.5-coder-7b-instruct       | supercoder |
| Qwen2     | 32B     | qwen2.5-coder-32b-instruct      | supercoder-max |
| qwen3     | 0.6B    | qwen3-0.6b                      | lm-studio speculative decoding and text rewriter |
| qwen3     | 1.7B    | qwen3-1.7b                      | testing as assistant  |
| qwen3     | 4B      | qwen3-4b-instruct-2507          | prompthub default  |
| qwen3     | 4B      | qwen3-4b-thinking-2507          | prompthub orchestrator  |
| qwen35    | 4B      | qwen3.5-4b                      | test driving multimodal  |


Qwen2.5-Coder as a foundation for code agents and real-world tooling workflows (tool-use, long-context, multi-language support). It does not itself implement an autonomous “agent loop” (planning, tool-calling, environment interaction), but it is a strong base for building such systems. The 7B model is surprisingly capable and can be used for many coding tasks, while the 32B model excels at complex reasoning and multi-file understanding.



## Shell configuration

```zsh
# LM Studio + SuperCoder configuration
export SUPERCODER_BASE_URL="http://127.0.0.1:1234/v1"
export SUPERCODER_API_KEY="${LMSTUDIO_API_KEY}"

# Default: fast single-file / everyday coding
export SUPERCODER_MODEL="qwen2.5-coder-7b-instruct"
alias supercoder-default='SUPERCODER_MODEL=qwen2.5-coder-7b-instruct supercoder'

# Heavy: architecture, multi-file reasoning
alias supercoder-max='SUPERCODER_MODEL=qwen2.5-coder-32b-instruct supercoder'

```

# Aliases

```zsh
suppercoder         # Launches supercoder with default model (7B)
supercoder-max      # Loads the 32B model
supercoder-default  # Use to switch back to the 7B model

```

🧠 When to use each

Use 7B `supercoder` for:
- editing files
- navigating repo
- refactoring
- quick fixes

Use 32B `supercoder-max` for:
- complex architecture
- debugging weird issues
- multi-file reasoning
