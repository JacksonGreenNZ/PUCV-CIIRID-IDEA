import shutil
import sys
from pathlib import Path

def get_ffmpeg_path():
    # 1. bundled (Windows installer layout)
    local_win = Path(sys.executable).parent / "ffmpeg" / "bin" / "ffmpeg.exe"
    if local_win.exists():
        return str(local_win)

    # 2. bundled (macOS DMG layout — ffmpeg binary sits next to the app)
    local_mac = Path(sys.executable).parent / "ffmpeg" / "ffmpeg"
    if local_mac.exists():
        return str(local_mac)

    # 3. system-wide (Linux/macOS)
    system = shutil.which("ffmpeg")
    if system:
        return system

    raise RuntimeError("FFmpeg not found")
