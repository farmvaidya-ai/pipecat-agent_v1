# Deploying Telugu Agriculture Bot to Pipecat Cloud

## Prerequisites
1. Pipecat Cloud account: https://cloud.pipecat.ai
2. Pipecat CLI installed: `pip install pipecat-ai-cli`
3. Docker installed and logged in: `docker login`
4. Docker Hub account (username: gunjesh843)

## Step 1: Set Up Your Environment

Make sure all your API keys are configured in `.env`:
```bash
# Copy from env.example if needed
cp env.example .env

# Edit .env and add your actual API keys
nano .env
```

## Step 2: Build Docker Image

```bash
# Build the Docker image (includes all dependencies)
docker build -t gunjesh843/pipecat-agent_v1:0.1 .

# Test locally (optional but recommended)
docker run --env-file .env -p 7860:7860 gunjesh843/pipecat-agent_v1:0.1

# Push to Docker Hub
docker push gunjesh843/pipecat-agent_v1:0.1
```

## Step 3: Set Secrets in Pipecat Cloud

```bash
# Log in to Pipecat Cloud
pipecat login

# Set your secret set name
SECRET_SET="pipecat-agent_v1-secrets"

# Core API Keys
pipecat secrets set --secret-set $SECRET_SET OPENAI_API_KEY="sk-..."
pipecat secrets set --secret-set $SECRET_SET SARVAM_API_KEY="your_key"

# Azure TTS Configuration
pipecat secrets set --secret-set $SECRET_SET AZURE_API_KEY="your_azure_key"
pipecat secrets set --secret-set $SECRET_SET AZURE_REGION="centralindia"
pipecat secrets set --secret-set $SECRET_SET AZURE_VOICE="te-IN-ShrutiNeural"

# Murf TTS Configuration (external package)
pipecat secrets set --secret-set $SECRET_SET MURF_API_KEY="ap2_..."
pipecat secrets set --secret-set $SECRET_SET MURF_VOICE_ID="en-IN-ravi"
pipecat secrets set --secret-set $SECRET_SET MURF_STYLE="Conversational"
pipecat secrets set --secret-set $SECRET_SET MURF_MODEL="FALCON"

# Service Provider Configuration
pipecat secrets set --secret-set $SECRET_SET STT_PROVIDER="sarvam"
pipecat secrets set --secret-set $SECRET_SET TTS_PROVIDER="azure"

# Knowledge Base
pipecat secrets set --secret-set $SECRET_SET KNOWLEDGE_FILE="resource_document.txt"
```

## Step 4: Deploy to Pipecat Cloud

```bash
# Deploy your bot
pipecat deploy

# Check deployment status
pipecat status pipecat-agent_v1

# View logs
pipecat logs pipecat-agent_v1
```

## Step 5: Test Your Deployed Bot

Once deployed, Pipecat Cloud will provide you with a URL to test your bot.

## Dependencies Installed Automatically

The Docker image includes all necessary dependencies:
- ✅ **pipecat-ai** with [azure] extras (Azure Speech SDK)
- ✅ **pipecat-murf-tts** (external Murf TTS integration)
- ✅ **azure-cognitiveservices-speech** (Azure TTS backend)
- ✅ All STT providers (Sarvam, Soniox, Deepgram)
- ✅ All LLM providers (OpenAI)
- ✅ ffmpeg for audio processing

## Monitoring & Scaling

```bash
# View metrics
pipecat metrics pipecat-agent_v1

# Scale manually (if needed)
pipecat scale pipecat-agent_v1 --min 2 --max 10

# Update deployment
pipecat deploy --update
```

## Switching Between TTS Providers

Update the `TTS_PROVIDER` secret:

```bash
# Switch to Murf
pipecat secrets set --secret-set pipecat-agent_v1-secrets TTS_PROVIDER="murf"

# Switch to Azure
pipecat secrets set --secret-set pipecat-agent_v1-secrets TTS_PROVIDER="azure"

# Redeploy to apply changes
pipecat deploy --update
```

## Troubleshooting

### Docker Build Issues
```bash
# Clean build (no cache)
docker build --no-cache -t gunjesh843/pipecat-agent_v1:0.1 .

# Check if all files are included
docker run gunjesh843/pipecat-agent_v1:0.1 ls -la
```

### Missing Dependencies
The Dockerfile uses `uv sync --locked` which installs ALL dependencies from `pyproject.toml`:
- Murf: `pipecat-murf-tts>=0.1.2`
- Azure: `pipecat-ai[azure]` (includes azure-cognitiveservices-speech)
- All other services are included in the main pipecat-ai package

### Bot not starting
- Check logs: `pipecat logs pipecat-agent_v1`
- Verify secrets: `pipecat secrets list --secret-set pipecat-agent_v1-secrets`
- Ensure Docker image is pushed: `docker pull gunjesh843/pipecat-agent_v1:0.1`

### Azure TTS Errors
- Verify region is correct: `centralindia` (not `southindia`)
- Check API key has Speech Services enabled
- Test locally first: `docker run --env-file .env -p 7860:7860 gunjesh843/pipecat-agent_v1:0.1`

### Murf TTS Not Working
- Verify API key format: `ap2_...`
- Check voice ID exists: `en-IN-ravi` for Indian English
- Ensure MODEL is set: `FALCON` for low latency

## Updating the Bot

```bash
# 1. Make changes to bot.py or resources
# 2. Increment version in pcc-deploy.toml
# 3. Build and push new image
docker build -t gunjesh843/pipecat-agent_v1:0.2 .
docker push gunjesh843/pipecat-agent_v1:0.2

# 4. Update pcc-deploy.toml image version to 0.2
# 5. Redeploy
pipecat deploy --update
```

## Cost Optimization

- Use `agent-1x` for development, `agent-2x` for production
- Set `min_agents=0` for dev (cold start delay acceptable)
- Monitor usage: `pipecat billing`
- Use Azure TTS (lower cost than Murf for production scale)
- Sarvam STT is India-based (lower latency)

## Pre-Deployment Checklist

- [x] All dependencies in pyproject.toml (including pipecat-murf-tts)
- [x] Dockerfile installs ffmpeg
- [x] Docker username updated to gunjesh843
- [x] pcc-deploy.toml configured correctly
- [x] All secrets documented
- [x] resource_document.txt copied in Dockerfile
- [ ] Test Docker build locally
- [ ] Push image to Docker Hub
- [ ] Set all secrets in Pipecat Cloud
- [ ] Deploy and test

## Support

- Pipecat Docs: https://docs.pipecat.ai
- Discord: https://discord.gg/pipecat
- GitHub: https://github.com/pipecat-ai/pipecat
