import sys
from pathlib import Path

def get_base_dir() -> Path:
    """Returns the base directory for data files — 
    next to the executable when packaged, repo root when running from source."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent

def get_asset_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = get_base_dir()
    return str(base / relative_path)