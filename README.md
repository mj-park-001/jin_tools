# Jin Tools

A collection of Maya tools for animation and rigging workflows.

## Installation

1. Clone or download this repository
2. Place the `jin_tools` folder in a location on Maya's Python path, such as:
   - `Documents/maya/scripts/`
   - Or any custom scripts folder

Alternatively, add the parent folder to Maya's path in your `Maya.env`:
```
PYTHONPATH=C:\path\to\parent_of_jin_tools
```

## Rig Locator Tool

A tool for creating virtual locator networks to non-destructively edit rig animation.

### Features
- Create aim-space locators for spine, neck, or any chain of controls
- Bake animation to locators, adjust, then bake back to rig
- Configurable presets that can be shared across workstations
- Non-destructive workflow - delete locators to revert changes

### Usage

Run in Maya's Script Editor (Python):

```python
from jin_tools.maya.app.animation.rig_locator_tool import window
window.run()
```

### Workflow

1. **Select Namespace** - Choose the rig's namespace from the dropdown
2. **Configure Presets** - Add presets for different control chains (spine, neck, etc.)
3. **Create** - Check the presets you want and click "Create Selected"
4. **Animate** - Adjust the locators to modify the animation
5. **Complete** - Click "Bake" to apply changes or "Del" to discard

### Preset Configuration

Presets are stored in `jin_tools/maya/app/animation/rig_locator_tool/presets.json`:

```json
{
    "presets": [
        {
            "name": "Spine Default",
            "target_controls": ["Spine_CON", "Spine1_CON", "Spine2_CON"],
            "cog_control": "Hips_CON",
            "direction": "y",
            "distance_multiplier": 80,
            "include_translate": true
        }
    ]
}
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

Min Jin Semsar-Park
