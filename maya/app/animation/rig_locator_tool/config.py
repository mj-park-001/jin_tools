"""Configuration management for rig locator tool presets."""

import logging
import os
from typing import List, Dict, Any, Tuple

from .....lib.util import json_util

log = logging.getLogger(__name__)

# Default preset structure
DEFAULT_PRESET = {
    "name": "",
    "target_controls": [],
    "cog_control": "",
    "direction": "y",
    "distance_multiplier": 80,
    "include_translate": True
}

# Default color configuration
DEFAULT_COLORS: Dict[str, Tuple[float, float, float]] = {
    "start": (0.25, 0.0, 0.0),
    "end": (0.0, 0.167, 1.0),
    "mid": (0.0, 0.5, 0.0)
}


def get_preset_path() -> str:
    """Get the path to the presets.json file.
    
    Returns:
        Full path to presets.json in the tool directory.
    """
    return os.path.join(os.path.dirname(__file__), "presets.json")


def load_presets() -> List[Dict[str, Any]]:
    """Load presets from the JSON config file.
    
    Returns:
        List of preset dictionaries. Returns empty list if file doesn't exist or is invalid.
    """
    preset_path = get_preset_path()
    
    if not os.path.exists(preset_path):
        log.warning("Presets file not found: {}".format(preset_path))
        return []
    
    try:
        data = json_util.get_from_path(preset_path)
        return data.get("presets", [])
    except Exception as e:
        log.error("Failed to load presets file: {}".format(e))
        return []


def save_presets(presets: List[Dict[str, Any]]) -> bool:
    """Save presets to the JSON config file.
    
    Args:
        presets: List of preset dictionaries to save.
        
    Returns:
        True if save was successful, False otherwise.
    """
    preset_path = get_preset_path()
    
    try:
        json_util.save_to_path({"presets": presets}, preset_path)
        log.info("Saved {} preset(s) to {}".format(len(presets), preset_path))
        return True
    except Exception as e:
        log.error("Failed to save presets file: {}".format(e))
        return False


def create_preset(name: str,
                  target_controls: List[str],
                  cog_control: str,
                  direction: str = "x",
                  distance_multiplier: int = 80,
                  include_translate: bool = True) -> Dict[str, Any]:
    """Create a new preset dictionary with the given values.
    
    Args:
        name: Display name for the preset.
        target_controls: List of target control names.
        cog_control: COG control name.
        direction: Direction axis ('x', 'y', or 'z').
        distance_multiplier: Distance multiplier value.
        include_translate: Whether to include translation.
        
    Returns:
        Preset dictionary.
    """
    return {
        "name": name,
        "target_controls": target_controls,
        "cog_control": cog_control,
        "direction": direction,
        "distance_multiplier": distance_multiplier,
        "include_translate": include_translate
    }


def validate_preset(preset: Dict[str, Any]) -> List[str]:
    """Validate a preset dictionary and return any errors.
    
    Args:
        preset: Preset dictionary to validate.
        
    Returns:
        List of error messages. Empty list if valid.
    """
    errors = []
    
    if not preset.get("name"):
        errors.append("Preset name is required")
    
    if not preset.get("target_controls"):
        errors.append("At least one target control is required")
    
    if not preset.get("cog_control"):
        errors.append("COG control is required")
    
    if preset.get("direction") not in ["x", "y", "z"]:
        errors.append("Direction must be 'x', 'y', or 'z'")
    
    return errors
