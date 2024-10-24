import bpy
import json
import os

# Define the path for the external file to store bone keyframe data
EXTERNAL_FILE_PATH = os.path.join(bpy.utils.resource_path('USER'), "bone_animation_data.json")

# Utility functions for saving and loading keyframe data
def save_keyframes_to_file(bone_keyframes):
    """Save bone keyframes data for multiple bones to an external JSON file."""
    with open(EXTERNAL_FILE_PATH, 'w') as file:
        json.dump(bone_keyframes, file)

def load_keyframes_from_file():
    """Load bone keyframes data for multiple bones from an external JSON file."""
    if os.path.exists(EXTERNAL_FILE_PATH):
        with open(EXTERNAL_FILE_PATH, 'r') as file:
            return json.load(file)
    return []

# Utility function for copying keyframes of selected bones across the timeline
def copy_bone_keyframes(obj, bone_name):
    """Copy all keyframes for a given bone across the entire timeline, including types."""
    action = obj.animation_data.action
    keyframes = []
    if action:
        for fcurve in action.fcurves:
            # Check if the fcurve belongs to the specified bone
            if fcurve.data_path.startswith(f'pose.bones["{bone_name}"]'):
                # Detect if it's a custom property (identified by double square brackets)
                if '"]["' in fcurve.data_path:
                    # Custom property detected
                    transform_type = 'custom_property'
                else:
                    # Identify if it's location, rotation, or scale
                    if 'location' in fcurve.data_path:
                        transform_type = 'location'
                    elif 'rotation' in fcurve.data_path:
                        transform_type = 'rotation'
                    elif 'scale' in fcurve.data_path:
                        transform_type = 'scale'
                    else:
                        continue  # Skip non-transform fcurves

                # Store keyframe data, including frame, value, and keyframe type
                for keyframe_point in fcurve.keyframe_points:
                    keyframes.append({
                        "data_path": fcurve.data_path,
                        "array_index": fcurve.array_index,
                        "transform_type": transform_type,
                        "frame": keyframe_point.co[0],
                        "value": keyframe_point.co[1],
                        "keyframe_type": keyframe_point.type  # Store keyframe type
                    })
    return keyframes

# Utility function to ensure an action group exists for a bone's keyframes
def ensure_action_group(action, bone_name, fcurve):
    """Ensure that the FCurve is assigned to the bone's action group."""
    group_name = bone_name
    group = action.groups.get(group_name)
    if not group:
        group = action.groups.new(name=group_name)
    fcurve.group = group

# Assign correct colors to f-curves based on axis and transformation type
def assign_fcurve_color(fcurve, array_index, transform_type):
    """Ensure the fcurve has the correct axis color (X=Red, Y=Green, Z=Blue)."""
    fcurve.color_mode = 'AUTO_RGB'
    if transform_type == 'location' or transform_type == 'rotation' or transform_type == 'scale':
        if array_index == 0:  # X-axis
            fcurve.color = (1.0, 0.0, 0.0)  # Red
        elif array_index == 1:  # Y-axis
            fcurve.color = (0.0, 1.0, 0.0)  # Green
        elif array_index == 2:  # Z-axis
            fcurve.color = (0.0, 0.0, 1.0)  # Blue

# Utility function to apply keyframes, adjusting based on time cursor
def apply_bone_keyframes(obj, bone_name, keyframes, cursor_frame, flexible=False):
    """Apply keyframes to the given bone, adjusting them relative to the time cursor."""
    if not keyframes:
        return 0  # Return 0 custom properties missed if no keyframes
    
    action = obj.animation_data.action
    if not action:
        action = bpy.data.actions.new(name="BoneAction")
        obj.animation_data.action = action

    # Get the first keyframe to calculate the offset
    first_keyframe = keyframes[0]['frame']
    frame_offset = cursor_frame - first_keyframe  # Adjust frames based on time cursor

    # Track custom properties that couldn't be applied
    missed_custom_properties = 0

    for keyframe in keyframes:
        data_path = keyframe["data_path"]
        array_index = keyframe["array_index"]
        frame = keyframe["frame"] + frame_offset  # Shift keyframe based on time cursor
        value = keyframe["value"]
        transform_type = keyframe["transform_type"]
        keyframe_type = keyframe.get("keyframe_type", 0)  # Get the keyframe type (default 0)

        # For custom properties, ensure the bone has the custom property before applying
        if transform_type == 'custom_property':
            custom_property_name = data_path.split('"]["')[1].replace('"]', '')
            if custom_property_name not in obj.pose.bones[bone_name]:
                missed_custom_properties += 1  # Count the custom property that cannot be pasted
                continue  # Skip if the target bone does not have the custom property

        # Ensure the data path reflects the correct bone property
        if flexible and transform_type != 'custom_property':
            # In flexible mode, keep the property but change the bone name to the current bone
            base_data_path = data_path.split('pose.bones["')[1].split('"]')[1]  # Get the property part
            data_path = f'pose.bones["{bone_name}"]{base_data_path}'  # Assign new bone name but keep property

        # Find or create the FCurve for the given data path and array index
        fcurve = action.fcurves.find(data_path, index=array_index)
        if not fcurve:
            fcurve = action.fcurves.new(data_path, index=array_index)

        # Ensure the FCurve is part of the bone's action group
        ensure_action_group(action, bone_name, fcurve)

        # Insert keyframe at the adjusted frame with the corresponding value
        keyframe_point = fcurve.keyframe_points.insert(frame, value, options={'FAST'})
        keyframe_point.type = keyframe_type  # Set the keyframe type (e.g., Jitter, Breakdown)

        # Assign the correct axis color to the f-curve if it's not a custom property
        if transform_type != 'custom_property':
            assign_fcurve_color(fcurve, array_index, transform_type)

    return missed_custom_properties

# Operators for copying and applying bone keyframes
class POSE_OT_CopyBoneKeyframes(bpy.types.Operator):
    bl_idname = "pose.copy_bone_keyframes"
    bl_label = "Copy Bone Animations"
    bl_description = "Copy keyframes from selected bones, including keyframe types"

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'ARMATURE' and context.mode == 'POSE':
            selected_bones = context.selected_pose_bones
            if selected_bones:
                bone_keyframes = {}
                for bone in selected_bones:
                    keyframes = copy_bone_keyframes(obj, bone.name)
                    if keyframes:  # Only store keyframes if they exist
                        bone_keyframes[bone.name] = keyframes

                save_keyframes_to_file(bone_keyframes)
                self.report({'INFO'}, f"Copied animations for {len(bone_keyframes)} bones, including keyframe types.")
            else:
                self.report({'WARNING'}, "No bones selected.")
        else:
            self.report({'WARNING'}, "Select an armature in pose mode.")
        return {'FINISHED'}

class POSE_OT_PasteBoneKeyframes(bpy.types.Operator):
    bl_idname = "pose.paste_bone_keyframes"
    bl_label = "Paste Bone Animations"
    bl_description = "Paste copied keyframes to selected bones based on selection order or bone name, including keyframe types"

    def execute(self, context):
        obj = context.active_object
        cursor_frame = context.scene.frame_current  # Get the current time cursor frame
        if obj and obj.type == 'ARMATURE' and context.mode == 'POSE':
            selected_bones = context.selected_pose_bones
            stored_bone_keyframes = load_keyframes_from_file()

            if selected_bones and stored_bone_keyframes:
                # Get the pasting method from the dropdown property
                pasting_method = context.scene.bone_pasting_method
                num_to_apply = min(len(selected_bones), len(stored_bone_keyframes))
                total_missed_custom_properties = 0

                if pasting_method == 'ORDER':
                    # Flexible pasting based strictly on the selection order
                    for bone, (stored_bone_name, keyframes) in zip(selected_bones, stored_bone_keyframes.items()):
                        missed_custom_properties = apply_bone_keyframes(obj, bone.name, keyframes, cursor_frame, flexible=True)
                        total_missed_custom_properties += missed_custom_properties

                    self.report({'INFO'}, f"Pasted animations by selection order.")

                elif pasting_method == 'NAME':
                    # Strict pasting based on matching bone names
                    for bone in selected_bones:
                        if bone.name in stored_bone_keyframes:
                            keyframes = stored_bone_keyframes[bone.name]
                            missed_custom_properties = apply_bone_keyframes(obj, bone.name, keyframes, cursor_frame)
                            total_missed_custom_properties += missed_custom_properties
                        else:
                            self.report({'WARNING'}, f"No matching data for bone '{bone.name}', skipping.")

                    self.report({'INFO'}, f"Pasted animations by matching bone name.")

                # Report the number of missed custom properties
                if total_missed_custom_properties > 0:
                    self.report({'WARNING'}, f"{total_missed_custom_properties} custom properties could not be pasted due to missing properties on target bones.")

            else:
                self.report({'WARNING'}, "No bones selected or no stored animations available.")
        else:
            self.report({'WARNING'}, "Select an armature in pose mode.")
        return {'FINISHED'}

# Panel for the UI with dropdown to select pasting method
class POSE_PT_BoneAnimationPanel(bpy.types.Panel):
    bl_idname = "POSE_PT_bone_animation_panel"
    bl_label = "Copy & Paste Bone Animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Scripts"

    def draw(self, context):
        layout = self.layout

        # Dropdown for selecting pasting method
        layout.prop(context.scene, "bone_pasting_method", text="Pasting Method")

        row = layout.row()
        row.operator("pose.copy_bone_keyframes", text="Copy Bone Animations", icon='COPYDOWN')

        row = layout.row()
        row.operator("pose.paste_bone_keyframes", text="Paste Bone Animations", icon='PASTEDOWN')

# Property for dropdown menu to select pasting method
def add_bone_pasting_method_property():
    bpy.types.Scene.bone_pasting_method = bpy.props.EnumProperty(
        name="Bone Pasting Method",
        description="Select how bone animations should be pasted",
        items=[
            ('ORDER', "By Selection Order", "Paste based on the order of selected bones"),
            ('NAME', "By Bone Name", "Paste based on matching bone names first, then selection order"),
        ],
        default='ORDER',  # Default to 'By Selection Order'
    )

# Register and unregister functions
def register():
    bpy.utils.register_class(POSE_OT_CopyBoneKeyframes)
    bpy.utils.register_class(POSE_OT_PasteBoneKeyframes)
    bpy.utils.register_class(POSE_PT_BoneAnimationPanel)
    add_bone_pasting_method_property()

def unregister():
    bpy.utils.unregister_class(POSE_OT_CopyBoneKeyframes)
    bpy.utils.unregister_class(POSE_OT_PasteBoneKeyframes)
    bpy.utils.unregister_class(POSE_PT_BoneAnimationPanel)
    del bpy.types.Scene.bone_pasting_method

if __name__ == "__main__":
    register()
