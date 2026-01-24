"""Functions to help with working with namespaces"""

import logging
from typing import Tuple, List

from maya import cmds

log = logging.getLogger(__name__)


def get_namespace_and_node(node: str) -> Tuple[str, str]:
    """Get the namespace and exact node name.

    Args:
        node: The node name.

    Returns:
        A tuple containing (namespace, node_name).
    """
    namespace, separator, name = str(node).rpartition('|')[-1].rpartition(':')

    return namespace, name


def get_namespace(node: str) -> str:
    """Get the namespace for the given node.

    Args:
        node: The node name.

    Returns:
        The namespace of the node.
    """
    return get_namespace_and_node(node)[0]


def get_node(node: str) -> str:
    """Only get the exact node name without the namespace or parents.

    Args:
        node: The node name.

    Returns:
        The node name without namespace or path.
    """
    return get_namespace_and_node(node)[1]


def get_namespaces(nodes: List[str]) -> List[str]:
    """Return unique namespaces from the given nodes, preserving order.

    Args:
        nodes: The node names.

    Returns:
        List of unique namespaces.
    """
    return list(dict.fromkeys(get_namespace(node) for node in nodes))


def replace_namespace(node: str, namespace: str) -> str:
    """Return the node path string with the specified namespace applied.

    Args:
        node: The node name.
        namespace: The new namespace (can be None or empty for no namespace).

    Returns:
        The modified node name with the new namespace.
    """
    path = node.split('|')
    path = [get_node(name) for name in path]
    
    if not namespace:
        # No namespace - return plain node names
        return '|'.join([name if name else '' for name in path])
    
    if not namespace.endswith(':'):
        namespace += ':'

    return '|'.join(['{}{}'.format(namespace, name) if name else '' for name in path])
