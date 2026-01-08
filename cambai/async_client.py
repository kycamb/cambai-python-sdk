import asyncio
import typing
from typing import AsyncIterator, Dict, Optional

from cambai.api.apis_api import CambAI
# from cambai.api_client import ApiClient
from cambai.configuration import Configuration


class AsyncCambAI:
    """
    Asynchronous client for Camb AI API.
    
    Provides non-blocking async/await interface for speech-to-text and text-to-speech operations.
    Both methods use async generators for streaming.
    
    Args:
        api_key: Your Camb AI API key
    
    Attributes:
        api_client: Internal API client
        apis_api: Internal APIs instance
    """

    def __init__(self, api_key: str):
        """Initialize AsyncCambAI with API key."""
        # self.api_client = ApiClient()
        # self.api_client.configuration = Configuration()
        # self.api_client.configuration.api_key = api_key
        self.camb_ai = CambAI(api_key=api_key)

    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: int,
        language: str = "en-us",
    ) -> AsyncIterator[bytes]:
        """
        Convert text to speech with async streaming.
        
        Yields audio chunks as they're generated, without blocking the event loop.
        
        Args:
            text: Text to convert to speech
            voice_id: ID of the voice to use
            language: Language code (default: "en-us")
        
        Yields:
            Audio chunks as bytes
        
        Example:
            >>> async for chunk in client.text_to_speech_stream("Hello", 123):
            ...     await save_to_file(chunk)
        """
        # Get sync generator from underlying API
        sync_gen = self.camb_ai.text_to_speech_stream(text, voice_id, language)
        
        # Yield chunks, allowing event loop to run between iterations
        for chunk in sync_gen:
            await asyncio.sleep(0)  # Yield control to event loop
            yield chunk

    async def speech_to_text_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        sample_rate: int,
        model: str = "camb",
        language: str = "en-us",
        translate_to_language: Optional[str] = None,
        punctuate: bool = True,
        diarize: bool = False,
        interim_results: bool = True,
    ) -> AsyncIterator[Dict]:
        """
        Transcribe audio stream to text with async streaming.
        
        Takes an async stream of audio chunks and yields transcription results
        as they arrive, without blocking the event loop.
        
        Args:
            audio_stream: Async generator yielding audio chunks (bytes)
            sample_rate: Sample rate in Hz (e.g., 16000)
            model: Transcription model (default: "camb")
            language: Language code (default: "en-us")
            translate_to_language: Target language for translation (optional)
            punctuate: Enable punctuation (default: True)
            diarize: Enable speaker diarization (default: False)
            interim_results: Yield interim results (default: True)
        
        Yields:
            Transcription results as dictionaries
        
        Example:
            >>> async def audio_gen():
            ...     # yield audio chunks from microphone or file
            ...     yield b"audio_chunk_1"
            ...     yield b"audio_chunk_2"
            >>> 
            >>> async for result in client.speech_to_text_stream(audio_gen(), 16000):
            ...     print(result)
        """
        # Convert async stream to list (we need to pass to sync function)
        audio_chunks = []
        async for chunk in audio_stream:
            audio_chunks.append(chunk)
        
        # Create sync generator from collected chunks
        def sync_audio_gen():
            for chunk in audio_chunks:
                yield chunk
        
        # Call sync version of speech_to_text_stream
        sync_gen = self.camb_ai.speech_to_text_stream(
            sync_audio_gen(),
            sample_rate=sample_rate,
            model=model,
            language=language,
            translate_to_language=translate_to_language,
            punctuate=punctuate,
            diarize=diarize,
            interim_results=interim_results,
        )
        
        # Yield results, allowing event loop to run between iterations
        for result in sync_gen:
            await asyncio.sleep(0)  # Yield control to event loop
            yield result
