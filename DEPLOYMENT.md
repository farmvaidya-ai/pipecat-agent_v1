# Production Deployment Guide

## 🚀 Quick Deploy Options

### Option 1: Pipecat Cloud (Recommended)
Easiest deployment with built-in scaling and monitoring.

```bash
# 1. Build and push Docker image
docker build -t your-registry/telugu-bot:latest .
docker push your-registry/telugu-bot:latest

# 2. Upload secrets
pipecat cloud secrets set telugu-bot-secrets --file .env

# 3. Update pcc-deploy.toml
# Set: image = "your-registry/telugu-bot:latest"

# 4. Deploy
pipecat cloud deploy
```

**Access:** https://pipecat.daily.co/

---

### Option 2: Custom Cloud (AWS/GCP/Azure)

#### Using Docker Compose

```bash
# 1. Create docker-compose.yml
docker compose up -d

# 2. Access via load balancer
# https://your-domain.com
```

#### Using Kubernetes

```bash
# 1. Apply secrets
kubectl create secret generic telugu-bot-secrets --from-env-file=.env

# 2. Deploy
kubectl apply -f k8s/

# 3. Expose service
kubectl expose deployment telugu-bot --type=LoadBalancer --port=7860
```

---

## 🔧 Production Considerations

### 1. **Scalability**
- **WebSocket Connections:** Each bot instance handles 1 concurrent user
- **Scaling Strategy:** Horizontal scaling with load balancer
- **Auto-scaling:** Based on active connections (min_agents in pcc-deploy.toml)

```toml
[scaling]
min_agents = 2      # Minimum instances
max_agents = 100    # Scale up to 100 concurrent users
```

### 2. **API Rate Limits**

| Service | Rate Limit | Cost Optimization |
|---------|------------|-------------------|
| Soniox STT | Check your plan | Use language_identification only when needed |
| Murf TTS | WebSocket streaming | FALCON model = lower latency |
| OpenAI LLM | 3,500 RPM (tier 1) | Cache system prompts, use gpt-4o-mini |

**Recommendations:**
- Monitor API usage via provider dashboards
- Implement request queuing for burst traffic
- Set up alerts for quota thresholds (80%, 90%)

### 3. **Security**

**API Keys:**
```bash
# Use secrets management (not .env in production)
# AWS Secrets Manager / GCP Secret Manager / Azure Key Vault

# Pipecat Cloud
pipecat cloud secrets set telugu-bot-secrets \
  --key OPENAI_API_KEY=sk-... \
  --key MURF_API_KEY=ap2_... \
  --key SONIOX_API_KEY=3b9...
```

**Network Security:**
- Enable HTTPS/WSS only
- Use VPC/Private networks
- Implement rate limiting (Cloudflare, API Gateway)
- Add authentication for bot access

### 4. **Monitoring & Logging**

**Metrics to Track:**
- Response latency (STT → LLM → TTS)
- Connection success rate
- API error rates
- Concurrent users
- Audio quality metrics

**Tools:**
```python
# Add to bot.py:
# - Prometheus metrics
# - Sentry error tracking
# - Custom loguru handlers to cloud logging

from prometheus_client import Counter, Histogram
requests_total = Counter('bot_requests_total', 'Total requests')
response_time = Histogram('bot_response_seconds', 'Response time')
```

### 5. **Cost Optimization**

**Estimated Costs (per hour of conversation):**
- Soniox STT: ~$0.012/min = $0.72/hour
- Murf TTS: ~$0.02/min = $1.20/hour
- OpenAI (gpt-4o-mini): ~$0.005/1K tokens ≈ $0.10/hour
- **Total: ~$2/hour per active user**

**Optimization Tips:**
1. Use `gpt-4o-mini` instead of `gpt-4` (60% cheaper)
2. Enable `enable_language_identification` only if multilingual
3. Cache LLM responses for common questions
4. Use FALCON model for Murf (lower latency = faster = cheaper)
5. Implement session timeouts (e.g., 5 minutes idle)

### 6. **Performance**

**Current Latency Breakdown:**
```
User speaks → Soniox STT → OpenAI LLM → Murf TTS → User hears
   ~200ms        ~500ms        ~800ms      ~300ms    = 1.8s
```

**Optimizations:**
- ✅ WebSocket streaming (Murf TTS) - instant audio playback
- ✅ FALCON model - ultra-low latency
- ⚠️ Consider edge deployment for regional users (India region)
- ⚠️ Use CDN for static assets

### 7. **Reliability**

**Error Handling:**
```python
# Already implemented:
- Automatic WebSocket reconnection (Murf TTS)
- API retry logic (built into pipecat)
- Graceful degradation (error frames)

# Add:
- Circuit breakers for external APIs
- Fallback voices if preferred unavailable
- Health check endpoints
```

**Health Checks:**
```bash
# Add to bot.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "stt": await check_soniox(),
            "llm": await check_openai(),
            "tts": await check_murf()
        }
    }
```

---

## 📊 Architecture Diagram

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ WebRTC
       ▼
┌─────────────────────────────────────────┐
│          Load Balancer (HTTPS)          │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│  Bot Pod 1  │  │  Bot Pod 2  │ ... (Auto-scaled)
│             │  │             │
│ ┌─────────┐ │  │ ┌─────────┐ │
│ │ Soniox  │◄┼──┼─┤  STT    │ │ (WebSocket)
│ │  STT    │ │  │ └─────────┘ │
│ └─────────┘ │  │             │
│      │      │  │ ┌─────────┐ │
│      ▼      │  │ │ OpenAI  │ │
│ ┌─────────┐ │  │ │  LLM    │◄┼─ (HTTP/2)
│ │Knowledge│ │  │ └─────────┘ │
│ │  Base   │ │  │      │      │
│ └─────────┘ │  │      ▼      │
│      │      │  │ ┌─────────┐ │
│      ▼      │  │ │  Murf   │ │
│ ┌─────────┐ │  │ │  TTS    │◄┼─ (WebSocket)
│ │  Murf   │ │  │ └─────────┘ │
│ │  TTS    │ │  │             │
│ └─────────┘ │  └─────────────┘
└─────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│     External APIs (Secrets Manager)     │
│  • Soniox API  • OpenAI API  • Murf API │
└─────────────────────────────────────────┘
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t ${{ secrets.REGISTRY }}/telugu-bot:${{ github.sha }} .
      
      - name: Push to registry
        run: docker push ${{ secrets.REGISTRY }}/telugu-bot:${{ github.sha }}
      
      - name: Deploy to Pipecat Cloud
        run: |
          pipecat cloud auth login --token ${{ secrets.PIPECAT_TOKEN }}
          pipecat cloud deploy --image ${{ secrets.REGISTRY }}/telugu-bot:${{ github.sha }}
```

---

## 📝 Environment Variables (Production)

```bash
# .env.production
OPENAI_API_KEY=sk-proj-...
SONIOX_API_KEY=...
MURF_API_KEY=ap2_...
DEEPGRAM_API_KEY=...

# Service configuration
STT_PROVIDER=soniox
TTS_PROVIDER=murf
SONIOX_MODEL=stt-rt-v3
MURF_VOICE_ID=en-IN-ravi
MURF_MODEL=FALCON
MURF_REGION=in

# Knowledge base
KNOWLEDGE_FILE=resource_document.txt

# Production settings
LOG_LEVEL=INFO
METRICS_ENABLED=true
SENTRY_DSN=https://...
```

---

## 🎯 Deployment Checklist

- [ ] Update Dockerfile with ffmpeg
- [ ] Configure secrets in cloud provider
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Enable error tracking (Sentry)
- [ ] Configure auto-scaling rules
- [ ] Set up CI/CD pipeline
- [ ] Add health check endpoints
- [ ] Configure HTTPS/WSS
- [ ] Test with production API keys
- [ ] Set up alerts (PagerDuty/Opsgenie)
- [ ] Document runbook for incidents
- [ ] Load test with expected traffic
- [ ] Configure backups for knowledge base
- [ ] Set up cost alerts (AWS Budgets)

---

## 🆘 Troubleshooting

### Common Production Issues

**1. High Latency**
```bash
# Check region proximity
# India users → MURF_REGION=in
# US users → MURF_REGION=global

# Monitor metrics
curl http://localhost:7860/metrics
```

**2. WebSocket Disconnections**
```bash
# Check load balancer timeout settings
# Ensure timeout > 300 seconds for idle connections

# Add reconnection logs
grep "WebSocket" /var/log/bot.log
```

**3. API Rate Limits**
```bash
# Implement exponential backoff
# Add request queuing
# Monitor API dashboards
```

---

## 📞 Support

- **Pipecat Discord:** https://discord.gg/pipecat
- **Murf Support:** support@murf.ai
- **Your Repo Issues:** https://github.com/farmvaidya-ai/pipecat-agent_v1/issues

