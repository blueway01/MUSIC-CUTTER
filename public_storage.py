"""公開版の作業領域をブラウザー接続ごとに分離する。"""

import tempfile
from pathlib import Path
from typing import MutableMapping


SESSION_KEY = "_public_temp_directory"


def session_directory(state: MutableMapping) -> Path:
    """接続ごとの一時フォルダーを取得する。"""
    temporary = state.get(SESSION_KEY)
    if temporary is None:
        temporary = tempfile.TemporaryDirectory(prefix="music-cutter-")
        state[SESSION_KEY] = temporary
    return Path(temporary.name)


def reset_session_directory(state: MutableMapping) -> None:
    """接続中の作業ファイルを削除する。"""
    temporary = state.pop(SESSION_KEY, None)
    if temporary is not None:
        temporary.cleanup()
