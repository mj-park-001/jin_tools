"""Main window for the Rig Locator Tool."""

try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide import QtWidgets, QtCore, QtGui

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import maya.cmds as cmds

from . import config
from . import core
from . import preset_dialog
from ....lib.node import namespace as libNamespace
from ....lib.ui import qt_util

log = logging.getLogger(__name__)


class RigLocatorWindow(QtWidgets.QWidget):
    """Main window for the Rig Locator Tool.
    
    Provides a unified interface for creating and managing rig locator networks
    with configurable presets that can be shared across workstations.
    """
    
    MIN_WIDTH = 550
    MIN_HEIGHT = 500
    
    # Table column indices
    COL_CHECK = 0
    COL_NAME = 1
    COL_COG = 2
    COL_DIR = 3
    COL_DIST = 4
    COL_TRANS = 5
    COL_ACTIONS = 6
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """Initialize the Rig Locator window.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.presets = []
        
        self._setup_ui()
        self._connect_signals()
        self._load_presets()
        self._refresh_scene_state()
    
    def _setup_ui(self) -> None:
        """Set up the main window UI."""
        self.setWindowTitle("Rig Locator Tool")
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === Namespace section ===
        namespace_layout = QtWidgets.QHBoxLayout()
        namespace_label = QtWidgets.QLabel("Namespace:")
        self.namespace_combo = QtWidgets.QComboBox()
        self.namespace_combo.setMinimumWidth(200)
        namespace_layout.addWidget(namespace_label)
        namespace_layout.addWidget(self.namespace_combo)
        namespace_layout.addStretch()
        self.refresh_btn = QtWidgets.QPushButton("↻ Refresh")
        self.refresh_btn.setFixedWidth(80)
        namespace_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(namespace_layout)
        
        # Separator line
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # === Presets section ===
        presets_group = QtWidgets.QGroupBox("Presets")
        presets_layout = QtWidgets.QVBoxLayout(presets_group)
        
        # Presets table
        self.presets_table = QtWidgets.QTableWidget()
        self.presets_table.setColumnCount(7)
        self.presets_table.setHorizontalHeaderLabels(["", "Name", "COG Control", "Dir", "Dist", "Trans", "Actions"])
        self.presets_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.presets_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.presets_table.verticalHeader().setVisible(False)
        self.presets_table.setAlternatingRowColors(True)
        
        # Column widths
        header = self.presets_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_CHECK, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_NAME, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_COG, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_DIR, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_DIST, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_TRANS, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_ACTIONS, QtWidgets.QHeaderView.Fixed)
        self.presets_table.setColumnWidth(self.COL_CHECK, 30)
        self.presets_table.setColumnWidth(self.COL_DIR, 40)
        self.presets_table.setColumnWidth(self.COL_DIST, 50)
        self.presets_table.setColumnWidth(self.COL_TRANS, 50)
        self.presets_table.setColumnWidth(self.COL_ACTIONS, 110)
        
        presets_layout.addWidget(self.presets_table)
        
        # Preset buttons
        preset_btn_layout = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("+ Add")
        self.edit_btn = QtWidgets.QPushButton("Edit")
        self.duplicate_btn = QtWidgets.QPushButton("Duplicate")
        self.remove_btn = QtWidgets.QPushButton("- Remove")
        
        preset_btn_layout.addWidget(self.add_btn)
        preset_btn_layout.addWidget(self.edit_btn)
        preset_btn_layout.addWidget(self.duplicate_btn)
        preset_btn_layout.addWidget(self.remove_btn)
        preset_btn_layout.addStretch()
        
        self.create_btn = QtWidgets.QPushButton("▶ Create Selected")
        self.create_btn.setMinimumWidth(130)
        preset_btn_layout.addWidget(self.create_btn)
        
        presets_layout.addLayout(preset_btn_layout)
        main_layout.addWidget(presets_group)
        
        # Separator line
        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.HLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(separator2)
        
        # === Log section ===
        log_group = QtWidgets.QGroupBox("Log")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self.log_text)
        
        log_btn_layout = QtWidgets.QHBoxLayout()
        log_btn_layout.addStretch()
        self.clear_log_btn = QtWidgets.QPushButton("Clear")
        self.clear_log_btn.setFixedWidth(60)
        log_btn_layout.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_btn_layout)
        
        main_layout.addWidget(log_group)
    
    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        self.refresh_btn.clicked.connect(self._refresh_scene_state)
        self.namespace_combo.currentIndexChanged.connect(self._on_namespace_changed)
        
        self.add_btn.clicked.connect(self._on_add_preset)
        self.edit_btn.clicked.connect(self._on_edit_preset)
        self.duplicate_btn.clicked.connect(self._on_duplicate_preset)
        self.remove_btn.clicked.connect(self._on_remove_preset)
        
        self.create_btn.clicked.connect(self._on_create)
        
        self.presets_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.clear_log_btn.clicked.connect(self._on_clear_log)
    
    def _load_presets(self) -> None:
        """Load presets from config file and populate table."""
        self.presets = config.load_presets()
        self._populate_presets_table()
    
    def _save_presets(self) -> None:
        """Save current presets to config file."""
        if config.save_presets(self.presets):
            self._log_info("Presets saved successfully")
        else:
            self._log_error("Failed to save presets")
    
    def _populate_presets_table(self) -> None:
        """Populate the presets table from current presets list."""
        self.presets_table.setRowCount(len(self.presets))
        
        namespace = self.namespace_combo.currentText()
        if namespace == "(no namespace)":
            namespace = ""
        
        for row, preset in enumerate(self.presets):
            # Checkbox
            check_widget = QtWidgets.QWidget()
            check_layout = QtWidgets.QHBoxLayout(check_widget)
            check_layout.setContentsMargins(0, 0, 0, 0)
            check_layout.setAlignment(QtCore.Qt.AlignCenter)
            checkbox = QtWidgets.QCheckBox()
            check_layout.addWidget(checkbox)
            self.presets_table.setCellWidget(row, self.COL_CHECK, check_widget)
            
            # Name
            name_item = QtWidgets.QTableWidgetItem(preset.get("name", ""))
            name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.presets_table.setItem(row, self.COL_NAME, name_item)
            
            # COG Control
            cog_item = QtWidgets.QTableWidgetItem(preset.get("cog_control", ""))
            cog_item.setFlags(cog_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.presets_table.setItem(row, self.COL_COG, cog_item)
            
            # Direction
            dir_item = QtWidgets.QTableWidgetItem(preset.get("direction", "y").upper())
            dir_item.setFlags(dir_item.flags() & ~QtCore.Qt.ItemIsEditable)
            dir_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.presets_table.setItem(row, self.COL_DIR, dir_item)
            
            # Distance
            dist_item = QtWidgets.QTableWidgetItem(str(preset.get("distance_multiplier", 80)))
            dist_item.setFlags(dist_item.flags() & ~QtCore.Qt.ItemIsEditable)
            dist_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.presets_table.setItem(row, self.COL_DIST, dist_item)
            
            # Include Translate
            trans_text = "✓" if preset.get("include_translate", False) else "✗"
            trans_item = QtWidgets.QTableWidgetItem(trans_text)
            trans_item.setFlags(trans_item.flags() & ~QtCore.Qt.ItemIsEditable)
            trans_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.presets_table.setItem(row, self.COL_TRANS, trans_item)
            
            # Actions (Bake/Delete buttons)
            actions_widget = QtWidgets.QWidget()
            actions_layout = QtWidgets.QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)
            
            bake_btn = QtWidgets.QPushButton("Bake")
            bake_btn.setFixedWidth(50)
            delete_btn = QtWidgets.QPushButton("Del")
            delete_btn.setFixedWidth(40)
            
            # Check if this preset's locator is active
            is_active = self._is_preset_locator_active(preset, namespace)
            bake_btn.setEnabled(is_active)
            delete_btn.setEnabled(is_active)
            
            # Connect buttons
            bake_btn.clicked.connect(lambda checked=False, p=preset: self._on_bake_preset(p))
            delete_btn.clicked.connect(lambda checked=False, p=preset: self._on_delete_preset(p))
            
            actions_layout.addWidget(bake_btn)
            actions_layout.addWidget(delete_btn)
            self.presets_table.setCellWidget(row, self.COL_ACTIONS, actions_widget)
        
        self._on_selection_changed()
    
    def _is_preset_locator_active(self, preset: Dict[str, Any], namespace: str) -> bool:
        """Check if a preset's locator is active in the scene.
        
        Args:
            preset: Preset dictionary.
            namespace: Current namespace.
            
        Returns:
            True if the preset's locator exists in the scene.
        """
        base_name = preset.get("name", "").replace(" ", "_").upper()
        locator_name = "{}PARENT".format(base_name)
        
        if namespace:
            locator_name = "{}:{}".format(namespace, locator_name)
        
        return cmds.objExists(locator_name)
    
    def _on_bake_preset(self, preset: Dict[str, Any]) -> None:
        """Bake and complete a preset's locator.
        
        Args:
            preset: Preset dictionary.
        """
        self._complete_preset_locator(preset, "bake")
    
    def _on_delete_preset(self, preset: Dict[str, Any]) -> None:
        """Delete a preset's locator.
        
        Args:
            preset: Preset dictionary.
        """
        self._complete_preset_locator(preset, "delete")
    
    def _complete_preset_locator(self, preset: Dict[str, Any], complete_type: str) -> None:
        """Complete (bake or delete) a preset's locator.
        
        Args:
            preset: Preset dictionary.
            complete_type: Either 'bake' or 'delete'.
        """
        namespace = self.namespace_combo.currentText()
        if namespace == "(no namespace)":
            namespace = None
        
        base_name = preset.get("name", "").replace(" ", "_")
        target_controls = preset.get("target_controls", [])
        
        try:
            core.complete_rig_locator(
                base_name=base_name,
                target_controls=target_controls,
                namespace=namespace,
                complete_type=complete_type
            )
            action = "Baked and completed" if complete_type == "bake" else "Deleted"
            self._log_info("{}: {}".format(action, preset.get("name", "")))
        except Exception as e:
            self._log_error("Failed to complete {}: {}".format(preset.get("name", ""), str(e)))
        
        # Refresh table to update button states
        self._populate_presets_table()
    
    def _get_row_checkbox(self, row: int) -> Optional[QtWidgets.QCheckBox]:
        """Get the checkbox widget for a given row.
        
        Args:
            row: Table row index.
            
        Returns:
            QCheckBox widget or None.
        """
        widget = self.presets_table.cellWidget(row, self.COL_CHECK)
        if widget:
            checkbox = widget.findChild(QtWidgets.QCheckBox)
            return checkbox
        return None
    
    def _get_checked_preset_indices(self) -> List[int]:
        """Get indices of all checked presets.
        
        Returns:
            List of row indices that are checked.
        """
        checked = []
        for row in range(self.presets_table.rowCount()):
            checkbox = self._get_row_checkbox(row)
            if checkbox and checkbox.isChecked():
                checked.append(row)
        return checked
    
    def _get_selected_row(self) -> int:
        """Get the currently selected row index.
        
        Returns:
            Selected row index, or -1 if none selected.
        """
        selection = self.presets_table.selectedItems()
        if selection:
            return selection[0].row()
        return -1
    
    def _refresh_scene_state(self) -> None:
        """Refresh namespaces and active locators from scene."""
        # Get all namespaces
        try:
            namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []
            # Filter out Maya defaults
            namespaces = [ns for ns in namespaces if ns not in ["UI", "shared"]]
        except RuntimeError:
            namespaces = []
        
        # Store current selection
        current_ns = self.namespace_combo.currentText()
        
        # Update namespace combo
        self.namespace_combo.clear()
        if namespaces:
            self.namespace_combo.addItems(sorted(namespaces))
            # Restore previous selection if still exists
            index = self.namespace_combo.findText(current_ns)
            if index >= 0:
                self.namespace_combo.setCurrentIndex(index)
        else:
            self.namespace_combo.addItem("(no namespace)")
        
        # Update table to refresh action button states
        self._populate_presets_table()
        
        self._log_info("Refreshed - Found {} namespace(s)".format(len(namespaces)))
    
    def _on_namespace_changed(self) -> None:
        """Handle namespace dropdown change."""
        self._populate_presets_table()
    
    def _on_selection_changed(self) -> None:
        """Handle preset table selection change."""
        has_selection = self._get_selected_row() >= 0
        self.edit_btn.setEnabled(has_selection)
        self.duplicate_btn.setEnabled(has_selection)
        self.remove_btn.setEnabled(has_selection)
    
    def _on_add_preset(self) -> None:
        """Handle add preset button click."""
        self.setEnabled(False)
        dialog = preset_dialog.show_preset_dialog(parent=self)
        dialog.preset_saved.connect(self._on_preset_saved)
        dialog.preset_saved.connect(lambda *args: self.setEnabled(True))
        dialog.rejected.connect(lambda: self.setEnabled(True))
    
    def _on_edit_preset(self) -> None:
        """Handle edit preset button click."""
        row = self._get_selected_row()
        if row < 0 or row >= len(self.presets):
            return
        
        self.setEnabled(False)
        existing_preset = self.presets[row]
        dialog = preset_dialog.show_preset_dialog(parent=self, preset=existing_preset, edit_row=row)
        dialog.preset_saved.connect(self._on_preset_saved)
        dialog.preset_saved.connect(lambda *args: self.setEnabled(True))
        dialog.rejected.connect(lambda: self.setEnabled(True))
    
    def _on_preset_saved(self, preset: Dict[str, Any], edit_row: int) -> None:
        """Handle preset saved from dialog.
        
        Args:
            preset: The saved preset dictionary.
            edit_row: Row being edited, or -1 for new preset.
        """
        if edit_row >= 0:
            # Editing existing preset
            self.presets[edit_row] = preset
            self._log_info("Updated preset: {}".format(preset.get("name", "")))
        else:
            # Adding new preset
            self.presets.append(preset)
            self._log_info("Added preset: {}".format(preset.get("name", "")))
        
        self._save_presets()
        self._populate_presets_table()
    
    def _on_duplicate_preset(self) -> None:
        """Handle duplicate preset button click."""
        row = self._get_selected_row()
        if row < 0 or row >= len(self.presets):
            return
        
        # Create a copy with modified name
        original = self.presets[row]
        duplicate = dict(original)
        duplicate["name"] = "{} (copy)".format(original.get("name", ""))
        
        self.presets.append(duplicate)
        self._save_presets()
        self._populate_presets_table()
        self._log_info("Duplicated preset: {}".format(original.get("name", "")))
    
    def _on_remove_preset(self) -> None:
        """Handle remove preset button click."""
        row = self._get_selected_row()
        if row < 0 or row >= len(self.presets):
            return
        
        preset_name = self.presets[row].get("name", "")
        
        # Confirm deletion
        result = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete preset '{}'?".format(preset_name),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if result == QtWidgets.QMessageBox.Yes:
            del self.presets[row]
            self._save_presets()
            self._populate_presets_table()
            self._log_info("Removed preset: {}".format(preset_name))
    
    def _on_create(self) -> None:
        """Handle create button click."""
        checked_indices = self._get_checked_preset_indices()
        
        if not checked_indices:
            self._log_warning("No presets selected. Check the boxes next to presets to create.")
            return
        
        namespace = self.namespace_combo.currentText()
        if namespace == "(no namespace)":
            namespace = None
        
        # Validate all checked presets first
        validation_errors = []
        for idx in checked_indices:
            preset = self.presets[idx]
            errors = self._validate_preset_controls(preset, namespace)
            if errors:
                validation_errors.extend(errors)
        
        if validation_errors:
            for error in validation_errors:
                self._log_error(error)
            self._log_error("Creation blocked - fix missing controls above")
            return
        
        # Create rig locators for all checked presets
        for idx in checked_indices:
            preset = self.presets[idx]
            try:
                core.create_rig_locator(
                    target_controls=preset["target_controls"],
                    namespace=namespace,
                    cog_control=preset["cog_control"],
                    base_name=preset["name"].replace(" ", "_"),
                    direction=preset["direction"],
                    distance_multiplier=preset["distance_multiplier"],
                    include_translate=preset["include_translate"]
                )
                self._log_info("Created: {} successfully".format(preset["name"]))
            except Exception as e:
                self._log_error("Failed to create {}: {}".format(preset["name"], str(e)))
        
        # Refresh table to update action button states
        self._populate_presets_table()
    
    def _validate_preset_controls(self, preset: Dict[str, Any], namespace: Optional[str]) -> List[str]:
        """Validate that all controls in a preset exist in the scene.
        
        Args:
            preset: Preset dictionary.
            namespace: Current namespace.
            
        Returns:
            List of error messages for missing controls.
        """
        errors = []
        preset_name = preset.get("name", "Unknown")
        
        # Check target controls
        for control in preset.get("target_controls", []):
            full_name = libNamespace.replace_namespace(control, namespace)
            if not cmds.objExists(full_name):
                errors.append("{} - {} not found".format(preset_name, full_name))
        
        # Check COG control
        cog_control = preset.get("cog_control", "")
        if cog_control:
            full_cog = libNamespace.replace_namespace(cog_control, namespace)
            if not cmds.objExists(full_cog):
                errors.append("{} - {} not found".format(preset_name, full_cog))
        
        return errors
    
    def _on_clear_log(self) -> None:
        """Clear the log widget."""
        self.log_text.clear()
    
    def _log_info(self, message: str) -> None:
        """Log an info message.
        
        Args:
            message: Message to log.
        """
        self._log_message("INFO", message)
    
    def _log_warning(self, message: str) -> None:
        """Log a warning message.
        
        Args:
            message: Message to log.
        """
        self._log_message("WARNING", message)
    
    def _log_error(self, message: str) -> None:
        """Log an error message.
        
        Args:
            message: Message to log.
        """
        self._log_message("ERROR", message)
    
    def _log_message(self, level: str, message: str) -> None:
        """Log a message to the log widget.
        
        Args:
            level: Log level (INFO, WARNING, ERROR).
            message: Message to log.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color based on level
        if level == "ERROR":
            color = "#ff6b6b"
        elif level == "WARNING":
            color = "#ffd93d"
        else:
            color = "#6bcb77"
        
        formatted = '<span style="color: {};">[{}] [{}] {}</span>'.format(
            color, timestamp, level, message
        )
        
        self.log_text.append(formatted)
        
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Also log to Maya
        if level == "ERROR":
            log.error(message)
        elif level == "WARNING":
            log.warning(message)
        else:
            log.info(message)


_window = None


def run() -> None:
    """Main entry point to launch the Rig Locator Tool window."""
    global _window
    
    # Check if window already exists and close it
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(widget, RigLocatorWindow):
            widget.close()
    
    maya_main = qt_util.get_maya_window()
    _window = RigLocatorWindow(parent=maya_main)
    _window.setWindowFlags(_window.windowFlags() | QtCore.Qt.Window)
    _window.show()
    
    log.info("Rig Locator Tool launched")
