"""Maya API utility functions."""

from typing import Optional, Union

import maya.OpenMaya as OpenMaya
import maya.api.OpenMaya as OpenMaya2


def get_mobject(node: str, api_type: float = 1.0) -> Optional[Union[OpenMaya.MObject, OpenMaya2.MObject]]:
    """Get OpenMaya.MObject from a node name.

    Args:
        node: The node name.
        api_type: Maya API version (1.0 or 2.0).

    Returns:
        The MObject or None if not found.
    """
    if api_type == 1.0:
        selection_list = OpenMaya.MSelectionList()
        try:
            selection_list.add(node)
            mobject = OpenMaya.MObject()
            selection_list.getDependNode(0, mobject)
            return mobject
        except RuntimeError:
            return None

    elif api_type == 2.0:
        try:
            selection_list = OpenMaya2.MSelectionList()
            selection_list.add(node)
            return selection_list.getDependNode(0)
        except RuntimeError:
            return None

    return None


def get_mplug(node: str, attr: str, api_type: float = 1.0) -> Optional[Union[OpenMaya.MPlug, OpenMaya2.MPlug]]:
    """Get MPlug from node and attribute name.

    Args:
        node: Node name.
        attr: Attribute name.
        api_type: Maya API version (1.0 or 2.0).

    Returns:
        The MPlug object or None if not found.
    """
    if api_type == 1.0:
        # Try getting plug directly via MSelectionList
        try:
            selection_list = OpenMaya.MSelectionList()
            selection_list.add(f"{node}.{attr}")
            mplug = OpenMaya.MPlug()
            selection_list.getPlug(0, mplug)
        except RuntimeError:
            # Fallback for attributes like .rotatePivot or if the attribute doesn't exist
            mobject = get_mobject(node, api_type=1.0)
            if not mobject:
                return None
            try:
                fn_node = OpenMaya.MFnDependencyNode(mobject)
                mplug = fn_node.findPlug(attr)
            except RuntimeError:
                return None

        # Verify the plug belongs to the requested node (avoiding implicit shape propagation)
        # Optimization: Compare MObjects instead of string parsing
        plug_node_obj = mplug.node()
        input_node_obj = get_mobject(node, api_type=1.0)
        
        if input_node_obj and plug_node_obj != input_node_obj:
            return None

        return mplug

    elif api_type == 2.0:
        try:
            selection_list = OpenMaya2.MSelectionList()
            selection_list.add(f"{node}.{attr}")
            return selection_list.getPlug(0)
        except RuntimeError:
            return None

    return None
