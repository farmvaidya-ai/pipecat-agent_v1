#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Pipecat Quickstart Example.

The example runs a simple voice AI bot that you can connect to using your
browser and speak with it. You can also deploy this bot to Pipecat Cloud.

Required AI services:
- Soniox (Speech-to-Text)/savram/deepagram
- OpenAI (LLM)/
- Cartesia (Text-to-Speech)/sarvam/

Run the bot using::

    uv run bot.py
"""

import os
import PyPDF2

from dotenv import load_dotenv
from loguru import logger

print("🚀 Starting Pipecat bot...")
print("⏳ Loading models and imports (20 seconds, first run only)\n")

logger.info("Loading Local Smart Turn Analyzer V3...")
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3

logger.info("✅ Local Smart Turn Analyzer V3 loaded")
logger.info("Loading Silero VAD model...")
from pipecat.audio.vad.silero import SileroVADAnalyzer

logger.info("✅ Silero VAD model loaded")

from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame

logger.info("Loading pipeline components...")
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from murf_tts_service import MurfTTSService  # Custom Murf integration
from pipecat.services.soniox.stt import SonioxSTTService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info(f"Starting bot")

    # STT Options: soniox, deepgram, sarvam
    stt_provider = os.getenv("STT_PROVIDER", "soniox").lower()
    
    if stt_provider == "soniox":
        stt = SonioxSTTService(
            api_key=os.getenv("SONIOX_API_KEY"),
            model=os.getenv("SONIOX_MODEL", "stt-rt-v3")
        )
    elif stt_provider == "deepgram":
        stt = DeepgramSTTService(
            api_key=os.getenv("DEEPGRAM_API_KEY")
        )
    elif stt_provider == "sarvam":
        stt = SarvamSTTService(
            api_key=os.getenv("SARVAM_API_KEY"),
            language_code="te-IN"  # Telugu
        )
    else:
        raise ValueError(f"Unknown STT provider: {stt_provider}")

    # TTS Options: murf, elevenlabs, cartesia, sarvam
    tts_provider = os.getenv("TTS_PROVIDER", "elevenlabs").lower()
    
    if tts_provider == "murf":
        tts = MurfTTSService(
            api_key=os.getenv("MURF_API_KEY"),
            voice_id="en-US-ken",  # Murf voice
            sample_rate=16000
        )
    elif tts_provider == "elevenlabs":
        tts = ElevenLabsTTSService(
            api_key=os.getenv("ELEVEN_LABS_API_KEY"),
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam - natural voice
            model="eleven_turbo_v2_5"  # Ultra-low latency
        )
    elif tts_provider == "cartesia":
        tts = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY"),
            voice_id="71a7ad14-091c-4e8e-a314-022ece01c121"  # British Reading Lady
        )
    elif tts_provider == "sarvam":
        tts = SarvamTTSService(
            api_key=os.getenv("SARVAM_API_KEY"),
            model="bulbul:v1"  # Sarvam TTS model
        )
    else:
        raise ValueError(f"Unknown TTS provider: {tts_provider}")

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    # Load knowledge base from PDF/text file
    knowledge_base = ""
    knowledge_file = os.getenv("KNOWLEDGE_FILE", "resource_document.txt")
    
    if os.path.exists(knowledge_file):
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            knowledge_base = f.read()
        logger.info(f"✅ Loaded knowledge base: {len(knowledge_base)} characters")
    else:
        logger.warning(f"⚠️  Knowledge file not found: {knowledge_file}")

    # Build system prompt with knowledge base
    system_prompt = """You are a friendly AI assistant. You must ALWAYS respond in Telugu language only. Never use English or any other language in your responses.

IMPORTANT: Answer questions ONLY based on the following knowledge base document. If the answer is not in the document, politely say you don't have that information in Telugu.

Knowledge Base:
{knowledge_base}

Instructions:
- Answer only from the above document
- Always respond in Telugu
- Be conversational and helpful
- If information is not in the document, say so honestly in Telugu
""".format(knowledge_base=knowledge_base)

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
    ]

    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            rtvi,  # RTVI processor
            stt,
            context_aggregator.user(),  # User responses
            llm,  # LLM
            tts,  # TTS
            transport.output(),  # Transport bot output
            context_aggregator.assistant(),  # Assistant spoken responses
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected: {client}")
        # Kick off the conversation.
        messages.append({"role": "system", "content": "Say hello and briefly introduce yourself."})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the bot starter."""

    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
