# Deploying Telugu Agriculture Bot to Pipecat Cloud

## Prerequisites
1. Pipecat Cloud account: https://cloud.pipecat.ai
2. Pipecat CLI installed: `pip install pipecat-ai-cli`
3. Docker installed for building images

## Step 1: Set Up Your Environment

Make sure all your API keys are configured in `.env`:
```bash
# Copy from env.example if needed
cp env.example .env

# Edit .env and add your actual API keys
nano .env
```

## Step 2: Update pcc-deploy.toml

Edit `pcc-deploy.toml` and update:
1. `image`: Replace `your_username` with your Docker Hub username
2. Review `agent_profile` (agent-2x is recommended for production)
3. Adjust `min_agents` and `max_agents` based on expected load

## Step 3: Set Secrets in Pipecat Cloud

```bash
# Log in to Pipecat Cloud
pipecat login

# Set your secret set name
SECRET_SET="telugu-agri-bot-secrets"

# Set required secrets
pipecat secrets set --secret-set $SECRET_SET OPENAI_API_KEY="your_key"
pipecat secrets set --secret-set $SECRET_SET SARVAM_API_KEY="your_key"
pipecat secrets set --secret-set $SECRET_SET AZURE_API_KEY="your_key"
pipecat secrets set --secret-set $SECRET_SET AZURE_REGION="centralindia"
pipecat secrets set --secret-set $SECRET_SET AZURE_VOICE="te-IN-ShrutiNeural"
pipecat secrets set --secret-set $SECRET_SET STT_PROVIDER="sarvam"
pipecat secrets set --secret-set $SECRET_SET TTS_PROVIDER="azure"
pipecat secrets set --secret-set $SECRET_SET KNOWLEDGE_FILE="resource_document.txt"
```

## Step 4: Build and Push Docker Image

```bash
# Build the Docker image
docker build -t your_username/telugu-agri-bot:0.1 .

# Test locally (optional)
docker run --env-file .env -p 7860:7860 your_username/telugu-agri-bot:0.1

# Push to Docker Hub
docker push your_username/telugu-agri-bot:0.1
```

## Step 5: Deploy to Pipecat Cloud

```bash
# Deploy your bot
pipecat deploy

# Check deployment status
pipecat status telugu-agri-bot

# View logs
pipecat logs telugu-agri-bot
```

## Step 6: Test Your Deployed Bot

Once deployed, Pipecat Cloud will provide you with a URL to test your bot.

## Monitoring & Scaling

```bash
# View metrics
pipecat metrics telugu-agri-bot

# Scale manually (if needed)
pipecat scale telugu-agri-bot --min 2 --max 10

# Update deployment
pipecat deploy --update
```

## Troubleshooting

### Bot not starting
- Check logs: `pipecat logs telugu-agri-bot`
- Verify secrets are set: `pipecat secrets list --secret-set telugu-agri-bot-secrets`
- Ensure Docker image is pushed and accessible

### High latency
- Check Azure region (`centralindia` is closest to India)
- Upgrade to `agent-4x` profile for better performance
- Enable caching in OpenAI API calls

### Knowledge base not loading
- Verify `resource_document.txt` is included in Docker image
- Check file path in Dockerfile COPY command
- Ensure KNOWLEDGE_FILE environment variable is set

## Updating the Bot

```bash
# 1. Make changes to bot.py or resources
# 2. Build new image with incremented version
docker build -t your_username/telugu-agri-bot:0.2 .
docker push your_username/telugu-agri-bot:0.2

# 3. Update pcc-deploy.toml image version
# 4. Redeploy
pipecat deploy --update
```

## Cost Optimization

- Use `agent-1x` for development, `agent-2x` for production
- Set `min_agents=0` for dev environments (cold start delay)
- Monitor usage: `pipecat billing`
- Use caching for OpenAI responses
- Consider Sarvam TTS (Indian service, lower latency)

## Support

- Pipecat Docs: https://docs.pipecat.ai
- Discord: https://discord.gg/pipecat
- GitHub: https://github.com/pipecat-ai/pipecat
