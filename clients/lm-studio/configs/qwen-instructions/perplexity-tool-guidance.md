# Perplexity Tool Guidance for Qwen3 Users

## Core Principle
Use Perplexity's agentic AI browser (Comet) to perform multi-source web research, synthesize insights, create concise summaries, and generate structured comparisons within your live browsing context.

## Best Practices for Implementation

### 1. Web Research with Multi-Source Coverage
- Use Comet to search across multiple sources simultaneously
- Always include "multi-source" in your tool call prompts to ensure broad coverage
- Example: *"Search for current research on AI agent frameworks using multi-source web research"

### 2. Structured Data Synthesis & Summaries
- **Favor concise, readable formats**: Use bullet points, key metrics, and short sections instead of long walls of text
- Structure summaries to be immediately actionable and useful for downstream tasks
- Example: *Provide 3 key findings with specific data points (e.g., "Research shows 87% adoption rate in healthcare")*

### 3. Structured Comparisons
- When comparing tools, vendors, papers, or approaches:
  - Explicitly ask Comet to generate a structured comparison
  - **Ideal output**: A clear table format showing key attributes side-by-side
- Example: *"Compare Qwen3 with GPT-4 in terms of reasoning capabilities and tool performance. Output as a structured table."

### 4. Context-Aware Usage
- Activate Comet when it can see your current browsing context (open tabs, documents)
- This allows it to leverage existing information instead of starting from scratch
- Avoid using Comet in isolation from your current workflow

## Implementation Checklist for Qwen3 Users

| Step | Action |
|------|--------|
| 1️⃣ | Ensure Perplexity's agentic AI browser (Comet) is available and running in your environment |
| 2️⃣ | When planning web research, include "multi-source" and "research-based insight synthesis" in your prompt |
| 3️⃣ | Use structured output formats: bullet points for findings, tables for comparisons |
| 4️⃣ | Verify the output is relevant by checking against current context (open tabs, documents) |
| 5️⃣ | When presenting results, provide a concise conclusion with actionable takeaways |

## Example Workflow

**User Prompt**: "Compare Qwen3 and GPT-4 in terms of reasoning capabilities for technical problem-solving."

**Qwen3 Response**: 
- **Thought**: Need to compare Qwen3 and GPT-4 on reasoning performance
- **Action**: Use Perplexity's Comet browser to conduct multi-source research on AI agent frameworks
- **Observation**: Retrieved comparative analysis showing key differences in reasoning depth and tool execution
- **Output (structured table)**:
| Feature | Qwen3 | GPT-4 |
|--------|-------|-------|
| Reasoning Depth | Strong at structured problem-solving | Excellent at creative reasoning |
| Tool Execution Accuracy | 92% success rate in technical tasks | 89% success rate |
| Long Context Handling | Up to 32k tokens | Up to 128k tokens |

**Conclusion**: Qwen3 excels in structured technical reasoning, while GPT-4 outperforms in creative problem-solving.
