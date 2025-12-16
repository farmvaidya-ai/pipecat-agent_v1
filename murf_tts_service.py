from pydub import AudioSegment
import pydub.utils

# Set ffmpeg and ffprobe paths
pydub.utils.ffmpeg_path = "/usr/bin/ffmpeg"
pydub.utils.ffprobe_path = "/usr/bin/ffprobe"
import io

import aiohttp
import asyncio
from typing import AsyncGenerator
from pipecat.frames.frames import Frame, TTSAudioRawFrame, TTSStartedFrame, TTSStoppedFrame, ErrorFrame
from pipecat.services.ai_services import TTSService
from loguru import logger


class MurfTTSService(TTSService):
    """Custom Murf TTS Service implementation"""
    
    def __init__(
        self,
        *,
        api_key: str,
        voice_id: str = "te-IN-priya",
        sample_rate: int = 16000,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._api_key = api_key
        self._voice_id = voice_id
        self._sample_rate = sample_rate
        self._api_url = "https://api.murf.ai/v1/speech/generate"
        
    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        """Generate speech from text using Murf API"""
        
        yield TTSStartedFrame()
        
        logger.debug(f"MurfTTSService: Generating TTS [{text}]")
        
        yield TTSStartedFrame()
        
        try:
            headers = {
                "api-key": self._api_key,  # Changed from Authorization: Bearer
                "Content-Type": "application/json"
            }
            
            payload = {
                "voiceId": self._voice_id,
                "text": text,
                "format": "WAV",
                "sampleRate": self._sample_rate,
                "channelType": "MONO"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Murf API error: {response.status} - {error_text}")
                        yield ErrorFrame(f"Murf TTS error: {response.status}")
                        return
                    
                    # Get audio data
                    data = await response.json()
                    audio_url = data["audioFile"]
                    
                    async with session.get(audio_url) as audio_response:
                        audio_data = await audio_response.read()
                    
                    # Resample audio to 16000 Hz for compatibility
                    audio_segment = AudioSegment.from_wav(io.BytesIO(audio_data))
                    audio_segment = audio_segment.set_frame_rate(16000)
                    resampled_wav = audio_segment.export(format="wav").read()
                    audio_bytes = resampled_wav[44:] if len(resampled_wav) > 44 else resampled_wav
                    yield TTSAudioRawFrame(  # Changed from AudioRawFrame
                        audio=audio_bytes,
                        sample_rate=16000,
                        num_channels=1
                    )
                    
                    logger.debug(f"MurfTTSService: Generated {len(audio_bytes)} bytes")
                    
                    yield TTSStoppedFrame()
                    
        except asyncio.TimeoutError:
            logger.error("MurfTTSService: Request timeout")
            yield ErrorFrame("Murf TTS timeout")
        except Exception as e:
            logger.error(f"MurfTTSService error: {e}")
            yield ErrorFrame(f"Murf TTS error: {str(e)}")
