import shutil
import sys
from pathlib import Path

def get_ffmpeg_path():
    # 1. bundled (Windows installer layout)
    local = Path(sys.executable).parent / "ffmpeg" / "bin" / "ffmpeg.exe"
    if local.exists():
        return str(local)

    # 2. system-wide (Linux/macOS)
    system = shutil.which("ffmpeg")
    if system:
        return system

    raise RuntimeError("FFmpeg not found")
