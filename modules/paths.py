from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR = ROOT_DIR / "config"
INSTANCE_DIR = ROOT_DIR / "instance"

SETTINGS_PATH = CONFIG_DIR / "settings.json"
DEFAULT_SETTINGS_PATH = CONFIG_DIR / "default_settings.json"
DATABASE_PATH = INSTANCE_DIR / "watering.db"
