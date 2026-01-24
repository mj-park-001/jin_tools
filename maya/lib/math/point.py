"""Math utility functions for working with Maya points."""

from typing import List, Tuple, Union, Any

import maya.OpenMaya as OpenMaya
import maya.cmds as cmds


def to_mpoint(point: Union[OpenMaya.MPoint, List[float], Tuple[float, float, float]]) -> OpenMaya.MPoint:
    """Convert a point-like object to an OpenMaya.MPoint.

    Args:
        point: The input point. Can be an MPoint, list, or tuple.

    Returns:
        An OpenMaya.MPoint object.
    """
    if isinstance(point, OpenMaya.MPoint):
        return point
    return OpenMaya.MPoint(point[0], point[1], point[2])


def to_mpoint_array(points: Union[OpenMaya.MPointArray, List[Any], Tuple[Any, ...]]) -> OpenMaya.MPointArray:
    """Convert a collection of points to an OpenMaya.MPointArray.

    Args:
        points: The input points. Can be an MPointArray, list of points, or other Maya array types.

    Returns:
        An OpenMaya.MPointArray object.

    Raises:
        RuntimeError: If the input cannot be converted.
    """
    if isinstance(points, OpenMaya.MPointArray):
        return points

    mpoint_array = OpenMaya.MPointArray()

    if isinstance(points, (list, tuple)):
        mpoint_array.setLength(len(points))
        for i, point in enumerate(points):
            mpoint_array.set(i, point[0], point[1], point[2])
        return mpoint_array

    if isinstance(points, (OpenMaya.MFloatPointArray, OpenMaya.MVectorArray, OpenMaya.MFloatVectorArray)):
        length = points.length()
        mpoint_array.setLength(length)
        for i in range(length):
            mpoint_array.set(i, points[i][0], points[i][1], points[i][2])
        return mpoint_array

    cmds.error(f'Bad conversion, {points} must be a MPointArray, MFloatPointArray, MVectorArray, MFloatVectorArray, tuple or list')


def get_chain_length(points: Union[OpenMaya.MPointArray, List[Any]]) -> float:
    """Calculate the total length of a chain of points.

    Args:
        points: The points in the chain.

    Returns:
        The total length of the chain.
    """
    mpoints = to_mpoint_array(points)
    length = 0.0
    for i in range(mpoints.length() - 1):
        length += mpoints[i].distanceTo(mpoints[i + 1])
    return length
