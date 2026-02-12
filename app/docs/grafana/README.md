AgentHub Grafana Dashboard
==========================

Import: Use Grafana >> Dashboards >> Import and upload `agenthub-enhancement-dashboard.json` or provision it.

Prometheus datasource: Ensure you have a Prometheus datasource configured and select it when importing. The example uses Prometheus expressions:

- `rate(agenthub_enhancement_calls_total[1m])` — calls per second
- `rate(agenthub_enhancement_failures_total[5m])` — failures per second
- `histogram_quantile(0.95, sum(rate(agenthub_enhancement_duration_seconds_bucket[5m])) by (le))` — p95 latency
- `sum(rate(agenthub_enhancement_duration_seconds_sum[5m])) / sum(rate(agenthub_enhancement_duration_seconds_count[5m]))` — avg duration

Recommendations for improving the dashboard and usability
---------------------------------------------------------

- Templating & Variables: Add a `job` or `instance` variable so users can scope panels to a single router instance or environment (dev/staging/prod).
- Alerts: Create alert rules for:
  - High failure rate (e.g., failures/sec > threshold)
  - Slow p95 latency above SLA (e.g., p95 > 0.5s)
  - Sudden spikes in calls (possible abuse)
- Annotations: Use annotations for deploy events and configuration changes (e.g., `auto_enhance_mcp` toggles) to correlate behavior changes with incidents.
- Runbooks & Links: Add panel links to a short runbook (playbook) describing what to check and mitigation steps (clear cache, disable enhancement, restart service).
- Logging Integration: Add a Logs panel or direct link to the ELK/ Loki stream filtered by `enhancement` and `client` so operators can inspect failing requests.
- Provisioning: Store the dashboard JSON under `deploy/grafana/provisioning/dashboards` and add a Grafana `datasource` provisioning file to enable automatic deployment.
- Version & CI: Keep the dashboard JSON in source control, and add a lightweight CI check that imports the JSON against a test Grafana (or validates JSON schema) to catch regressions.

Design/Refactor suggestions for the dashboard UI
-----------------------------------------------

- Layout: Group panels by purpose (Overview row with totals/stats, Latency row, Failure/Errors row, Capacity/Rate row).
- Compact summary: Add a single-row summary at the top with `Total calls`, `Failures (1h)`, `p95 latency`, `Rate-limited` (if available).
- Drilldowns: Use panel links to drill into per-client or per-tool views. Include a `client` variable to switch context quickly.
- Color coding: Use thresholds and color rules to highlight unhealthy states (red for failures, amber for slow latency).
- Mobile-friendly: Keep important alerts and the summary stat panels visible on narrow screens; hide detailed graphs in a secondary tab.

Advanced:

- SLOs & Error Budget: If you have service-level objectives, encode p95 latency and failure-rate SLOs into panels and alerting.
- Distributed rate limiting: If you move from in-memory to Redis, add panels showing Redis token usage, misses, and node health.
- Sampling traces: If you instrument with OpenTelemetry, add a panel linking to traces for slow enhancement calls.

Quick commands
--------------

Import via Grafana CLI (example):

```bash
grafana-cli admin import-dashboard /path/to/agenthub-enhancement-dashboard.json
```

Provisioning (example): Add the JSON to Grafana provisioning directory and a YAML mapping file.
