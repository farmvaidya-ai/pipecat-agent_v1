"""
Custom Murf TTS Service for Pipecat
Integrates Murf AI TTS API with Pipecat framework
"""

import aiohttp
import asyncio
from typing import AsyncGenerator
from pipecat.frames.frames import Frame, AudioRawFrame, ErrorFrame
from pipecat.services.ai_services import TTSService
from loguru import logger


class MurfTTSService(TTSService):
    """Custom Murf TTS Service implementation"""
    
    def __init__(
        self,
        *,
        api_key: str,
        voice_id: str = "en-US-ken",
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
        
        logger.debug(f"MurfTTSService: Generating TTS [{text}]")
        
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
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
                    audio_data = await response.read()
                    
                    # Skip WAV header (first 44 bytes for standard WAV)
                    audio_bytes = audio_data[44:] if len(audio_data) > 44 else audio_data
                    
                    # Yield audio frame
                    yield AudioRawFrame(
                        audio=audio_bytes,
                        sample_rate=self._sample_rate,
                        num_channels=1
                    )
                    
                    logger.debug(f"MurfTTSService: Generated {len(audio_bytes)} bytes")
                    
        except asyncio.TimeoutError:
            logger.error("MurfTTSService: Request timeout")
            yield ErrorFrame("Murf TTS timeout")
        except Exception as e:
            logger.error(f"MurfTTSService error: {e}")
            yield ErrorFrame(f"Murf TTS error: {str(e)}")
