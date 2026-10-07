from __future__ import annotations

import threading
import pythoncom
import win32com.client


class SynoraTTS:
    """
    Windows SAPI5 Text-to-Speech for Synora AI.

    Uses the Windows SAPI.SpVoice engine directly instead of pyttsx3.
    Speech is handled safely in a background thread.
    """

    def __init__(
        self,
        rate: int = 0,
        volume: int = 100,
    ):
        self.rate = max(-10, min(rate, 10))
        self.volume = max(0, min(volume, 100))

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def speak(
        self,
        text: str,
        blocking: bool = False,
    ):
        text = str(text or "").strip()

        if not text:
            return

        self._stop_event.clear()

        if blocking:
            self._speak_now(text)
            return

        thread = threading.Thread(
            target=self._speak_now,
            args=(text,),
            daemon=True,
        )

        thread.start()

    def _speak_now(self, text: str):
        pythoncom.CoInitialize()

        try:
            with self._lock:
                if self._stop_event.is_set():
                    return

                speaker = win32com.client.Dispatch(
                    "SAPI.SpVoice"
                )

                speaker.Rate = self.rate
                speaker.Volume = self.volume

                speaker.Speak(
                    text,
                    0,
                )

        except Exception as error:
            print(
                f"[Synora TTS] {error}"
            )

        finally:
            pythoncom.CoUninitialize()

    def stop(self):
        self._stop_event.set()


_tts = SynoraTTS()


def speak(text: str, blocking: bool = False):
    _tts.speak(text, blocking=blocking)

def stop_speaking():
    _tts.stop()


if __name__ == "__main__":
    print(
        "Synora TTS test"
    )

    text = input(
        "Enter text for Synora to speak: "
    ).strip()

    if text:
        print(
            "[Synora TTS] Speaking..."
        )

        _tts.speak(
            text,
            blocking=True,
        )

        print(
            "[Synora TTS] Finished."
        )
    else:
        print(
            "[Synora TTS] No text entered."
        )
        