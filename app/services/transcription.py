from __future__ import annotations

from pathlib import Path

from openai import OpenAI

from app.core.config import settings


class TranscriptionError(RuntimeError):
    pass


class AudioTranscriber:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key)
        self.client = OpenAI(api_key=settings.openai_api_key) if self.enabled else None

    def transcribe(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise TranscriptionError(f"Audio file not found: {file_path}")
        if not self.enabled or self.client is None:
            raise TranscriptionError(
                "Audio transcription is not configured. Set OPENAI_API_KEY to enable voice support."
            )
        with path.open("rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model=settings.openai_audio_model,
                file=audio_file,
            )
        return getattr(transcript, "text", "").strip()
