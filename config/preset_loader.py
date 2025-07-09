"""
Configuration Preset Loader
Loads and manages processing configuration presets for common locations.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class PresetLoader:
    """Loads and manages configuration presets for MISR processing."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize with configuration directory."""
        if config_dir is None:
            config_dir = Path(__file__).parent
        self.config_dir = Path(config_dir)
        self._presets = {}
        self._load_presets()

    def _load_presets(self):
        """Load all preset files from config directory."""
        if not self.config_dir.exists():
            logger.warning(f"Config directory not found: {self.config_dir}")
            return

        preset_files = list(self.config_dir.glob("*_preset.json"))

        for preset_file in preset_files:
            try:
                with open(preset_file, "r") as f:
                    preset_data = json.load(f)

                preset_name = preset_data.get("name", preset_file.stem)
                self._presets[preset_name] = preset_data
                logger.info(f"Loaded preset: {preset_name}")

            except Exception as e:
                logger.error(f"Failed to load preset {preset_file}: {e}")

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a preset by name."""
        return self._presets.get(name)

    def list_presets(self) -> List[str]:
        """List all available preset names."""
        return list(self._presets.keys())

    def get_processing_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get processing configuration from preset."""
        preset = self.get_preset(name)
        if preset:
            return preset.get("processing_config")
        return None

    def save_preset(self, name: str, preset_data: Dict[str, Any]):
        """Save a new preset to file."""
        try:
            # Create filename from name
            filename = f"{name.lower().replace(' ', '_')}_preset.json"
            filepath = self.config_dir / filename

            with open(filepath, "w") as f:
                json.dump(preset_data, f, indent=2)

            # Add to loaded presets
            self._presets[name] = preset_data
            logger.info(f"Saved preset: {name}")

        except Exception as e:
            logger.error(f"Failed to save preset {name}: {e}")
            raise

    def validate_preset(self, name: str) -> bool:
        """Validate a preset configuration."""
        preset = self.get_preset(name)
        if not preset:
            return False

        # Check required fields
        required_fields = ["name", "processing_config"]
        for field in required_fields:
            if field not in preset:
                logger.error(f"Preset {name} missing required field: {field}")
                return False

        # Check processing config required fields
        config = preset["processing_config"]
        required_config_fields = [
            "target_lat",
            "target_lon",
            "region_margin",
            "target_resolution",
        ]
        for field in required_config_fields:
            if field not in config:
                logger.error(f"Preset {name} missing required config field: {field}")
                return False

        return True

    def get_preset_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a preset."""
        preset = self.get_preset(name)
        if not preset:
            return None

        return {
            "name": preset.get("name"),
            "description": preset.get("description"),
            "location": preset.get("location"),
            "notes": preset.get("notes", []),
            "created": preset.get("created"),
            "version": preset.get("version"),
        }
