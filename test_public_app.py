"""公開版で切り分けからダウンロード表示まで確認する。"""

import io
import math
import shutil
import struct
import unittest
import wave
from pathlib import Path

from streamlit.testing.v1 import AppTest


def sample_wav() -> bytes:
    """短い検証用音声を生成する。"""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        samples = (
            struct.pack("<h", round(4000 * math.sin(2 * math.pi * 440 * i / 8000)))
            for i in range(16000)
        )
        stream.writeframes(b"".join(samples))
    return buffer.getvalue()


@unittest.skipUnless(shutil.which("ffmpeg"), "音声変換にFFmpegが必要")
class PublicAppTests(unittest.TestCase):
    def test_save_download_history_and_reset(self) -> None:
        app = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
        app.get("file_uploader")[0].upload("test.wav", sample_wav(), "audio/wav").run()
        self.assertEqual(len(app.table), 1)
        self.assertFalse(next(button for button in app.button if button.label == "Cut and save").disabled)
        next(button for button in app.button if button.label == "Cut and save").click().run()
        self.assertFalse(app.error)
        self.assertEqual(len(app.get("download_button")), 1)
        self.assertEqual(len(app.dataframe), 1)
        directory = app.session_state["_public_temp_directory"].name
        next(button for button in app.button if button.label == "Start a new task (reset)").click().run()
        self.assertFalse(Path(directory).exists())
        self.assertFalse(app.error)

    def test_automatic_mode_updates_review_list(self) -> None:
        app = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
        app.get("file_uploader")[0].upload("test.wav", sample_wav(), "audio/wav").run()
        next(radio for radio in app.radio if radio.label == "Splitting method").set_value("Automatic").run()
        self.assertFalse(app.error)
        self.assertEqual(len(app.table), 1)
        self.assertFalse(next(button for button in app.button if button.label == "Cut and save").disabled)


if __name__ == "__main__":
    unittest.main()
