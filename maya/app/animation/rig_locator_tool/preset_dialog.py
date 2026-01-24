"""Dialog for adding and editing rig locator presets."""

try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    from PySide import QtWidgets, QtCore

import logging
from typing import Optional, Dict, Any, List

import maya.cmds as cmds

log = logging.getLogger(__name__)


class PresetDialog(QtWidgets.QDialog):
    """Dialog for creating or editing a preset configuration."""
    
    DIRECTIONS = ["y", "z", "x"]
    
    # Signal emitted when preset is saved: (preset_dict, edit_row)
    # edit_row is -1 for new presets, or the row index being edited
    preset_saved = QtCore.Signal(dict, int)
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None, preset: Optional[Dict[str, Any]] = None, edit_row: int = -1):
        """Initialize the preset dialog.
        
        Args:
            parent: Parent widget.
            preset: Existing preset dict to edit, or None to create new.
            edit_row: Row index being edited, or -1 for new preset.
        """
        super().__init__(parent)
        
        self.preset = preset
        self.edit_row = edit_row
        self._result_preset = None
        
        self._setup_ui()
        self._connect_signals()
        
        # Populate fields if editing existing preset
        if preset:
            self._populate_from_preset(preset)
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        # Window settings
        title = "Edit Preset" if self.preset else "Add Preset"
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Form layout for fields
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(8)
        
        # Name field
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Spine Default")
        form_layout.addRow("Name:", self.name_edit)
        
        # Target controls field with pick button
        target_layout = QtWidgets.QHBoxLayout()
        self.target_edit = QtWidgets.QLineEdit()
        self.target_edit.setPlaceholderText("Spine_CON, Spine1_CON, Spine2_CON")
        self.target_pick_btn = QtWidgets.QPushButton("◀ Pick Selected")
        self.target_pick_btn.setFixedWidth(100)
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(self.target_pick_btn)
        form_layout.addRow("Target Controls:", target_layout)
        
        # Help label for target controls
        target_help = QtWidgets.QLabel("(comma-separated, without namespace)")
        target_help.setStyleSheet("color: gray; font-size: 10px;")
        form_layout.addRow("", target_help)
        
        # COG control field with pick button
        cog_layout = QtWidgets.QHBoxLayout()
        self.cog_edit = QtWidgets.QLineEdit()
        self.cog_edit.setPlaceholderText("Hips_CON")
        self.cog_pick_btn = QtWidgets.QPushButton("◀ Pick Selected")
        self.cog_pick_btn.setFixedWidth(100)
        cog_layout.addWidget(self.cog_edit)
        cog_layout.addWidget(self.cog_pick_btn)
        form_layout.addRow("COG Control:", cog_layout)
        
        # Direction radio buttons
        direction_layout = QtWidgets.QHBoxLayout()
        self.direction_group = QtWidgets.QButtonGroup(self)
        self.direction_radios = {}
        
        for direction in self.DIRECTIONS:
            radio = QtWidgets.QRadioButton(direction.upper())
            self.direction_radios[direction] = radio
            self.direction_group.addButton(radio)
            direction_layout.addWidget(radio)
        
        # Default to Y
        self.direction_radios["y"].setChecked(True)
        direction_layout.addStretch()
        form_layout.addRow("Direction:", direction_layout)
        
        # Distance spinbox
        self.distance_spin = QtWidgets.QSpinBox()
        self.distance_spin.setRange(0, 9999)
        self.distance_spin.setValue(80)
        self.distance_spin.setFixedWidth(100)
        form_layout.addRow("Distance:", self.distance_spin)
        
        # Include translate checkbox
        self.translate_check = QtWidgets.QCheckBox()
        self.translate_check.setChecked(True)
        form_layout.addRow("Include Translate:", self.translate_check)
        
        main_layout.addLayout(form_layout)
        
        # Spacer
        main_layout.addStretch()
        
        # Button box
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.setDefault(True)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
    
    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        self.target_pick_btn.clicked.connect(self._pick_target_controls)
        self.cog_pick_btn.clicked.connect(self._pick_cog_control)
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._on_save)
    
    def _populate_from_preset(self, preset: Dict[str, Any]) -> None:
        """Populate dialog fields from existing preset.
        
        Args:
            preset: Preset dictionary to populate from.
        """
        self.name_edit.setText(preset.get("name", ""))
        
        target_controls = preset.get("target_controls", [])
        self.target_edit.setText(", ".join(target_controls))
        
        self.cog_edit.setText(preset.get("cog_control", ""))
        
        direction = preset.get("direction", "y")
        if direction in self.direction_radios:
            self.direction_radios[direction].setChecked(True)
        
        self.distance_spin.setValue(preset.get("distance_multiplier", 80))
        self.translate_check.setChecked(preset.get("include_translate", True))
    
    def _pick_target_controls(self) -> None:
        """Pick target controls from Maya selection."""
        selection = cmds.ls(selection=True) or []
        
        if not selection:
            log.warning("Nothing selected in Maya")
            return
        
        # Strip namespace from selection
        control_names = [self._strip_namespace(obj) for obj in selection]
        self.target_edit.setText(", ".join(control_names))
    
    def _pick_cog_control(self) -> None:
        """Pick COG control from Maya selection (first selected)."""
        selection = cmds.ls(selection=True) or []
        
        if not selection:
            log.warning("Nothing selected in Maya")
            return
        
        # Use first selected, strip namespace
        control_name = self._strip_namespace(selection[0])
        self.cog_edit.setText(control_name)
    
    def _strip_namespace(self, node_name: str) -> str:
        """Strip namespace from a node name.
        
        Args:
            node_name: Full node name possibly with namespace.
            
        Returns:
            Node name without namespace.
        """
        if ":" in node_name:
            return node_name.split(":")[-1]
        return node_name
    
    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate inputs
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Preset name is required.")
            self.name_edit.setFocus()
            return
        
        target_text = self.target_edit.text().strip()
        if not target_text:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "At least one target control is required.")
            self.target_edit.setFocus()
            return
        
        cog_control = self.cog_edit.text().strip()
        if not cog_control:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "COG control is required.")
            self.cog_edit.setFocus()
            return
        
        # Parse target controls
        target_controls = [ctrl.strip() for ctrl in target_text.split(",") if ctrl.strip()]
        
        # Get selected direction
        direction = "y"
        for dir_key, radio in self.direction_radios.items():
            if radio.isChecked():
                direction = dir_key
                break
        
        # Build result preset
        self._result_preset = {
            "name": name,
            "target_controls": target_controls,
            "cog_control": cog_control,
            "direction": direction,
            "distance_multiplier": self.distance_spin.value(),
            "include_translate": self.translate_check.isChecked()
        }
        
        # Emit signal with result and close
        self.preset_saved.emit(self._result_preset, self.edit_row)
        self.close()
    
    def get_preset(self) -> Optional[Dict[str, Any]]:
        """Get the resulting preset after dialog closes.
        
        Returns:
            Preset dictionary if saved, None if cancelled.
        """
        return self._result_preset


def show_preset_dialog(parent: Optional[QtWidgets.QWidget] = None, 
                       preset: Optional[Dict[str, Any]] = None,
                       edit_row: int = -1) -> PresetDialog:
    """Show the preset dialog (non-blocking).
    
    Args:
        parent: Parent widget.
        preset: Existing preset to edit, or None to create new.
        edit_row: Row index being edited, or -1 for new preset.
        
    Returns:
        The dialog instance. Connect to its preset_saved signal to get results.
    """
    dialog = PresetDialog(parent=parent, preset=preset, edit_row=edit_row)
    dialog.show()
    return dialog
