# Core Setup

**Essential configuration and advanced features for AgentHub**

Configure AgentHub to start automatically, store credentials securely, and leverage advanced resilience and enhancement features.

## Guides in This Section

### Essential Setup
1. **[LaunchAgent](launchagent.md)** - Auto-start AgentHub on login (10 min)
   - macOS LaunchAgent configuration
   - Start/stop/status commands
   - Troubleshooting startup issues

2. **[Keychain](keychain.md)** - Secure credential storage (10 min)
   - macOS Keychain integration
   - Store API keys securely
   - Access credentials from MCP servers

### Alternative Deployment
3. **[Docker](docker.md)** - Run AgentHub in Docker (15 min)
   - Docker Compose setup
   - Container configuration
   - Volume mounting for configs

### Advanced Features
4. **[Circuit Breaker](circuit-breaker.md)** - Resilience and fault tolerance (15 min)
   - Circuit breaker pattern fundamentals
   - State transitions (CLOSED → OPEN → HALF_OPEN)
   - Configuration tuning and monitoring

5. **[Enhancement Rules](enhancement-rules.md)** - Prompt enhancement configuration (15 min)
   - Per-client model selection (DeepSeek-R1, Qwen3-Coder, llama3.2)
   - Custom system prompts
   - Enhancement testing and optimization

6. **[Audit Logging](audit-logging.md)** - Security and compliance (15 min)
   - Structured audit trails
   - Activity log querying
   - Security alert system
   - HIPAA/SOC 2/GDPR compliance

## Recommended Path

### For Most Users
1. **Start here:** LaunchAgent + Keychain (essential)
2. **Then read:** Circuit Breaker (understand resilience)
3. **Optional:** Enhancement Rules (customize AI behavior)

### For Advanced Users
- **DevOps/SRE:** Docker + Circuit Breaker + Audit Logging
- **Security Teams:** Keychain + Audit Logging
- **AI Engineers:** Enhancement Rules + Audit Logging

---

**Estimated Time:** 10-60 minutes (depending on path)
**Difficulty:** Beginner to Advanced
**Prerequisites:** Completed [01-getting-started](../01-getting-started/)
