import sys
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        # installed app — use user's home directory
        return Path.home() / ".clearskyrfi"
    return Path(__file__).parent.parent

def get_asset_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = get_base_dir()
    return str(base / relative_path)