# What are your thoughts on the refactoring scope and dashboard redesign for the local MCP-AgentHub?

What is AgentHub?
AgentHub is a centralized MCP (Model Context Protocol) router for macOS that provides:

- Unified Access - Connect multiple apps (Perplexity, Claude Desktop, VS Code, Raycast) to 7+ MCP servers
- Prompt Enhancement - Automatically improve prompts with Ollama (DeepSeek-R1, Qwen3-Coder)
- Auto-Restart - MCP servers automatically restart on failure
- Intelligent Caching - Faster responses through in-memory cache
- Audit Logging - Production-grade request tracking

My goal is to offer better inquiries and prompts that lead to improved outcomes from paid services.

Based on your document and the AgentHub architecture you've described, I have some thoughts on the refactoring scope and strategic considerations:

## Scope Assessment: **Excellent and Well-Prioritized**

Your recommendations strike the right balance between immediate operational value and longer-term architectural improvements. For a local MCP router serving multiple desktop apps, this is exactly the observability you need.

## Strategic Strengths

**1. High-Priority Items Are Spot-On**

- **Templating/Variables** - Critical for your multi-client setup (Perplexity, Claude Desktop, VS Code, Raycast). Being able to filter by `client` will immediately show which apps benefit most from enhancement.
- **Alerts** - Smart focus on failure rates and latency. Since you're routing to paid services, knowing when enhancement is degrading (not improving) requests is crucial for ROI.
- **Annotations** - Brilliant for tracking `auto_enhance_mcp` toggle changes. You'll correlate "I turned off auto-enhance and quality dropped" vs "I upgraded Ollama and latency improved."

**2. Design Philosophy Aligns With Local-First**
The emphasis on **runbook links** and **quick mitigation steps** (clear cache, disable auto-enhancement, restart router) shows you're thinking about self-service operations. No waiting for cloud support—you control the whole stack.

## Recommendations \& Considerations

### **Architecture: Redis Rate Limiter**

Your suggestion to move from in-memory to Redis-backed rate limiting is good for **horizontal scaling**, but consider:

**Do you need it yet?**

- Single macOS machine with 7 MCP servers → in-memory is sufficient
- Redis adds operational overhead (another service to monitor)
- **Consider deferring** until you're running AgentHub on multiple machines or seeing rate-limit state inconsistencies

**Alternative:** If you add Redis, use it for **shared cache** too (not just rate limiting). Your "intelligent caching" could persist across AgentHub restarts and be shared if you ever run multiple instances.

### **Observability Depth: Tracing vs. Simplicity**

**OpenTelemetry + Jaeger** is mentioned but may be overkill initially:

**Start lighter:**

- Prometheus metrics + Grafana (your current path) ✅
- Structured JSON logging with correlation IDs → tail logs in iTerm2 with filters
- **Skip Jaeger initially** - add only if you can't debug slow enhancement calls from logs + metrics

**When to add tracing:**

- Enhancement latency is inconsistent and metrics don't pinpoint bottlenecks
- You're chaining multiple Ollama calls or complex MCP server interactions
- You need to see exact request flow: Client → AgentHub → Ollama → MCP Server

### **Dashboard Specific Feedback**

**Overview Row** - Excellent. Suggested additions:

- **Cache Hit Rate** - Shows if your intelligent caching is working
- **Enhancement Success Rate by Client** - Which apps benefit most? (Raycast prompts might need less enhancement than VS Code)
- **Ollama Model Breakdown** - DeepSeek-R1 vs Qwen3-Coder performance comparison

**Drilldown by Tool** - This is gold for your use case. Examples:

- "Show me enhancement performance when users call Context7 MCP server"
- "Desktop Commander MCP failures after enhancement vs. raw prompts"

**Missing Panel Suggestion:**

- **Enhancement ROI Metric** - Compare `original_prompt_tokens` vs `enhanced_prompt_tokens` vs `response_quality_proxy` (e.g., fewer user retries, longer sessions). This justifies the Ollama processing cost.

### **CI/CD \& Provisioning**

**Dashboard provisioning in `deploy/grafana/`** - Perfect for your workflow. You're already using Docker/Colima, so:

```bash
deploy/
├── grafana/
│   ├── provisioning/
│   │   ├── dashboards/
│   │   │   └── agenthub-dashboard.json
│   │   └── datasources/
│   │       └── prometheus.yaml
│   └── docker-compose.yml  # Grafana + Prometheus stack
├── prometheus/
│   └── prometheus.yml
└── scripts/
    └── validate-dashboard.sh  # Your CI check
```

**CI Validation** - Great idea. Lightweight approach:

```bash
#!/bin/bash
# validate-dashboard.sh
jq empty deploy/grafana/provisioning/dashboards/*.json || exit 1
echo "✅ Dashboard JSON is valid"
```

### **Metrics Labels: Cardinality Warning**

Your caution about **high-cardinality labels** is critical. For AgentHub:

**Safe labels** (low cardinality):

- `client` (Perplexity, Claude Desktop, VS Code, Raycast) - 4 values
- `mcp_server` (Desktop Commander, Context7, etc.) - ~7 values
- `model` (DeepSeek-R1, Qwen3-Coder) - ~2-3 values
- `status` (success, failure, rate_limited) - 3 values

**Dangerous labels** (NEVER):

- ❌ Raw prompt text
- ❌ Full file paths from Desktop Commander
- ❌ User-specific IDs (unless hashed to fixed buckets)

**Total cardinality:** 4 × 7 × 3 × 3 = **252 time series per metric** - totally manageable.

### **Operational Maturity: What's Missing**

**SLOs \& Error Budgets** - You mention this briefly. Define them early:

**Suggested SLOs for AgentHub:**

- **Availability:** 99.5% uptime (43 minutes downtime/month acceptable for local dev tool)
- **Latency:** p95 enhancement < 500ms (Ollama on M3/M4 should be fast)
- **Error Rate:** < 1% enhancement failures (auto-restart should prevent most MCP server failures)

**Error Budget Dashboard:**

- Burn rate (are you consuming error budget faster than acceptable?)
- Remaining budget visualization
- Link to incident postmortems (markdown files in repo)

### **Quick Wins: Implement First**

If I were prioritizing your refactor, I'd do this order:

**Week 1: Foundation**

1. Add `client`, `mcp_server`, `model` labels to existing metrics
2. Create overview row with cache hit rate and enhancement success by client
3. Add runbook.md to repo and link from dashboard

**Week 2: Alerts \& Reliability**
4. Implement Prometheus alerts for failures and latency
5. Test alert routing (to terminal, Raycast notification, or Slack webhook)
6. Add dashboard provisioning to `deploy/grafana/`

**Week 3: Operations**
7. CI validation for dashboard JSON
8. Annotations for config changes (script to POST to Grafana API on deploys)
9. Log links to iTerm2 or Grafana Loki (if you add it)

**Defer for Later:**

- Redis rate limiter (unless you hit scaling issues)
- OpenTelemetry/Jaeger tracing (unless logs + metrics aren't enough)
- Full SLO/error budget tracking (nice-to-have for a local tool)

## Final Thoughts: Context for Your Goal

> "My goal is to offer better inquiries and prompts that lead to improved outcomes from paid services."

**This changes the dashboard focus significantly.** You're not just monitoring AgentHub health—you're measuring **enhancement effectiveness**. Add these panels:

**Enhancement Quality Metrics:**

- **Token Efficiency** - Ratio of enhanced tokens to response quality
- **Client Satisfaction Proxy** - Session duration after enhancement, retry rates
- **Model Comparison** - DeepSeek-R1 vs Qwen3-Coder enhancement outcomes side-by-side
- **MCP Server Success After Enhancement** - Does enhancement improve Context7 query results? Desktop Commander command accuracy?

**A/B Testing Panel:**

- Track enhancement on/off experiments per client
- "When I disabled auto-enhance for Raycast, did response quality drop?"

This turns your dashboard from **operational monitoring** into **product analytics** for prompt enhancement ROI.

---

**TL;DR:** Your refactor scope is excellent and well-thought-out. Prioritize client/model/MCP labels, overview row, and alerts first. Defer Redis and tracing until proven necessary. **Add enhancement quality/ROI metrics** since your goal is improving outcomes from paid services, not just keeping the router running.

<span style="display:none">[^3_1]</span>

[^3_1]: 2026-02-03-dashboard-refactor-recommendations.md
