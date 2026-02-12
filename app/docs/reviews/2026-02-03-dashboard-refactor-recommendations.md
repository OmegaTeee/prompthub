Dashboard: Recommendations & Refactor Suggestions
---------------------------------------------------
**Date:** 2026-02-03
**Author:** Copilot (automated changes applied during enhancement middleware work)

Summary
-------
- This document captures recommendations for improving the AgentHub enhancement monitoring dashboard and refactor suggestions for the UI and observability pipeline.

High-priority Recommendations
-----------------------------
- **Templating / Variables:** Add variables for `env`, `instance`, `client` and `job` so operators can scope panels quickly (dev/stage/prod, instance, per-client).
- **Alerts:** Implement alerting rules (Prometheus/Alertmanager) for:
  - High failure rate: e.g., `rate(agenthub_enhancement_failures_total[5m]) > X`
  - Slow p95 latency: `histogram_quantile(0.95, ...) > SLA`
  - Sudden call-rate spikes: anomalous increases in `rate(agenthub_enhancement_calls_total[1m])`
- **Annotations:** Record deploys and config changes (e.g., toggles of `auto_enhance_mcp`) as annotations so incidents can be correlated with changes.
- **Runbook Links:** Add direct runbook links and quick mitigation steps on the dashboard (clear cache, disable auto-enhancement, restart router). Keep the runbook in the repo and link to it.

Design & Usability Improvements
------------------------------
- **Overview Row:** Add a compact top-row summary showing `Total Calls`, `Failures (1h)`, `p95 latency`, and `Rate-limited` count so critical state is visible at a glance.
- **Logical Grouping:** Re-organize panels into rows: Overview, Latency, Errors, Capacity/Rate. Keep the overview minimal for small screens.
- **Drilldowns:** Use variables and panel links to enable drilldowns by client, tool, or MCP server. Add a `client` variable to switch context quickly.
- **Color Rules & Thresholds:** Apply color thresholds on stat panels (green/amber/red) to surface unhealthy states immediately.
- **Mobile Layout:** Hide secondary graphs on narrow screens and keep the overview and alert panels visible.

Observability & Tracing
-----------------------
- **Logging Integration:** Add links/panels to log streams (Loki/ELK) filtered by `enhancement` and `client` to inspect failing requests.
- **Tracing:** If available, link to traces for slow enhancement calls (OpenTelemetry/Jaeger) for root-cause analysis.
- **SLOs & Error Budget:** If you have SLOs, encode p95 latency and failure rate SLOs into the dashboard and alert rules.

Operational / CI Improvements
-----------------------------
- **Provisioning:** Store the dashboard JSON in `deploy/grafana/provisioning/dashboards` and add a YAML provisioning file. This ensures Grafana instances are consistent and reproducible.
- **CI Validation:** Add a CI check that validates the dashboard JSON and attempts an import against a test Grafana or at least verifies JSON schema compliance.
- **Versioning:** Keep dashboard JSON in source control and increment a version or include an annotation with a git SHA on updates.

Backend & Architectural Suggestions
----------------------------------
- **Rate Limiting:** Move from in-memory limiter to a Redis-backed distributed rate limiter for multi-instance deployments. Expose Redis metrics on dashboard.
- **Metrics Labels:** Ensure Prometheus metrics include useful labels (e.g., `client`, `instance`, `tool`) to enable fine-grained filtering and aggregation without exploding cardinality.
- **Sampling & Cardinality:** Be cautious with high-cardinality labels (raw prompt text must never be a label). Use hashed/sampled client IDs only when necessary.

Example Alerts (Prometheus Rule Snippets)
----------------------------------------

```yaml
- alert: EnhancementFailuresHigh
  expr: rate(agenthub_enhancement_failures_total[5m]) > 0.1
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "Enhancement failures are high"
    description: "{{ $value }} failures/sec over 5m"

- alert: EnhancementP95Slow
  expr: histogram_quantile(0.95, sum(rate(agenthub_enhancement_duration_seconds_bucket[5m])) by (le)) > 0.5
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "Enhancement p95 latency above SLA"
    description: "p95 > 0.5s"
```

Next Steps (recommended implementation plan)
--------------------------------------------
1. Add `env`, `instance`, and `client` variables to the dashboard and re-export JSON.
2. Create Alertmanager rules for failures and latency and test them in staging.
3. Provision the dashboard and datasource mapping in `deploy/grafana/`.
4. Replace in-memory rate limiter with Redis-backed limiter and add Redis metrics panels.
5. Add CI job to validate dashboard JSON and run a smoke import against a test Grafana.

References
----------
- Grafana provisioning: <https://grafana.com/docs/grafana/latest/administration/provisioning/>
- Prometheus alerting: <https://prometheus.io/docs/alerting/latest/overview/>
- Tracing + logs integration: OpenTelemetry, Jaeger, Loki
