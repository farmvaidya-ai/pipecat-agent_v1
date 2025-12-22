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
from pipecat_murf_tts import MurfTTSService  # Official Murf integration
from pipecat.services.soniox.stt import SonioxSTTService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.services.azure.tts import AzureTTSService
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
            # language_hints=["te", "en", "hi"]
        )
    elif stt_provider == "deepgram":
        stt = DeepgramSTTService(
            api_key=os.getenv("DEEPGRAM_API_KEY")
        )
    elif stt_provider == "sarvam":
        stt = SarvamSTTService(
            api_key=os.getenv("SARVAM_API_KEY"),
            # language_code="te-IN"  # Telugu
        )
    else:
        raise ValueError(f"Unknown STT provider: {stt_provider}")

    # TTS Options: murf, elevenlabs, cartesia, sarvam
    tts_provider = os.getenv("TTS_PROVIDER", "elevenlabs").lower()
    
    if tts_provider == "murf":
        # Create aiohttp session for streaming
        import aiohttp
        session = aiohttp.ClientSession()
        
        tts = MurfTTSService(
            api_key=os.getenv("MURF_API_KEY"),
            params=MurfTTSService.InputParams(
                voice_id=os.getenv("MURF_VOICE_ID", "en-IN-ravi"),
                style=os.getenv("MURF_STYLE", "Conversational"),
                model=os.getenv("MURF_MODEL", "FALCON"),
                sample_rate=16000,
                format="PCM",
                channel_type="MONO"
            )
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
            target_language_code="te-IN",
            voice_id="manisha",  #female voices : manisha, vidya, anushka, arya,    male voices : abhilash, karun, hitesh 
            model="bulbul:v2",  # Sarvam TTS model
            enable_preprocessing=True,
            speech_sample_rate=22050,
            pitch=0,        # Range: -1 to 1
            pace=1,         # Range: 0.3 to 3
            loudness=1       # Range: 0.1 to 3        
            
        )
    elif tts_provider == "azure":
        tts = AzureTTSService(
            api_key=os.getenv("AZURE_API_KEY"),
            region=os.getenv("AZURE_REGION", "eastus"),
            voice=os.getenv("AZURE_VOICE", "te-IN-ShrutiNeural"),
            sample_rate=24000,
            params=AzureTTSService.InputParams(
            rate="1.05",  # Normal speed
            pitch=None,   # Default pitch
            style=None    # You can set styles like "cheerful" if supported
        )
        )
    else:
        raise ValueError(f"Unknown TTS provider: {tts_provider}")

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"),
                           stream=True #this will enable the streaming in chunks and reduce the latency
                           )

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
    system_prompt = """You are a friendly Telugu AI assistant. You must ALWAYS respond in Telugu language only. Never use English or any other language in your responses.

    IMPORTANT:
    - Aim for 15 to 30 words per response.
    - Never exceed 35 words unless the user asks for more.
    - Answer questions ONLY based on the following knowledge base document.
    - Use previous user messages in this conversation to understand context, intent, and continuity.
    - Do NOT introduce information that is not present in the knowledge base.

    Conversational Memory & Context:
    - Treat this as an ongoing conversation, not a single question
    - Remember and use past user messages to understand what the user is referring to
    - If the user asks a follow-up question, connect it to previous questions naturally
    - Do NOT ask the user to repeat information already provided earlier

    Clarification Behavior:
    - If the user's question is incomplete, vague, or depends on missing details, politely ask a follow-up question in Telugu
    - Ask only what is necessary to continue the conversation
    - Do not guess or hallucinate missing information

    Knowledge Base:
    {knowledge_base}

    Rules you must strictly follow:
    1. Respond ONLY in pure Telugu (Unicode Telugu script).
    2. Do NOT use any English words, letters, numbers, symbols, emojis, or bullet points.
    3. Use natural spoken Telugu as used in phone conversations.
    4. Keep sentences short and clear.
    5. Use simple farmer-friendly agricultural language.
    6. Always include proper punctuation like commas, full stops, and question marks.
    7. If numbers or quantities are needed, write them fully in Telugu words.
    8. Avoid headings, lists, or markdown formatting.
    
    Response Rules:
    - Always respond in Telugu only
    - Be conversational, polite, and helpful
    - Answer strictly from the knowledge base
    - If the information is not found in the document, clearly say you do not have that information (in Telugu)
    - If clarification is required, ask a question instead of answering
    - If the knowledge base contains non-Telugu words or phrases, rewrite them in Telugu without changing the meaning
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