# AGENTS

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Invoke: Bash("openskills read <skill-name>")
- The skill content will load with detailed instructions on how to complete the task
- Base directory provided in output for resolving bundled resources (references/, scripts/, assets/)

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
- Each skill invocation is stateless
</usage>

<available_skills>

<skill>
<name>artifacts-builder</name>
<description>Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.</description>
<location>global</location>
</skill>

<skill>
<name>backend-development</name>
<description>APIs, databases, server architecture patterns.</description>
<location>global</location>
</skill>

<skill>
<name>brand-guidelines</name>
<description>Apply brand colors and typography to artifacts. Use when brand colors, style guidelines, visual formatting, or company design standards apply. Ensures consistency across branded content.</description>
<location>global</location>
</skill>

<skill>
<name>canvas-design</name>
<description>Create beautiful visual art in .png and .pdf documents using design philosophy. Use when the user asks to create a poster, piece of art, design, or other static visual piece. Creates original visual designs.</description>
<location>global</location>
</skill>

<skill>
<name>changelog-generator</name>
<description>Automatically creates user-facing changelogs from git commits by analyzing commit history, categorizing changes, and transforming technical commits into clear, customer-friendly release notes. Turns hours of manual changelog writing into minutes of automated generation.</description>
<location>global</location>
</skill>

<skill>
<name>code-documentation</name>
<description>Writing effective code documentation - API docs, README files, inline comments, and technical guides. Use for documenting codebases, APIs, or writing developer guides.</description>
<location>global</location>
</skill>

<skill>
<name>code-refactoring</name>
<description>Code refactoring patterns and techniques for improving code quality without changing behavior. Use for cleaning up legacy code, reducing complexity, or improving maintainability.</description>
<location>global</location>
</skill>

<skill>
<name>code-review</name>
<description>Automated PR review patterns for thorough, constructive code reviews.</description>
<location>global</location>
</skill>

<skill>
<name>content-research-writer</name>
<description>Assists in writing high-quality content by conducting research, adding citations, improving hooks, iterating on outlines, and providing real-time feedback on each section. Transforms your writing process from solo effort to collaborative partnership.</description>
<location>global</location>
</skill>

<skill>
<name>database-design</name>
<description>Database schema design, optimization, and migration patterns for PostgreSQL, MySQL, and NoSQL databases. Use for designing schemas, writing migrations, or optimizing queries.</description>
<location>global</location>
</skill>

<skill>
<name>developer-growth-analysis</name>
<description>Analyzes your recent Claude Code chat history to identify coding patterns, development gaps, and areas for improvement, curates relevant learning resources from HackerNews, and automatically sends a personalized growth report to your Slack DMs.</description>
<location>global</location>
</skill>

<skill>
<name>doc-coauthoring</name>
<description>Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers. Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks.</description>
<location>global</location>
</skill>

<skill>
<name>docx</name>
<description>Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When Claude needs to work with professional documents (.docx files) for creating new documents, modifying content, working with tracked changes, or adding comments.</description>
<location>global</location>
</skill>

<skill>
<name>domain-name-brainstormer</name>
<description>Generates creative domain name ideas for your project and checks availability across multiple TLDs (.com, .io, .dev, .ai, etc.). Saves hours of brainstorming and manual checking.</description>
<location>global</location>
</skill>

<skill>
<name>fontforge</name>
<description>Font management toolkit for listing, analyzing, renaming, and converting font files. Use when working with font files (TTF, OTF, WOFF2, TTC), font metrics, font conversion, or font organization tasks. Handles batch operations across font families.</description>
<location>global</location>
</skill>

<skill>
<name>hygiene</name>
<description>></description>
<location>global</location>
</skill>

<skill>
<name>job-application</name>
<description>Write tailored cover letters and job applications using your CV and preferred style</description>
<location>global</location>
</skill>

<skill>
<name>llm-application-dev</name>
<description>Building applications with Large Language Models - prompt engineering, RAG patterns, and LLM integration. Use for AI-powered features, chatbots, or LLM-based automation.</description>
<location>global</location>
</skill>

<skill>
<name>mcp-builder</name>
<description>Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools.</description>
<location>global</location>
</skill>

<skill>
<name>python-development</name>
<description>Modern Python development with Python 3.12+, Django, FastAPI, async patterns, and production best practices. Use for Python projects, APIs, data processing, or automation scripts.</description>
<location>global</location>
</skill>

<skill>
<name>qa-regression</name>
<description>Automate QA regression testing with reusable test skills. Create login flows, dashboard checks, user creation, and other common test scenarios that run consistently.</description>
<location>global</location>
</skill>

<skill>
<name>skill-creator</name>
<description>Guide for creating new agent skills that follow the Agent Skills specification.</description>
<location>global</location>
</skill>

<skill>
<name>webapp-testing</name>
<description>Browser automation and testing with Playwright.</description>
<location>global</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
