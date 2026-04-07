import shutil
from pathlib import Path
import sys


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_base_dir() -> Path:
    if is_frozen():
        base = Path.home() / ".clearskyrfi"
    else:
        base = Path(__file__).resolve().parent.parent

    base.mkdir(parents=True, exist_ok=True)
    return base


def get_data_dir() -> Path:
    path = get_base_dir() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_asset_base() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_asset_path(relative_path: str) -> str:
    return str(get_asset_base() / relative_path)

def get_ffmpeg():
    # 1. bundled (Windows installer case)
    local = Path(sys.executable).parent / "ffmpeg" / "bin" / "ffmpeg.exe"
    if local.exists():
        return str(local)

    # 2. system install (Linux/macOS)
    system = shutil.which("ffmpeg")
    if system:
        return system

    raise RuntimeError("FFmpeg not found")
