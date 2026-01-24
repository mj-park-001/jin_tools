"""Attribute utility functions."""

import logging
from typing import List, Tuple

import maya.cmds as cmds
from ..node import api as libNodeApi

log = logging.getLogger(__name__)


# PLUG RELATED

def get_node_attr(plug: str) -> Tuple[str, str]:
    """Split a plug name into node and attribute.

    Args:
        plug: The plug name (e.g., "pCube1.tx").

    Returns:
        A tuple of (node, attribute).
    """
    node, _, attr = plug.partition('.')
    return node, attr


def get_node(plug: str) -> str:
    """Get the node name from a plug."""
    return get_node_attr(plug)[0]


def get_attr(plug: str) -> str:
    """Get the attribute name from a plug."""
    return get_node_attr(plug)[1]


# COMPOUND RELATED

def is_compound_attr(plug: str) -> bool:
    """Check if a plug is a compound attribute."""
    node, attr = get_node_attr(plug)
    mplug = libNodeApi.get_mplug(node, attr)
    if mplug:
        return mplug.isCompound()
    return False


def get_children(plug: str) -> List[str]:
    """Get children attributes of a compound plug."""
    node, attr = get_node_attr(plug)
    mplug = libNodeApi.get_mplug(node, attr)

    if not mplug:
        return []

    children = []
    for i in range(mplug.numChildren()):
        child_plug = mplug.child(i)
        children.append(child_plug.info())

    return children


def lock(node: str, attrs: List[str], propagate: bool = False, action: bool = True) -> None:
    """Lock or unlock attributes on a node.

    Args:
        node: The node name.
        attrs: List of attributes to lock/unlock.
        propagate: If True, apply to children of compound attributes.
        action: True to lock, False to unlock.
    """
    for attr in attrs:
        plug = f"{node}.{attr}"
        if not cmds.objExists(plug):
            continue

        try:
            cmds.setAttr(plug, lock=action)
        except RuntimeError as e:
            log.error("Failed to lock attribute %s: %s", plug, e)

        if propagate and is_compound_attr(plug):
            children_plugs = get_children(plug)
            children_attrs = [get_attr(p) for p in children_plugs]
            lock(node, children_attrs, propagate=propagate, action=action)


def hide(node: str, attrs: List[str], propagate: bool = False, action: bool = True) -> None:
    """Hide or show attributes on a node.

    Args:
        node: The node name.
        attrs: List of attributes to hide/show.
        propagate: If True, apply to children of compound attributes.
        action: True to hide, False to show.
    """
    for attr in attrs:
        plug = f"{node}.{attr}"
        if not cmds.objExists(plug):
            continue

        display = not action

        try:
            if display:
                cmds.setAttr(plug, channelBox=display)
                cmds.setAttr(plug, keyable=display)
            else:
                cmds.setAttr(plug, keyable=display)
                cmds.setAttr(plug, channelBox=display)
        except RuntimeError as e:
            log.error("Failed to set display for attribute %s: %s", plug, e)

        if propagate and is_compound_attr(plug):
            children_plugs = get_children(plug)
            children_attrs = [get_attr(p) for p in children_plugs]
            hide(node, children_attrs, propagate=propagate, action=action)


def lock_and_hide(node: str, attrs: List[str], propagate: bool = False) -> None:
    """Lock and hide attributes on a node.

    Args:
        node: The node name.
        attrs: List of attributes to lock/hide.
        propagate: If True, apply to children of compound attributes.
    """
    lock(node, attrs, propagate=propagate)
    hide(node, attrs, propagate=propagate)
