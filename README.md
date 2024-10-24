# Copy-Paste-Bone-Animation
Is a Python script used within Blender that copy and paste animation exclusively from and to multiple bones on an armature within the same or different Blender file.

Users can begin using the script by first opening it in Blender's Text Editor and run the script which will add the UI “Scripts” to the N Panel ready for use.


Script UI Content:


A single dropdown menu “Pasting Method:” which has two different pasting methods that can be set and changes the way the copied animation is pasted onto bones within the user’s selection.

“Copy Bone Animations” button which copies and stores the selected bone animations in an external temporary file that will be deleted once all open Blender files are closed.

“Paste Bone Animations” button that applies the stored bones animations to the bones within the user’s current selection based on the behaviour set by the user’s choice of pasting method. 


Feature Descriptions:


Pasting method “By Selection Order" is set by default and it copies and pastes animation based on the selection order of bones the user has selected when copying and pasting.

When copying animation from bones that have custom properties to bones that do not it will not receive the animation from the custom properties but only if they have custom properties of their own.

Pasting method “By Bone Name" when set it pastes the animation to bones within the users selection that  match the names of the bones that were copied, meaning that copying animation and then pasting it onto bones that do not share the same name as the bone that was copied within the users selection will not be pasted.

When copying animation from bones that have Custom Properties when using the pasting method “By Bone Name" the custom properties of the copied animation must also match the naming convention of the custom properties on the bone that is being pasted onto in order for the animation to be pasted successfully.

The user can copy single to multiple keyframes at once as well as individual transformation channels of bones with keyframes.

The script can paste the same copied animation multiple times until the user overwrites the stored animation by copying another one.

Keyframe Type can also be copied and pasted to and from bones.

When pasting animation the keyframes will be placed in the position where the user has position the Time Curser on the Time Line, Dope Sheet and Graph Editor.
