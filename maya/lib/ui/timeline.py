"""Timeline utility functions for Maya playback and animation ranges."""

import maya.cmds as cmds


def get_playback_start() -> float:
    """Get the start frame of the playback range (inner timeline).

    Returns:
        The start frame of the playback range.
    """
    return cmds.playbackOptions(query=True, minTime=True)


def get_playback_end() -> float:
    """Get the end frame of the playback range (inner timeline).

    Returns:
        The end frame of the playback range.
    """
    return cmds.playbackOptions(query=True, maxTime=True)


def get_animation_start() -> float:
    """Get the start frame of the animation range (outer timeline).

    Returns:
        The start frame of the animation range.
    """
    return cmds.playbackOptions(query=True, animationStartTime=True)


def get_animation_end() -> float:
    """Get the end frame of the animation range (outer timeline).

    Returns:
        The end frame of the animation range.
    """
    return cmds.playbackOptions(query=True, animationEndTime=True)
