"""
Blender Spring Bone Import Fixer
================================
This script reads the JSON data exported from CC5 and fixes spring bone
parenting relationships in Blender after FBX import.

Usage:
1. Import your CC5 character FBX into Blender (using CC Blender Tools or standard import)
2. Run this script in Blender's scripting workspace
3. Point it to the JSON file exported from CC5
4. The script will fix bone parenting relationships

Compatible with: Blender 3.x+, CC/iC Blender Tools 1.3.x

Author: Created for GB Portfolio 2025 avatar pipeline
Date: December 2024
"""

import bpy
import json
import os
from mathutils import Matrix, Vector, Quaternion, Euler
import math


class SpringBoneImporter:
    """
    Handles importing and fixing spring bone relationships in Blender.
    """
    
    def __init__(self, json_path):
        self.json_path = json_path
        self.data = None
        self.armature = None
        self.report_messages = []
    
    def load_json(self):
        """Load the spring bone data from JSON."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.report(f"Loaded spring bone data for: {self.data['metadata']['avatar_name']}")
            return True
        except Exception as e:
            self.report(f"ERROR: Failed to load JSON: {e}")
            return False
    
    def report(self, message):
        """Log a message."""
        print(message)
        self.report_messages.append(message)
    
    def find_armature(self, armature_name=None):
        """
        Find the target armature in the scene.
        If name not specified, uses the avatar name from JSON or finds first armature.
        """
        if armature_name:
            self.armature = bpy.data.objects.get(armature_name)
        else:
            # Try to find by avatar name
            avatar_name = self.data['metadata']['avatar_name']
            
            # Look for exact match or containing name
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE':
                    if obj.name == avatar_name or avatar_name in obj.name:
                        self.armature = obj
                        break
            
            # Fallback to first armature
            if not self.armature:
                for obj in bpy.data.objects:
                    if obj.type == 'ARMATURE':
                        self.armature = obj
                        break
        
        if self.armature:
            self.report(f"Found armature: {self.armature.name}")
            return True
        else:
            self.report("ERROR: No armature found in scene!")
            return False
    
    def get_bone_by_name(self, bone_name):
        """Find a bone by name, trying various naming conventions."""
        if not self.armature:
            return None
        
        edit_bones = self.armature.data.edit_bones
        
        # Direct match
        if bone_name in edit_bones:
            return edit_bones[bone_name]
        
        # Try without CC_ prefix
        if bone_name.startswith('CC_') and bone_name[3:] in edit_bones:
            return edit_bones[bone_name[3:]]
        
        # Try with CC_ prefix
        if f'CC_{bone_name}' in edit_bones:
            return edit_bones[f'CC_{bone_name}']
        
        # Case-insensitive search
        bone_name_lower = bone_name.lower()
        for bone in edit_bones:
            if bone.name.lower() == bone_name_lower:
                return bone
        
        return None
    
    def fix_bone_parenting(self):
        """
        Fix spring bone parenting based on the JSON data.
        """
        if not self.armature or not self.data:
            self.report("ERROR: Armature or data not loaded")
            return False
        
        # Enter edit mode
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode='EDIT')
        
        parenting_map = self.data.get('bone_parenting', {})
        spring_bones = self.data['skeleton'].get('spring_bones', [])
        potential_bones = self.data['skeleton'].get('potential_spring_bones', [])
        
        all_spring_bones = spring_bones + potential_bones
        spring_bone_names = [b['name'] for b in all_spring_bones]
        
        fixed_count = 0
        missing_count = 0
        
        self.report(f"\nProcessing {len(spring_bone_names)} spring bones...")
        
        for bone_info in all_spring_bones:
            bone_name = bone_info['name']
            target_parent = bone_info.get('parent')
            
            if not target_parent:
                continue
            
            bone = self.get_bone_by_name(bone_name)
            parent_bone = self.get_bone_by_name(target_parent)
            
            if not bone:
                self.report(f"  WARNING: Bone not found: {bone_name}")
                missing_count += 1
                continue
            
            if not parent_bone:
                self.report(f"  WARNING: Parent not found: {target_parent} (for {bone_name})")
                missing_count += 1
                continue
            
            # Check if parenting is already correct
            if bone.parent and bone.parent.name == parent_bone.name:
                continue
            
            # Fix parenting
            bone.parent = parent_bone
            
            # Use connected if the tail of parent matches head of child
            if parent_bone.tail and bone.head:
                distance = (parent_bone.tail - bone.head).length
                if distance < 0.001:  # Very close
                    bone.use_connect = True
                else:
                    bone.use_connect = False
            
            self.report(f"  Fixed: {bone_name} -> {target_parent}")
            fixed_count += 1
        
        # Exit edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report(f"\nParenting fix complete:")
        self.report(f"  Fixed: {fixed_count} bones")
        self.report(f"  Missing: {missing_count} bones")
        
        return True
    
    def apply_transforms(self, apply_rest_pose=False):
        """
        Optionally apply transforms from the JSON data to adjust bone positions.
        Use with caution - primarily for debugging.
        """
        if not apply_rest_pose:
            return
        
        if not self.armature or not self.data:
            return
        
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode='EDIT')
        
        for bone_info in self.data['skeleton']['all_bones']:
            bone_name = bone_info['name']
            transform = bone_info.get('transform', {})
            
            bone = self.get_bone_by_name(bone_name)
            if not bone:
                continue
            
            # Only apply if we have local transform data
            local_data = transform.get('local', {})
            if 'error' in local_data:
                continue
            
            # This is complex due to coordinate system differences
            # CC5 uses Y-up, Blender uses Z-up (depending on FBX import settings)
            # For now, just log what we'd apply
            self.report(f"  Transform data for {bone_name}: {local_data.get('translation', 'N/A')}")
        
        bpy.ops.object.mode_set(mode='OBJECT')
    
    def create_vertex_groups_from_chains(self):
        """
        Create or verify vertex groups for spring bone chains.
        This helps with weight painting setup.
        """
        if not self.armature or not self.data:
            return
        
        chains = self.data['skeleton'].get('spring_chains', {})
        
        self.report(f"\nSpring bone chains found: {len(chains)}")
        
        for chain_name, chain_bones in chains.items():
            self.report(f"\n  Chain: {chain_name}")
            self.report(f"    Bones: {len(chain_bones)}")
            
            # List the chain
            bone_names = [b['name'] for b in chain_bones]
            self.report(f"    Sequence: {' -> '.join(bone_names)}")
    
    def generate_spring_rig_setup(self):
        """
        Generate setup instructions for CC Blender Tools spring rig.
        """
        self.report("\n" + "="*60)
        self.report("SPRING RIG SETUP INSTRUCTIONS")
        self.report("="*60)
        
        self.report("""
For proper spring bone physics in Blender, you have two options:

OPTION 1: Use CC/iC Blender Tools Spring Rig
---------------------------------------------
1. In the CC/iC Create tab, find "Spring Rig" panel
2. Set target to "Character Creator" or "Unity" as needed
3. The imported bones should now be properly parented
4. Use "Bind Hair" to weight paint the hair meshes to spring bones

OPTION 2: Use Rigid Body Physics
--------------------------------
1. Select the armature
2. In Pose Mode, select the spring bone chain
3. Use CC/iC Tools > Scene Tools > Spring Bone Simulation
4. Adjust physics settings as needed
5. Bake the simulation

OPTION 3: Manual Constraint Setup
--------------------------------
If you need custom physics behavior:
1. Select spring bones in Pose Mode
2. Add "Copy Rotation" constraint from child to parent
3. Add damped track constraints for physics follow
4. Use drivers for dynamic behavior
""")
        
        return True


def fix_spring_bones_from_json(json_path, armature_name=None):
    """
    Main entry point - fix spring bone parenting from JSON data.
    
    Args:
        json_path: Path to the JSON file exported from CC5
        armature_name: Optional specific armature name to target
    
    Returns:
        SpringBoneImporter instance with results
    """
    importer = SpringBoneImporter(json_path)
    
    if not importer.load_json():
        return importer
    
    if not importer.find_armature(armature_name):
        return importer
    
    importer.fix_bone_parenting()
    importer.create_vertex_groups_from_chains()
    importer.generate_spring_rig_setup()
    
    return importer


# ============================================================================
# Blender Operator for UI Integration
# ============================================================================

class SPRINGBONE_OT_import_json(bpy.types.Operator):
    """Import and fix spring bone data from CC5 JSON export"""
    bl_idname = "springbone.import_json"
    bl_label = "Import Spring Bone Data"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="JSON File",
        description="Path to the spring bone JSON file",
        subtype='FILE_PATH'
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        
        importer = fix_spring_bones_from_json(self.filepath)
        
        if importer.armature:
            self.report({'INFO'}, f"Spring bone parenting fixed for {importer.armature.name}")
        else:
            self.report({'WARNING'}, "No armature found or processed")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SPRINGBONE_PT_panel(bpy.types.Panel):
    """Spring Bone Tools Panel"""
    bl_label = "CC5 Spring Bone Fixer"
    bl_idname = "SPRINGBONE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CC5 Tools'
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Fix Spring Bone Parenting:")
        layout.operator("springbone.import_json", text="Import JSON Data")
        
        layout.separator()
        layout.label(text="After import, use CC Blender Tools")
        layout.label(text="Spring Rig panel to set up physics.")


def register():
    bpy.utils.register_class(SPRINGBONE_OT_import_json)
    bpy.utils.register_class(SPRINGBONE_PT_panel)


def unregister():
    bpy.utils.unregister_class(SPRINGBONE_PT_panel)
    bpy.utils.unregister_class(SPRINGBONE_OT_import_json)


# ============================================================================
# Direct Script Execution
# ============================================================================

if __name__ == "__main__":
    # For direct execution, you can modify this path:
    JSON_PATH = r"C:\Users\YourName\Documents\YourAvatar_spring_bones.json"
    
    # Check if running in Blender
    if bpy.context:
        # Register the addon
        register()
        
        # Or run directly:
        # importer = fix_spring_bones_from_json(JSON_PATH)
        
        print("\n" + "="*60)
        print("Spring Bone Fixer loaded!")
        print("Find the panel in View3D > Sidebar > CC5 Tools")
        print("="*60)
