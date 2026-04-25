# User Guide: Qwen3 Hermes-Style Thinking Template

## Getting Started
1. Place this template in your LM Studio preset directory (`~/.lmstudio/hub/presets/prompt-templates/`)
2. Select it when creating a new Qwen3 model instance
3. Begin conversations with your model using natural language prompts

## How It Works
The template uses a structured thinking workflow:

### Thought → Action → Observation Pattern
- **Thought**: The model considers the problem from multiple angles
- **Action**: Executes specific steps to solve the problem
- **Observation**: Records what was observed during execution

This creates a clear, logical flow that helps Qwen3 reason through complex problems.

## Sample Conversation
**User**: What's the capital of France?
**Assistant**: I need to find information about France's capital. Let me think...
- **Thought**: The capital of France is likely Paris based on general knowledge
- **Action**: Return the answer directly
- **Observation**: Found that Paris is the capital of France
**Response**: The capital of France is Paris.

## Best Practices
- Use this template for tasks requiring logical reasoning or multi-step problem solving
- Avoid using it for simple factual questions where direct answers are sufficient
- Combine with tool calling when you need external information

## Common Issues & Solutions
| Issue | Solution |
|-------|----------|
| Model doesn't follow thinking structure | Ensure the template is selected in your model settings |
| Tool calls fail to parse | Verify JSON formatting matches LM Studio requirements |
| Excessive prompt length | This template reduces bloat by filtering historical thinking blocks |

## For Developers
This template includes developer comments that explain:
- The purpose of each section
- Key design decisions
- How the code works

The structure follows best practices from Hermes-style agent frameworks while being optimized for small Qwen3 models in LM Studio.
