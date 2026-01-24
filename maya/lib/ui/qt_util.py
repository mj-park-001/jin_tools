"""Helper functions for working with Maya's Qt API.

This module provides utility functions for integrating Qt/PySide2 widgets
with Maya's user interface.
"""

import maya.OpenMayaUI as OpenMayaUI

try:
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance
except ImportError:
    from PySide import QtWidgets
    from shiboken import wrapInstance


def get_maya_window() -> QtWidgets.QWidget:
    """Get Maya's main window as a Qt widget.

    This function retrieves Maya's main window pointer and wraps it
    as a QWidget, allowing Qt widgets to be parented to Maya's interface.

    Returns:
        QtWidgets.QWidget: Maya's main window as a QWidget instance.
    """
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
