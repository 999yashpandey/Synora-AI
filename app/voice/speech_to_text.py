from __future__ import annotations

import os
import tempfile
import wave
from pathlib import Path

import speech_recognition as sr
from faster_whisper import WhisperModel


# ============================================================
# CONFIGURATION
# ============================================================

WHISPER_MODEL = "base"

recognizer = sr.Recognizer()

_stt = None


# ============================================================
# LOAD LOCAL WHISPER
# ============================================================

def get_stt():

    global _stt

    if _stt is None:

        print(
            "[Synora Voice] Loading local Whisper model: base"
        )

        _stt = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
        )

        print(
            "[Synora Voice] Local Whisper model ready."
        )

    return _stt


# ============================================================
# MICROPHONE CAPTURE
# ============================================================

def capture_audio() -> sr.AudioData | None:

    with sr.Microphone() as source:

        print(
            "[Synora Voice] Adjusting microphone..."
        )

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.8,
        )

        print(
            "[Synora Voice] Listening..."
        )

        try:

            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=12,
            )

        except sr.WaitTimeoutError:

            print(
                "[Synora Voice] No speech detected."
            )

            return None

    return audio


# ============================================================
# AUDIO → WAV
# ============================================================

def audio_to_wav(
    audio: sr.AudioData,
) -> Path:

    fd, filename = tempfile.mkstemp(
        suffix=".wav"
    )

    os.close(fd)

    path = Path(filename)

    wav_data = audio.get_wav_data()

    with wave.open(
        str(path),
        "wb"
    ) as wav_file:

        wav_file.setnchannels(1)

        wav_file.setsampwidth(
            audio.sample_width
        )

        wav_file.setframerate(
            audio.sample_rate
        )

        wav_file.writeframes(
            wav_data
        )

    return path


# ============================================================
# LOCAL ENGLISH TRANSCRIPTION
# ============================================================

def transcribe_audio(
    audio_path: Path,
) -> str:

    model = get_stt()

    print(
        "[Synora Voice] Transcribing locally..."
    )

    segments, info = model.transcribe(

        str(audio_path),

        language="en",

        task="transcribe",

        beam_size=5,

        vad_filter=True,

        condition_on_previous_text=False,

        # IMPORTANT:
        # Do NOT provide a long initial_prompt.
        # It can cause Whisper to hallucinate the prompt
        # as if the user actually spoke it.
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    ).strip()

    return text


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def listen_and_transcribe() -> str | None:

    audio = capture_audio()

    if audio is None:
        return None

    temporary_path = None

    try:

        temporary_path = audio_to_wav(
            audio
        )

        text = transcribe_audio(
            temporary_path
        )

        if text:

            print(
                f"[Synora Voice] You said: {text}"
            )

            return text

        print(
            "[Synora Voice] "
            "I couldn't understand that."
        )

        return None

    except Exception as error:

        print(
            "[Synora Voice] "
            f"Local transcription error: {error}"
        )

        return None

    finally:

        if (
            temporary_path
            and temporary_path.exists()
        ):

            try:
                temporary_path.unlink()

            except Exception:
                pass


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 55)
    print(
        "        SYNORA AI - LOCAL WHISPER STT TEST"
    )
    print("=" * 55)

    print(
        "\nYour microphone audio will be "
        "transcribed locally."
    )

    result = listen_and_transcribe()

    if result:

        print(
            f"\nYou said: {result}"
        )

    else:

        print(
            "\nNo usable speech was detected."
        )