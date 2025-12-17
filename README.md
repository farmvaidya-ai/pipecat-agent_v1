# Pipecat Voice AI Bot - Telugu Bio-Fertilizer Assistant

A production-ready voice AI bot that provides expert guidance on bio-fertilizers and organic farming in Telugu language. Built with Pipecat framework with flexible STT/TTS provider options and knowledge base integration.

## 🎯 Features

- **Telugu-Only Responses**: AI responds exclusively in Telugu language
- **Knowledge Base Integration**: Answers based on comprehensive bio-fertilizer documentation (60K+ characters)
- **Multiple STT Providers**: Soniox, Deepgram, Sarvam
- **Multiple TTS Providers**: Murf (custom), ElevenLabs, Cartesia, Sarvam
- **WebRTC Connection**: Real-time voice communication
- **Production Ready**: Deploy to Pipecat Cloud or run locally

## 📋 Prerequisites

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd pipecat-quickstart
uv sync
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` with your API keys:

```env
# Required
OPENAI_API_KEY=your_openai_api_key

# STT Provider Keys (choose one)
SONIOX_API_KEY=your_soniox_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
SARVAM_API_KEY=your_sarvam_api_key

# TTS Provider Keys (choose one)
MURF_API_KEY=your_murf_api_key
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key
CARTESIA_API_KEY=your_cartesia_api_key

# Provider Selection
STT_PROVIDER=soniox        # Options: soniox, deepgram, sarvam
TTS_PROVIDER=elevenlabs    # Options: murf, elevenlabs, cartesia, sarvam

# Knowledge Base
KNOWLEDGE_FILE=resource_document.txt

# Optional: Daily.co for cloud deployment
DAILY_API_KEY=your_daily_api_key
```

### 3. Run the Bot

```bash
uv run bot.py
```

Open http://localhost:7860/client in your browser and click **Connect**.

## 🎤 STT Providers

| Provider | Speed | Accuracy | Best For |
|----------|-------|----------|----------|
| **Soniox** | Ultra-fast | High | Real-time conversations |
| **Deepgram** | Fast | Very High | Accuracy-critical apps |
| **Sarvam** | Fast | High | Telugu language optimization |

**Switch STT Provider:**
```bash
# In .env
STT_PROVIDER=deepgram
```

## 🔊 TTS Providers

| Provider | Latency | Quality | Best For |
|----------|---------|---------|----------|
| **Murf** | Ultra-low | High | Real-time, natural voice |
| **Cartesia** | Low | High | Balanced performance |
| **Sarvam** | Low | High | Telugu native voice |

**Switch TTS Provider:**
```bash
# In .env
TTS_PROVIDER=murf
```

**Murf Voice Options:**
- `en-US-ronnie` - Male, supports Telugu (current)
- `en-US-wayne` - Deep male
- `en-IN-priya` - Indian female

## 📚 Knowledge Base

The bot uses a comprehensive bio-fertilizer document (`resource_document.txt`) covering:
- Bio-fertilizers (NPK, Mycorrhiza, etc.)
- Organic fertilizers
- Chemical fertilizers
- Product information from Biofactor

### Update Knowledge Base

1. **From PDF:**
```bash
uv run python3 << 'EOF'
import PyPDF2

with open('your_document.pdf', 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    text = []
    for page in pdf_reader.pages:
        text.append(page.extract_text())

with open('resource_document.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(text))



Configure Murf settings in `.env`:



The bot uses a custom Murf TTS service (`murf_tts_service.py`) for streaming audio output.
**Python Packages:** Ensure `aiohttp` is installed (usually via `uv sync`). If needed: `pip install aiohttp`.

**Runtime Notes:**
- The service streams audio frames for low-latency TTS.
- Verify ffmpeg path with `which ffmpeg`.
- Test API key and voice ID validity.

**Note:** The voice ID `Karan` was invalid; updated to `en-US-ronnie` which supports Telugu.

```bash
sudo apt install ffmpeg
pip install pydub
```

Configure Murf settings in `.env`:

```env
# Murf TTS Configuration (for Telugu voice)
MURF_API_KEY=your_murf_api_key
MURF_VOICE_ID=en-US-ronnie
MURF_STYLE=Conversational
MURF_MODEL=FALCON
MURF_REGION=in
```

The bot uses a custom Murf TTS service (`murf_tts_service.py`) for streaming audio output.
**Python Packages:** Ensure `aiohttp` is installed (usually via `uv sync`). If needed: `pip install aiohttp`.

**Runtime Notes:**
- The service streams audio frames for low-latency TTS.
- Verify ffmpeg path with `which ffmpeg`.
- Test API key and voice ID validity.

**Note:** The voice ID `Karan` was invalid; updated to `en-US-ronnie` which supports Telugu.
