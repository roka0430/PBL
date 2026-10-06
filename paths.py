from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

CONFIG_DIR = ROOT_DIR / "config"
INSTANCE_DIR = ROOT_DIR / "instance"

SETTINGS_PATH = CONFIG_DIR / "settings.json"
DATABASE_PATH = INSTANCE_DIR / "watering.db"
