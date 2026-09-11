import sys
import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("config.toml")


def load_config():
    """Load config.toml from the project directory."""
    if not CONFIG_PATH.exists():
        sys.exit(
            f"Error: {CONFIG_PATH.name} not found. "
            "Copy config.example.toml to config.toml and fill in your details."
        )
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)
