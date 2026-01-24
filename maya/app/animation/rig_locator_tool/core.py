"""Core functions for rig locator tool."""

import logging
from typing import List, Tuple, Dict

import maya.cmds as cmds
from . import config
from ....lib.math import point as libPnt
from ....lib.attribute import core as libAttr
from ....lib.ui import timeline as libTimeline
from ....lib.node import namespace as libNamespace

log = logging.getLogger(__name__)

DIRECTION_DATA: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    "y": {
        "target_offset": (0, 1, 0),
        "aim_vector": (1, 0, 0),
        "up_vector": (0, 0, 1)
    },
    "z": {
        "target_offset": (0, 0, 1),
        "aim_vector": (0, 0, -1),
        "up_vector": (0, 1, 0)
    },
    "x": {
        "target_offset": (1, 0, 0),
        "aim_vector": (0, 1, 0),
        "up_vector": (0, 0, 1)
    }
}

COMPLETE_TYPE: List[str] = ["bake", "delete"]


def create_rig_locator(target_controls: List[str],
                       namespace: str,
                       cog_control: str,
                       base_name: str = "spine",
                       direction: str = "y",
                       distance_multiplier: int = 80,
                       include_translate: bool = False) -> None:
    """Create rig locator. Utilizing preset data provided.

    Create virtual locators, project animation from target controls, and bake it.
    User can modify animation with virtual locations non-destructively, and bake it if result is good.
    Otherwise, user can simply remove it.

    Args:
        target_controls: List of target controls.
        namespace: Namespace to attach.
        cog_control: Extra cog control to create macro virtual control.
        base_name: Base module name such as head or spine.
        direction: Direction can be y, z, and x.
        distance_multiplier: Direction multiply for offset.
        include_translate: Either include translate driver or not.
    """
    # make a list of selected objects
    physical_target_control = [libNamespace.replace_namespace(node=control, namespace=namespace) for control in
                               target_controls]
    target_cog_control = libNamespace.replace_namespace(node=cog_control, namespace=namespace)
    
    # transform snapshot
    all_old_transforms = cmds.ls(exactType="transform")
    
    # check control exists
    for control in physical_target_control + [target_cog_control]:
        if not cmds.objExists(control):
            raise ValueError("Control '{}' does not exist".format(control))

    # base root node, and no touch group
    root_node = libNamespace.replace_namespace("{}PARENT".format(base_name.upper()), namespace)
    no_touch_node = libNamespace.replace_namespace("{}_NO_TOUCH".format(base_name.upper()), namespace)

    # object exists check
    if cmds.objExists(root_node):
        raise ValueError("R-Locator Root Node '{}' already exists".format(root_node))

    # check if direction is valid input
    if direction not in DIRECTION_DATA:
        raise ValueError("Direction must be in {}".format(list(DIRECTION_DATA.keys())))

    # Cache direction data to avoid repeated lookups
    direction_data = DIRECTION_DATA[direction]
    translate_offset = [axis * distance_multiplier for axis in direction_data["target_offset"]]

    # create root node if not exists
    root_node = cmds.spaceLocator(name=root_node)[0]

    if not cmds.objExists(no_touch_node):
        no_touch_node = cmds.createNode("transform", name=no_touch_node, parent=root_node)

    cmds.setAttr("{}.visibility".format(no_touch_node), False)

    # recorded all created target locators
    aimspace_target_locs = []

    # for every item you have selected, do this for loop
    last_index = len(physical_target_control) - 1
    for target_index, target_control in enumerate(physical_target_control):
        # create hierarchy per provided control
        root_transform, offset_transform = build_rig_locator_block(namespace=namespace,
                                                                   name="{}_temp_aimspace_root".format(target_control),
                                                                   child_name="{}_temp_aimspace_offset".format(target_control),
                                                                   target_control=target_control,
                                                                   local_scale=(50.0, 50.0, 50.0))

        # Check if translate should be included for this control
        use_translate = include_translate and not cmds.getAttr("{}.translate".format(target_control), lock=True)
        
        # hide it if you don't need to use this controls
        if use_translate:
            cmds.parent(root_transform, root_node)
        else:
            cmds.parent(root_transform, no_touch_node)

        # create target transform
        target_root_transform, target_transform = build_rig_locator_block(namespace=namespace,
                                                                          name="{}_temp_aimspace_target_offset".format(target_control),
                                                                          child_name="{}_temp_aimspace_target".format(target_control))
        aimspace_target_locs.append(target_transform)
        apply_color(transform=target_transform, color_key="start")
        
        # match created cog locator to target cog control
        cmds.matchTransform(target_transform, target_control)
        cmds.xform(target_transform, objectSpace=True, relative=True, translation=translate_offset)
        cmds.parentConstraint(target_control, target_transform, maintainOffset=True)
        
        # bakes the root and target. then deletes constraints on them
        bake_and_clean(controls=[target_transform, target_root_transform, root_transform], attributes=["rx", "ry", "rz", "tx", "ty", "tz"])

        # create aim constraint between target and offset
        cmds.aimConstraint(target_transform,
                           offset_transform,
                           maintainOffset=True,
                           aimVector=direction_data["aim_vector"],
                           upVector=direction_data["up_vector"],
                           worldUpType="objectrotation",
                           worldUpVector=direction_data["up_vector"],
                           worldUpObject=root_transform)

        # reverse connection so locator drives control rig
        driver_control = physical_target_control[target_index - 1] if target_index > 0 else target_cog_control
        cmds.parentConstraint(driver_control, root_transform, maintainOffset=True, skipRotate=("x", "y", "z"))

        # bake translate offset
        pnt_cons = cmds.pointConstraint(target_control, offset_transform, maintainOffset=False)
        bake_and_clean(controls=[offset_transform], attributes=["tx", "ty", "tz"], remove_constraint=False)
        cmds.delete(pnt_cons)

        if use_translate:
            cmds.parentConstraint(offset_transform, target_control, maintainOffset=False)
        else:
            cmds.orientConstraint(offset_transform, target_control, maintainOffset=False)

        # parent accordingly depending on cases
        if target_index != last_index:
            cmds.parent(target_root_transform, no_touch_node)
        else:
            cmds.parent(target_root_transform, root_node)

    # add cog
    cog_transform, cog_child_transform = build_rig_locator_block(namespace=namespace,
                                                                 name="temp_Cog_{}".format(base_name),
                                                                 child_name="temp_Cog_{}_Child".format(base_name),
                                                                 target_control=target_cog_control,
                                                                 translate_offset=translate_offset)
    cmds.parent(cog_transform, root_node)
    apply_color(transform=cog_child_transform, color_key="end")
    
    # get normalize factor
    normalize_factor = 1.0 / len(aimspace_target_locs)
    for ii in range(len(aimspace_target_locs) - 1):
        # add mid
        mid_transform, mid_child_transform = build_rig_locator_block(namespace=namespace,
                                                                     name="temp_Mid_{}_{}".format(ii, base_name),
                                                                     child_name="temp_Mid_{}_{}_child".format(ii, base_name)
                                                                     )
        cmds.parent(mid_transform, root_node)
        apply_color(transform=mid_child_transform, color_key="mid")
        
        # first and last loc drive newly added mid loc
        cmds.pointConstraint(cog_child_transform, aimspace_target_locs[-1], mid_transform, maintainOffset=False)
        cmds.pointConstraint(cog_child_transform, mid_transform, edit=True, weight=1 - (normalize_factor * (ii + 1)))
        cmds.pointConstraint(aimspace_target_locs[-1], mid_transform, edit=True, weight=normalize_factor * (ii + 1))

        # bake anim in worldspace and do reverse connection
        cmds.pointConstraint(aimspace_target_locs[ii], mid_child_transform, maintainOffset=False)
        bake_and_clean(controls=mid_child_transform, attributes=["rx", "ry", "rz", "tx", "ty", "tz"])
        cmds.pointConstraint(mid_child_transform, aimspace_target_locs[ii], maintainOffset=False)
        
    # clean up - compare all the nodes created
    all_new_transforms = cmds.ls(exactType="transform")
    new_transforms = list(set(all_new_transforms) - set(all_old_transforms))
    
    for new_transform in new_transforms:
        # Lock and hide scale
        libAttr.lock_and_hide(new_transform, attrs=["scale"], propagate=True)
        
        # Lock channels connected to pairblend or constraint
        for axis in ("X", "Y", "Z"):
            for channel in ("translate", "rotate"):
                cons = cmds.listConnections("{}.{}{}".format(new_transform, channel, axis), source=True, destination=False)
                if not cons:
                    continue
                    
                for con in cons:
                    node_type = cmds.nodeType(con)
                    if node_type == "pairBlend" or "constraint" in cmds.nodeType(con, inherited=True):
                        libAttr.lock_and_hide(new_transform, attrs=["{}{}".format(channel, axis)])

    # select last animatable control
    cmds.select(aimspace_target_locs[-1])


def complete_rig_locator(base_name: str,
                         target_controls: List[str],
                         namespace: str,
                         complete_type: str = "bake") -> None:
    """Complete rig locator tool.

    Args:
        base_name: Base name of module such as spine, head.
        target_controls: List of target controls.
        namespace: Namespace fed from control rig.
        complete_type: How do you want to complete the tool? either bake or delete.
    """

    # root node name
    root_node = libNamespace.replace_namespace("{}PARENT".format(base_name.upper()), namespace)

    if not cmds.objExists(root_node):
        raise ValueError("Node '{}' does not exist".format(root_node))

    # complete type needs to be either bake or delete
    if complete_type not in ["bake", "delete"]:
        raise ValueError("complete_type must be in ['bake', 'delete']")

    if complete_type == "bake":
        physical_target_controls = [libNamespace.replace_namespace(node=control, namespace=namespace) for control in target_controls]
        bake_and_clean(controls=physical_target_controls, attributes=["rx", "ry", "rz", "tx", "ty", "tz"])

    # delete root node
    cmds.delete(root_node)


def bake_and_clean(controls: List[str], attributes: List[str], remove_constraint: bool = True) -> None:
    """Bake the animation in current time range.
    Run some cleaning process and remove constraints if any.

    Args:
        controls: List of control to be baked.
        attributes: List of attribute to be baked.
        remove_constraint: Either to remove constraint after bake or not.
    """

    if isinstance(controls, str):
        controls = [controls]

    if not all(cmds.objExists(control) for control in controls):
        raise ValueError("Controls '{}' do not exist".format(controls))

    # suspend refresh so it doesn't get calculated
    cmds.refresh(suspend=True)

    # bake anim from current playback range
    start_frame, end_frame = libTimeline.get_playback_start(), libTimeline.get_playback_end()
    cmds.bakeResults(controls, time=(start_frame, end_frame), attribute=attributes, simulation=True, preserveOutsideKeys=True)

    # we don't need any static channels
    cmds.delete(staticChannels=True)
    cmds.filterCurve()

    # remove constraint after baking
    if remove_constraint:
        cmds.delete(controls, constraints=True)

    # let's remove if there is any blend parent attribute as a product of constraint blend
    for control in controls:
        if cmds.objExists("{}.blendParent1".format(control)):
            cmds.deleteAttr("{}.blendParent1".format(control))

    # resume refresh
    cmds.refresh(suspend=False)


def build_rig_locator_block(namespace: str,
                            name: str,
                            child_name: str = None,
                            target_control: str = None,
                            local_scale: Tuple[float, float, float] = (10.0, 10.0, 10.0),
                            translate_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> List[str]:
    """Build a basic locator hierarchy with scale and template treatment
    and connect constraint if target_control is provided.

    transform
        |- child_transform

    Args:
        namespace: Name of namespace.
        name: Name of parent transform.
        child_name: Name of child transform.
        target_control: Target control that user wants to connect ParentConstraint from to parent_transform.
        local_scale: List of 3 floats for local locator scale.
        translate_offset: List of 3 float for translate offset.

    Returns:
        List of [parent transform, child transform].
    """

    if not name:
        return []

    if not child_name:
        child_name = "{}_child".format(name)

    # build locator hierarchy
    transform = cmds.spaceLocator(name=libNamespace.replace_namespace(name, namespace))[0]
    child_transform = cmds.spaceLocator(name=libNamespace.replace_namespace(child_name, namespace))[0]
    cmds.parent(child_transform, transform)

    # set template
    transform_shapes = cmds.listRelatives(transform, shapes=True)
    for transform_shape in transform_shapes:
        cmds.setAttr("{}.template".format(transform_shape), True)

    # set local scale for children
    cmds.setAttr("{}.localScale".format(child_transform), *local_scale)

    # without target_control, doesn't need to worry about constraint
    if not target_control:
        return [transform, child_transform]

    # get vector length to define either maintain offset or not
    vec_len = libPnt.get_chain_length([(0, 0, 0), translate_offset])

    # no need to set offset if value is too small
    if vec_len <= 0.001:
        maintain_offset = False
    else:
        maintain_offset = True

    # match created cog locator to target cog control
    cmds.matchTransform(transform, target_control)
    cmds.xform(transform, objectSpace=True, relative=True, translation=translate_offset)
    cmds.parentConstraint(target_control, transform, maintainOffset=maintain_offset)

    return [transform, child_transform]


def apply_color(transform: str, color_key: str = "start") -> None:
    """Simply apply the color to locator shape.
    
    Args:
        transform: Name of transform.
        color_key: Color key ('start', 'end', or 'mid').
    """
    if color_key not in config.DEFAULT_COLORS:
        raise ValueError("Color key must be in {}. '{}' is provided".format(list(config.DEFAULT_COLORS.keys()), color_key))
    
    loc_shapes = cmds.listRelatives(transform, children=True, type="locator")
    for loc_shape in loc_shapes:
        cmds.setAttr("{}.overrideEnabled".format(loc_shape), True)
        cmds.setAttr("{}.overrideRGBColors".format(loc_shape), True)
        cmds.setAttr("{}.overrideColorRGB".format(loc_shape), *config.DEFAULT_COLORS[color_key])
