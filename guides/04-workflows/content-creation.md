# Content Creation Workflow with Claude Desktop

**Master research, writing, and content refinement using Claude Desktop + AgentHub + DeepSeek-R1**

> **What you'll learn:** How to leverage AgentHub's DeepSeek-R1 enhancement for research synthesis, long-form writing, fact-checking, and content refinement.

---

## Overview

### What This Guide Covers
- Research and information gathering with MCP tools
- Long-form content generation (articles, reports, documentation)
- Fact-checking and citation management
- Content refinement and editing workflows
- Multi-stage writing process optimization

### Prerequisites
- ✅ Claude Desktop app installed
- ✅ AgentHub running ([Quick check](../../_shared/health-checks.md))
- ✅ DeepSeek-R1 model downloaded: `ollama pull deepseek-r1:7b`
- ✅ Enhancement enabled in Claude Desktop config

### Estimated Time
- Initial setup: 5 minutes
- Workflow mastery: 3-4 writing sessions

---

## Concepts

### Why DeepSeek-R1?
DeepSeek-R1 excels at structured reasoning and is ideal for content creation because:
- **Chain-of-thought reasoning** - Explicitly shows its thinking process
- **Structured responses** - Organized paragraphs, clear sections
- **Fact synthesis** - Combines multiple sources into coherent narratives
- **Critical thinking** - Evaluates arguments and identifies gaps

### How Enhancement Works for Content
When you make a request in Claude Desktop:
1. **Your prompt** → Sent to AgentHub with `X-Enhance: true`
2. **DeepSeek-R1** → Structures the request, adds reasoning framework
3. **Enhanced prompt** → Forwarded to MCP servers (fetch, brave-search, etc.)
4. **Richer content** → More thoughtful, well-researched responses

**Key benefit:** The AI actively reasons through content structure before writing.

---

## Step-by-Step: Initial Setup

### 1. Verify Enhancement is Active

**Check Claude Desktop config:**

```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Should contain:**

```json
{
  "mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Enhance": "true",
        "X-Client-Name": "claude-desktop"
      }
    }
  }
}
```

**Test enhancement:**
1. Open Claude Desktop
2. Ask: "What enhancement model are you using?"
3. Should respond: "I'm using DeepSeek-R1 for structured reasoning"

---

### 2. Configure Enhancement Rules

Edit `~/.local/share/agenthub/configs/enhancement-rules.json`:

```json
{
  "claude-desktop": {
    "model": "deepseek-r1:7b",
    "system_prompt": "You are a professional content creator and researcher. Structure your responses with:\n- Clear reasoning process\n- Well-organized sections\n- Proper citations and sources\n- Engaging, readable prose\n- Critical analysis of information\n\nAlways show your thinking before providing final content.",
    "enabled": true,
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

**Restart AgentHub:**

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.router.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.router.plist
```

---

### 3. Verify MCP Servers

**Essential servers for content creation:**

```bash
curl http://localhost:9090/servers
```

**Should show:**
- ✅ `fetch` - Retrieve web content for research
- ✅ `brave-search` - Web search for sources (requires API key)
- ✅ `filesystem` - Save drafts and research notes

**If missing, add to `configs/mcp-servers.json`** (see [Core Setup](../../02-core-setup/README.md))

---

## Understanding the Workflow

### The Content Creation Cycle

```
1. Research → 2. Outline → 3. Draft → 4. Refine → 5. Fact-Check → 6. Publish
   ↑                                                                    ↓
   └───────────────────────── Iterate ←──────────────────────────────┘
```

**Where AI helps most:**
- **Research** - Gather sources, synthesize information
- **Outline** - Structure ideas, identify gaps
- **Draft** - Generate sections, maintain tone
- **Fact-check** - Verify claims, find citations

**Where you lead:**
- **Refine** - Voice, style, brand alignment
- **Publish** - Final quality check, formatting

---

## Common Use Cases

### Use Case 1: Research Synthesis

**Scenario:** You need to write about a complex topic you're not an expert in.

**Workflow:**

**Step 1:** Broad research

```
Prompt: "Research the current state of AI code generation tools. Find 5-7 authoritative sources covering:
- Market leaders (GitHub Copilot, Claude Code, Cursor)
- Technology approaches (LLM models, context mechanisms)
- Developer adoption trends
- Strengths and limitations
Provide source URLs."
```

**Step 2:** Deep dive on specific aspects

```
Prompt: "From the sources, extract key differences between GitHub Copilot and Claude Code. Focus on:
- Code quality
- Context awareness
- Pricing models
- Developer workflow integration
Create a comparison table."
```

**Step 3:** Synthesize into narrative

```
Prompt: "Using the research, write a 500-word executive summary on the future of AI code generation. Include:
- Current state (3 sentences)
- Key trends (2 paragraphs)
- Prediction for next 12 months (1 paragraph)
- Cite sources inline (Author, Year)"
```

**Why this works:**
- Fetch MCP server retrieves actual web content
- DeepSeek-R1 synthesizes multiple sources
- Enhanced reasoning produces coherent narratives

---

### Use Case 2: Long-Form Content Generation

**Scenario:** Write a 2,000-word blog post on a technical topic.

**Workflow:**

**Step 1:** Create detailed outline

```
Prompt: "Create an outline for a blog post: 'How to Build Resilient Microservices with Circuit Breakers'

Target audience: Senior backend engineers
Goal: Educate on circuit breaker pattern
Length: 2,000 words
Tone: Professional but accessible

Include:
- Intro hook (100 words)
- 3-4 main sections with subsections
- Real-world examples
- Code snippets placeholder notes
- Conclusion and call-to-action"
```

**Step 2:** Review and adjust outline
- Ensure logical flow
- Add/remove sections based on scope
- Specify which sections need examples

**Step 3:** Generate section-by-section

```
Prompt: "Write the Introduction section (200 words). Open with a story about a production outage caused by cascading failures. Transition to explaining what circuit breakers are."
```

**Step 4:** Maintain consistency across sections

```
Prompt: "Write Section 2: 'How Circuit Breakers Work' (400 words). Match the tone and style of the introduction. Include a simple diagram description."
```

**Step 5:** Integrate and smooth transitions

```
Prompt: "Review the transition between Section 2 and Section 3. Make it flow naturally."
```

**Section-by-section benefits:**
- Easier to review and edit smaller chunks
- Maintain control over content direction
- Adjust tone/depth as you go

---

### Use Case 3: Fact-Checking and Citations

**Scenario:** Verify claims in your draft and add proper citations.

**Workflow:**

**Step 1:** Identify claims to verify

```
Prompt: "Review this paragraph and identify statements that need citations:

'Circuit breakers prevent cascading failures in microservices. Netflix pioneered this pattern in their Hystrix library. Studies show that 60% of production outages are caused by cascading failures.'

List each claim and indicate confidence level."
```

**Step 2:** Find authoritative sources

```
Prompt: "Find authoritative sources for:
1. Netflix's Hystrix library and circuit breaker pattern
2. Statistics on cascading failure causes in production

Prioritize: official documentation, academic papers, reputable tech blogs"
```

**Step 3:** Add inline citations

```
Prompt: "Rewrite the paragraph with proper inline citations in Chicago style. Use the sources you found."
```

**Step 4:** Create bibliography

```
Prompt: "Generate a bibliography for all cited sources in this article. Use MLA format."
```

---

### Use Case 4: Content Refinement

**Scenario:** Your draft is complete but needs polish.

**Workflow:**

**Step 1:** Readability analysis

```
Prompt: "Analyze this section for readability. Identify:
- Overly complex sentences
- Jargon that needs explanation
- Passive voice instances
- Transition gaps
Suggest specific improvements."
```

**Step 2:** Tone adjustment

```
Prompt: "This section feels too formal. Make it more conversational while maintaining professionalism. Keep technical accuracy."
```

**Step 3:** Engagement optimization

```
Prompt: "Make this introduction more engaging. Add:
- A compelling hook in the first sentence
- A clear value proposition
- A preview of what readers will learn
Keep it under 150 words."
```

**Step 4:** SEO optimization

```
Prompt: "Optimize this article for SEO targeting keyword 'circuit breaker pattern'. Suggest:
- Title alternatives
- Meta description (155 characters)
- Header structure improvements
- Keyword placement opportunities
Don't sacrifice readability."
```

---

### Use Case 5: Interview-to-Article Transformation

**Scenario:** Turn interview notes into a polished article.

**Workflow:**

**Step 1:** Extract key points

```
Prompt: "Review these interview notes and extract:
- 5 key insights
- 3 compelling quotes
- Main themes/topics discussed
- Potential article angles

[Paste interview transcript]"
```

**Step 2:** Structure narrative

```
Prompt: "Create an article outline from this interview. Structure it as:
- Lede (introduce subject and main insight)
- Background (3 paragraphs on subject's expertise)
- Q&A sections (group related questions)
- Conclusion (key takeaway and future outlook)"
```

**Step 3:** Write in narrative form

```
Prompt: "Write the article based on this outline. Use quotes strategically (20% quotes, 80% narrative). Maintain the subject's voice while making it readable."
```

**Step 4:** Add context

```
Prompt: "Add context paragraphs explaining technical terms. Target audience: general tech-savvy readers, not domain experts."
```

---

### Use Case 6: Content Repurposing

**Scenario:** Turn a blog post into multiple content formats.

**Workflow:**

**Step 1:** Twitter thread

```
Prompt: "Convert this blog post into a Twitter thread (10-12 tweets). Each tweet:
- Standalone clarity
- Compelling hooks
- Call-to-action in final tweet
- Include thread numbering (1/12, 2/12...)"
```

**Step 2:** LinkedIn post

```
Prompt: "Adapt the key insights into a LinkedIn post (1,300 characters). Professional tone, include:
- Eye-catching first line
- 3 bullet points with key takeaways
- Question to encourage comments
- Link to full article"
```

**Step 3:** Email newsletter

```
Prompt: "Create a newsletter version (300 words). Include:
- Personal intro paragraph
- Summary of article highlights
- 'Why this matters' section
- Clear CTA to read full post"
```

**Step 4:** Presentation outline

```
Prompt: "Create a 10-slide presentation outline covering this article's main points. Include speaker notes."
```

---

## Advanced Techniques

### Technique 1: The "Thinking Aloud" Approach

Leverage DeepSeek-R1's reasoning capabilities:

```
Prompt: "Before writing this section, think through:
- Who is the target audience and what do they already know?
- What's the most important takeaway?
- What examples will resonate?
- What questions might they have?

Then write the section."
```

**Benefits:**
- More thoughtful content
- Better audience alignment
- Identifies gaps before writing

---

### Technique 2: Iterative Depth Control

Start broad, then dive deep:

```
1st prompt: "Write a high-level overview of API versioning (200 words)"
2nd prompt: "Expand the 'semantic versioning' paragraph into 500 words with examples"
3rd prompt: "Add a section on breaking changes and migration strategies (300 words)"
```

---

### Technique 3: Voice Consistency

Maintain consistent voice across long documents:

```
Prompt: "Analyze the tone and style of this first section:
[paste sample]

When writing future sections, match:
- Sentence structure variety
- Technical depth level
- Use of examples
- Formality level
- Humor/personality"
```

---

### Technique 4: Multi-Source Synthesis

Compare and synthesize competing viewpoints:

```
Prompt: "I've found 3 articles with different perspectives on AI safety:
- Article A argues for regulation
- Article B emphasizes industry self-regulation
- Article C focuses on technical solutions

Synthesize these into a balanced view. Identify:
- Common ground
- Key disagreements
- Your assessment of strongest arguments
- Gaps in the debate"
```

---

## Best Practices

### 1. Research First, Write Second

**Good workflow:**

```
✅ Gather 5-10 sources
✅ Extract key points
✅ Create outline
✅ Write first draft
✅ Fact-check and cite
```

**Bad workflow:**

```
❌ Start writing immediately
❌ Research as you go
❌ Add citations at the end
```

---

### 2. Chunk Long Content

Don't ask for 2,000 words at once:

```
✅ "Write Section 3 (400 words)"
❌ "Write the entire article (2,000 words)"
```

**Chunking benefits:**
- Easier to maintain quality
- Better control over direction
- Simpler to review and edit

---

### 3. Specify Tone and Audience

**Be explicit:**

```
✅ "Write for startup founders with technical background. Professional but conversational. Use analogies, avoid jargon."

❌ "Write an article"
```

---

### 4. Use Progressive Refinement

**First pass:** Get content down

```
Prompt: "Write a rough draft. Don't worry about polish, focus on hitting key points."
```

**Second pass:** Structure and flow

```
Prompt: "Improve structure. Ensure logical flow between paragraphs."
```

**Third pass:** Readability

```
Prompt: "Polish language. Improve sentence variety, eliminate passive voice."
```

**Fourth pass:** Engagement

```
Prompt: "Enhance engagement. Add hooks, strengthen examples, improve transitions."
```

---

### 5. Maintain Research Notes

Create a research summary document:

```
Prompt: "Organize all research findings into a reference document with:
- Source title, author, URL
- Key quotes (with page/section numbers)
- Main arguments/findings
- Credibility assessment
- How it relates to my article"
```

**Save this in a file** so you can reference it throughout writing.

---

## Troubleshooting

### Issue: Content lacks depth

**Solution:** Request reasoning process

```
Prompt: "This feels superficial. Before revising, explain:
- What makes this topic complex?
- What nuances am I missing?
- What would a domain expert add?
Then rewrite with more depth."
```

---

### Issue: Writing feels generic

**Solution:** Add specific examples

```
Prompt: "Replace abstract statements with concrete examples. For each claim, provide:
- Real company/product example
- Specific numbers or metrics
- Named people or events"
```

---

### Issue: Sources are outdated

**Solution:** Constrain research timeframe

```
Prompt: "Find sources published in the last 12 months only. Focus on 2025-2026 information."
```

---

### Issue: Citations are incomplete

**Solution:** Request full citation details

```
Prompt: "For each source, provide complete citation information:
- Full author name(s)
- Publication date
- Article/book title
- Publisher/website
- DOI or URL
- Access date"
```

---

### Issue: Tone shifts between sections

**Solution:** Establish style guide

```
Prompt: "Create a style guide based on Section 1:
- Sentence length range
- Paragraph length
- Technical depth
- Example frequency
- Use of humor
Apply this guide to Section 2."
```

---

## Key Takeaways

- ✅ **DeepSeek-R1 enables structured reasoning** - See AI's thinking process
- ✅ **Research before writing** - Gather sources first, synthesize second
- ✅ **Write in chunks** - Section-by-section for better quality control
- ✅ **Verify claims** - Use fetch MCP server to check facts and add citations
- ✅ **Iterate in layers** - Draft → Structure → Readability → Engagement
- ✅ **Specify tone and audience** - Clear prompts produce better content
- ✅ **Repurpose efficiently** - One article → multiple content formats

**Next steps:**
- Explore [Code Development Workflow](code-development.md) for technical writing
- See [Quick Commands](quick-commands.md) for content shortcuts
- Configure [Enhancement Rules](../../02-core-setup/enhancement-rules.md) for custom behavior

---

**Last Updated:** 2026-02-05
**Workflow Difficulty:** Beginner to Intermediate
**Time to Master:** 3-4 writing sessions
**Prerequisites:** Claude Desktop + AgentHub + DeepSeek-R1
