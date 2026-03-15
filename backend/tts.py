from google import genai
from google.genai import types
import wave
from pathlib import Path
import os


def write_wave_file(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def text_to_speech_file(
    text: str,
    output_path: str,
    api_key: str | None = None,
    model: str = "gemini-2.5-flash-preview-tts",
    voice_name: str = "Charon",
):
    if not text.strip():
        raise ValueError("text cannot be empty")

    api_key = "API_KEY"
    if not api_key:
        raise ValueError("Missing API key. Pass api_key or set GEMINI_API_KEY.")

    client = genai.Client(api_key="API_KEY")
    content = f"In a VERY strict and angry tone, say: {text}"
    response = client.models.generate_content(
        model=model,
        contents=content,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        ),
    )

    audio_data = response.candidates[0].content.parts[0].inline_data.data

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    write_wave_file(output_file, audio_data)
    return str(output_file)
