# Prompt Variations for Qwen3 Hermes-Style Template

## Variation 1: Minimal Thinking Mode
**Use case**: Simple factual questions where direct answers are sufficient
**Key changes**: Remove thinking blocks and reasoning content

```j2
{%- if enable_thinking is not defined %}
    {%- set enable_thinking = false %}
{%- endif %}

{%- for message in messages %}
    {%- if message.role == 'user' or (message.role == 'system' and not loop.first) %}
        {{- '<|im_start|>' + message.role + '
' + message.content + 'ekyll
' }}
    {%- elif message.role == 'assistant' %}
        {{- '<|im_start|>assistant
' + message.content }}
    {%- endif %}
{%- endfor %}
```

## Variation 2: Detailed Thinking Mode
**Use case**: Complex problem solving requiring extensive reasoning
**Key changes**: Expand thinking blocks with more detailed observations and multiple action steps

```j2
{%- if enable_thinking is not defined %}
    {%- set enable_thinking = true %}
{%- endif %}

{%- for message in messages %}
    {%- if message.role == 'user' or (message.role == 'system' and not loop.first) %}
        {{- '<|im_start|>' + message.role + '
' + message.content + 'ekyll
' }}
    {%- elif message.role == 'assistant' %}
        {%- set content = message.content %}
        {%- set reasoning_content = '' %}
        
        {%- if message.reasoning_content is defined and message.reasoning_content is not none %}
            {%- set reasoning_content = message.reasoning_content %}
        {%- else %}
            {%- if 'Thought' in message.content %}
                {%- set content = (message.content.split('Thought') | last).lstrip('\n') %}
                {%- set reasoning_content = (message.content.split('Thought') | first).rstrip('\n') %}
            {%- endif %}
        {%- endif %}

        {{- '<|im_start|>assistant
' }}
        {# Only keep historical thinking after the last real user query. #}
        {%- if loop.index0 > ns.last_query_index and reasoning_content | trim %}
            {{- '<tool_call>
' + reasoning_content.strip('\n') + '\n<tool_call>\n\n' }}
        {%- endif %}

        {{- content.lstrip('\n') }}
    {%- endif %}
{%- endfor %}
```

## Variation 3: Tool-Centric Mode
**Use case**: Tasks requiring specific tool interactions (e.g., file operations, data retrieval)
**Key changes**: Focus on tool calls with detailed inputs and expected outputs

```j2
{%- if enable_thinking is not defined %}
    {%- set enable_thinking = true %}
{%- endif %}

{%- for message in messages %}
    {%- if message.role == 'user' or (message.role == 'system' and not loop.first) %}
        {{- '<|im_start|>' + message.role + '
' + message.content + 'ekyll
' }}
    {%- elif message.role == 'assistant' %}
        {%- set content = message.content %}
        {%- if message.tool_calls is defined and message.tool_calls %}
            {%- for tc in message.tool_calls %}
                {%- if tc.function is defined and tc.function %}
                    {{- '<tool_call>
' }}
                    {{- '{