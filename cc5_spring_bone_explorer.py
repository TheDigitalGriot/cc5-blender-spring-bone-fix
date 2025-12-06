"""
CC5 Spring Bone Explorer and Exporter
=====================================
This script explores the RLPy API in Character Creator 5 to extract
spring bone hierarchy and relationship data for proper Blender import.

Usage:
1. Open Character Creator 5 with your character loaded (including hair with spring bones)
2. Go to Plugins > Python > Load Python
3. Load this script
4. Check the Console/Log window for output
5. JSON file will be saved alongside your character

Author: Created for GB Portfolio 2025 avatar pipeline
Date: December 2024
"""

import RLPy
import json
import os
from datetime import datetime

# ============================================================================
# PART 1: API EXPLORATION - Run this first to discover available methods
# ============================================================================

def explore_rlpy_api():
    """
    Explore the RLPy module to discover available classes and methods.
    This helps identify physics-related APIs that may not be documented.
    """
    print("\n" + "="*80)
    print("EXPLORING RLPy API")
    print("="*80)
    
    # Get all RLPy members
    all_members = dir(RLPy)
    
    # Filter for potentially physics-related items
    physics_keywords = ['physics', 'spring', 'cloth', 'soft', 'rigid', 'collision', 
                       'dynamic', 'constraint', 'joint', 'physx', 'simulation']
    
    print("\n--- Potential Physics-Related Classes/Functions ---")
    for member in all_members:
        member_lower = member.lower()
        if any(keyword in member_lower for keyword in physics_keywords):
            print(f"  {member}")
    
    # Look for Component-related classes
    print("\n--- Component Classes ---")
    for member in all_members:
        if 'Component' in member or 'component' in member:
            print(f"  {member}")
    
    # Look for Bone-related classes
    print("\n--- Bone/Skeleton Classes ---")
    for member in all_members:
        if 'Bone' in member or 'Skeleton' in member or 'bone' in member:
            print(f"  {member}")
    
    return all_members


def explore_avatar_methods(avatar):
    """
    Explore all available methods on an avatar object.
    """
    print("\n" + "="*80)
    print("EXPLORING AVATAR METHODS")
    print("="*80)
    
    methods = [m for m in dir(avatar) if not m.startswith('_')]
    
    # Group by type
    get_methods = [m for m in methods if m.startswith('Get')]
    set_methods = [m for m in methods if m.startswith('Set')]
    other_methods = [m for m in methods if not m.startswith('Get') and not m.startswith('Set')]
    
    print("\n--- Get Methods (data retrieval) ---")
    for m in sorted(get_methods):
        print(f"  {m}")
    
    print("\n--- Set Methods (data modification) ---")
    for m in sorted(set_methods):
        print(f"  {m}")
        
    print("\n--- Other Methods ---")
    for m in sorted(other_methods):
        print(f"  {m}")


def explore_skeleton_component(skeleton_component):
    """
    Deep dive into skeleton component methods and data.
    """
    print("\n" + "="*80)
    print("EXPLORING SKELETON COMPONENT")
    print("="*80)
    
    methods = [m for m in dir(skeleton_component) if not m.startswith('_')]
    
    print("\n--- Skeleton Component Methods ---")
    for m in sorted(methods):
        print(f"  {m}")
    
    # Try to call common methods
    print("\n--- Testing Common Methods ---")
    
    try:
        root_bone = skeleton_component.GetRootBone()
        print(f"  GetRootBone(): {root_bone.GetName() if root_bone else 'None'}")
    except Exception as e:
        print(f"  GetRootBone(): Error - {e}")
    
    try:
        motion_bones = skeleton_component.GetMotionBones()
        print(f"  GetMotionBones(): {len(motion_bones) if motion_bones else 0} bones")
    except Exception as e:
        print(f"  GetMotionBones(): Error - {e}")
    
    try:
        skin_bones = skeleton_component.GetSkinBones()
        print(f"  GetSkinBones(): {len(skin_bones) if skin_bones else 0} bones")
    except Exception as e:
        print(f"  GetSkinBones(): Error - {e}")
    
    try:
        clip_count = skeleton_component.GetClipCount()
        print(f"  GetClipCount(): {clip_count}")
    except Exception as e:
        print(f"  GetClipCount(): Error - {e}")


def explore_bone_node(bone_node, depth=0):
    """
    Explore methods available on a bone node.
    """
    if depth == 0:
        print("\n" + "="*80)
        print("EXPLORING BONE NODE METHODS")
        print("="*80)
        
        methods = [m for m in dir(bone_node) if not m.startswith('_')]
        print("\n--- Bone Node Methods ---")
        for m in sorted(methods):
            print(f"  {m}")


# ============================================================================
# PART 2: SPRING BONE DATA EXTRACTION
# ============================================================================

def find_bone_by_name(skeleton_component, bone_name):
    """
    Find a specific bone by name in the skeleton.
    """
    # Check skin bones
    skin_bones = skeleton_component.GetSkinBones()
    if skin_bones:
        for bone in skin_bones:
            if bone.GetName() == bone_name:
                return bone
    
    # Check motion bones
    motion_bones = skeleton_component.GetMotionBones()
    if motion_bones:
        for bone in motion_bones:
            if bone.GetName() == bone_name:
                return bone
    
    return None


def get_transform_data(bone_node):
    """
    Extract transform data from a bone node.
    """
    transform_data = {}
    
    try:
        # Local transform
        local_transform = bone_node.LocalTransform()
        local_t = local_transform.T()
        local_r = local_transform.R()
        local_s = local_transform.S()
        
        transform_data['local'] = {
            'translation': [local_t.x, local_t.y, local_t.z],
            'rotation': [local_r.x, local_r.y, local_r.z, local_r.w] if hasattr(local_r, 'w') else [local_r.x, local_r.y, local_r.z],
            'scale': [local_s.x, local_s.y, local_s.z]
        }
    except Exception as e:
        transform_data['local'] = {'error': str(e)}
    
    try:
        # World transform
        world_transform = bone_node.WorldTransform()
        world_t = world_transform.T()
        world_r = world_transform.R()
        world_s = world_transform.S()
        
        transform_data['world'] = {
            'translation': [world_t.x, world_t.y, world_t.z],
            'rotation': [world_r.x, world_r.y, world_r.z, world_r.w] if hasattr(world_r, 'w') else [world_r.x, world_r.y, world_r.z],
            'scale': [world_s.x, world_s.y, world_s.z]
        }
    except Exception as e:
        transform_data['world'] = {'error': str(e)}
    
    return transform_data


def traverse_bone_hierarchy(bone_node, depth=0, bone_data=None):
    """
    Recursively traverse bone hierarchy and collect data.
    """
    if bone_data is None:
        bone_data = []
    
    bone_info = {
        'name': bone_node.GetName(),
        'id': str(bone_node.GetID()) if hasattr(bone_node, 'GetID') else None,
        'depth': depth,
        'parent': None,
        'children': [],
        'transform': get_transform_data(bone_node)
    }
    
    # Get parent
    parent = bone_node.GetParent()
    if parent:
        bone_info['parent'] = parent.GetName()
    
    # Get children
    children = bone_node.GetChildren()
    if children:
        for child in children:
            bone_info['children'].append(child.GetName())
    
    bone_data.append(bone_info)
    
    # Recurse into children
    if children:
        for child in children:
            traverse_bone_hierarchy(child, depth + 1, bone_data)
    
    return bone_data


def identify_spring_bones(all_bones):
    """
    Identify spring bones from the bone list using naming conventions.
    
    Common spring bone naming patterns:
    - CC_Hair_Spine01, CC_Hair_Spine02, etc.
    - Hair_Spring_*, Spring_*, etc.
    - Bones parented to head/neck that aren't standard skeleton bones
    """
    spring_bone_patterns = [
        'spring', 'spine', 'hair_', 'ponytail', 'braid', 'tail_',
        'ribbon', 'accessory', 'dynamic', 'phys_', 'cloth_'
    ]
    
    standard_bones = [
        'CC_Base_', 'RL_', 'root', 'pelvis', 'spine', 'chest', 'neck', 'head',
        'shoulder', 'arm', 'forearm', 'hand', 'finger', 'thumb', 'leg', 'thigh',
        'calf', 'foot', 'toe', 'hip', 'waist', 'breast', 'eye', 'jaw', 'teeth',
        'tongue', 'brow', 'cheek', 'nostril', 'lip'
    ]
    
    spring_bones = []
    potential_spring_bones = []
    
    for bone in all_bones:
        bone_name = bone['name'].lower()
        
        # Check if it matches spring bone patterns
        is_spring = any(pattern in bone_name for pattern in spring_bone_patterns)
        
        # Check if it's NOT a standard skeleton bone
        is_standard = any(std in bone_name for std in standard_bones)
        
        if is_spring:
            spring_bones.append(bone)
        elif not is_standard and bone['parent']:
            # Check if parented to head/neck (common for hair springs)
            parent_lower = bone['parent'].lower()
            if 'head' in parent_lower or 'neck' in parent_lower:
                potential_spring_bones.append(bone)
    
    return spring_bones, potential_spring_bones


def build_spring_chains(spring_bones):
    """
    Organize spring bones into chains (connected bone sequences).
    """
    chains = {}
    
    # Create a lookup by name
    bone_lookup = {bone['name']: bone for bone in spring_bones}
    
    # Find root bones (bones whose parent is not in the spring bone set)
    spring_names = set(bone_lookup.keys())
    
    for bone in spring_bones:
        parent = bone['parent']
        if parent not in spring_names:
            # This is a chain root
            chain_name = bone['name']
            chain = []
            
            # Follow the chain
            current = bone
            while current:
                chain.append({
                    'name': current['name'],
                    'parent': current['parent'],
                    'transform': current['transform']
                })
                
                # Find child in spring set
                next_bone = None
                for child_name in current.get('children', []):
                    if child_name in spring_names:
                        next_bone = bone_lookup[child_name]
                        break
                current = next_bone
            
            chains[chain_name] = chain
    
    return chains


# ============================================================================
# PART 3: MESH AND PHYSICS WEIGHT DATA (if accessible)
# ============================================================================

def get_mesh_data(avatar):
    """
    Extract mesh information from the avatar.
    """
    mesh_data = {}
    
    try:
        mesh_names = avatar.GetMeshNames()
        if mesh_names:
            for mesh_name in mesh_names:
                mesh_data[mesh_name] = {
                    'name': mesh_name,
                    'has_physics': False,  # Will try to determine
                    'weight_map': None
                }
    except Exception as e:
        mesh_data['error'] = str(e)
    
    return mesh_data


def try_get_physics_data(avatar):
    """
    Attempt to access physics data through various methods.
    Note: This may not work as physics APIs aren't fully documented.
    """
    physics_data = {}
    
    # Try various potential method names
    potential_methods = [
        'GetPhysicsComponent',
        'GetClothComponent', 
        'GetSoftClothComponent',
        'GetSpringComponent',
        'GetDynamicComponent',
        'GetPhysXComponent'
    ]
    
    for method_name in potential_methods:
        if hasattr(avatar, method_name):
            try:
                component = getattr(avatar, method_name)()
                if component:
                    physics_data[method_name] = {
                        'exists': True,
                        'methods': [m for m in dir(component) if not m.startswith('_')]
                    }
            except Exception as e:
                physics_data[method_name] = {
                    'exists': False,
                    'error': str(e)
                }
    
    return physics_data


# ============================================================================
# PART 4: JSON EXPORT
# ============================================================================

def export_spring_bone_data(avatar, output_path=None):
    """
    Main export function - extracts all relevant data and saves to JSON.
    """
    print("\n" + "="*80)
    print("EXPORTING SPRING BONE DATA")
    print("="*80)
    
    # Initialize output structure
    export_data = {
        'metadata': {
            'exported_at': datetime.now().isoformat(),
            'avatar_name': avatar.GetName(),
            'format_version': '1.0',
            'description': 'CC5 Spring Bone Data for Blender Import'
        },
        'skeleton': {
            'all_bones': [],
            'spring_bones': [],
            'potential_spring_bones': [],
            'spring_chains': {}
        },
        'physics_info': {},
        'mesh_data': {},
        'bone_parenting': {}
    }
    
    # Get skeleton component
    skeleton_component = avatar.GetSkeletonComponent()
    
    # Get all skin bones (includes spring bones)
    print("\nExtracting skeleton data...")
    skin_bones = skeleton_component.GetSkinBones()
    
    if skin_bones:
        print(f"  Found {len(skin_bones)} skin bones")
        
        # Build bone hierarchy data
        for bone in skin_bones:
            bone_info = {
                'name': bone.GetName(),
                'parent': bone.GetParent().GetName() if bone.GetParent() else None,
                'children': [c.GetName() for c in (bone.GetChildren() or [])],
                'transform': get_transform_data(bone)
            }
            export_data['skeleton']['all_bones'].append(bone_info)
            
            # Build parenting map
            if bone_info['parent']:
                export_data['bone_parenting'][bone_info['name']] = bone_info['parent']
    
    # Identify spring bones
    print("\nIdentifying spring bones...")
    spring_bones, potential = identify_spring_bones(export_data['skeleton']['all_bones'])
    export_data['skeleton']['spring_bones'] = spring_bones
    export_data['skeleton']['potential_spring_bones'] = potential
    
    print(f"  Identified {len(spring_bones)} spring bones")
    print(f"  Found {len(potential)} potential spring bones")
    
    # Build spring chains
    print("\nBuilding spring bone chains...")
    all_spring = spring_bones + potential
    export_data['skeleton']['spring_chains'] = build_spring_chains(all_spring)
    print(f"  Found {len(export_data['skeleton']['spring_chains'])} spring chains")
    
    # Try to get physics data
    print("\nAttempting to access physics data...")
    export_data['physics_info'] = try_get_physics_data(avatar)
    
    # Get mesh data
    print("\nExtracting mesh data...")
    export_data['mesh_data'] = get_mesh_data(avatar)
    
    # Determine output path
    if output_path is None:
        # Try to get project path
        try:
            # Default to user's documents
            output_path = os.path.join(
                os.path.expanduser('~'),
                'Documents',
                f'{avatar.GetName()}_spring_bones.json'
            )
        except:
            output_path = 'spring_bones_export.json'
    
    # Save to JSON
    print(f"\nSaving to: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print("Export successful!")
    except Exception as e:
        print(f"Export failed: {e}")
        # Return data anyway
        return export_data
    
    return export_data


# ============================================================================
# PART 5: PRETTY PRINT RESULTS
# ============================================================================

def print_spring_bone_summary(export_data):
    """
    Print a human-readable summary of the spring bone data.
    """
    print("\n" + "="*80)
    print("SPRING BONE SUMMARY")
    print("="*80)
    
    print(f"\nAvatar: {export_data['metadata']['avatar_name']}")
    print(f"Total bones: {len(export_data['skeleton']['all_bones'])}")
    print(f"Spring bones: {len(export_data['skeleton']['spring_bones'])}")
    print(f"Potential spring bones: {len(export_data['skeleton']['potential_spring_bones'])}")
    
    print("\n--- Spring Bone Chains ---")
    for chain_name, chain in export_data['skeleton']['spring_chains'].items():
        print(f"\nChain: {chain_name}")
        print(f"  Length: {len(chain)} bones")
        print(f"  Root parent: {chain[0]['parent'] if chain else 'Unknown'}")
        print(f"  Bones: {' -> '.join([b['name'] for b in chain])}")
    
    print("\n--- Critical Parenting Info for Blender ---")
    spring_bone_names = [b['name'] for b in export_data['skeleton']['spring_bones']]
    for bone in export_data['skeleton']['spring_bones'][:10]:  # First 10
        print(f"  {bone['name']} -> parent: {bone['parent']}")
    
    if len(spring_bone_names) > 10:
        print(f"  ... and {len(spring_bone_names) - 10} more")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main entry point for the script.
    """
    print("\n" + "#"*80)
    print("# CC5 SPRING BONE EXPLORER AND EXPORTER")
    print("#"*80)
    
    # Step 1: Explore the API (comment out after initial run)
    print("\n[Step 1] Exploring RLPy API...")
    explore_rlpy_api()
    
    # Step 2: Get avatars in scene
    print("\n[Step 2] Getting avatars from scene...")
    avatar_list = RLPy.RScene.GetAvatars()
    
    if not avatar_list:
        print("ERROR: No avatars found in scene!")
        print("Please load a character with spring bone hair first.")
        return
    
    # Use first avatar (or modify to select specific one)
    avatar = avatar_list[0]
    avatar_name = avatar.GetName()
    print(f"  Found avatar: {avatar_name}")
    
    # Step 3: Explore avatar methods
    print("\n[Step 3] Exploring avatar methods...")
    explore_avatar_methods(avatar)
    
    # Step 4: Explore skeleton component
    print("\n[Step 4] Exploring skeleton component...")
    skeleton_component = avatar.GetSkeletonComponent()
    explore_skeleton_component(skeleton_component)
    
    # Step 5: Explore bone node methods (using root bone)
    print("\n[Step 5] Exploring bone node methods...")
    root_bone = skeleton_component.GetRootBone()
    if root_bone:
        explore_bone_node(root_bone)
    
    # Step 6: Export spring bone data
    print("\n[Step 6] Exporting spring bone data...")
    export_data = export_spring_bone_data(avatar)
    
    # Step 7: Print summary
    print_spring_bone_summary(export_data)
    
    print("\n" + "#"*80)
    print("# EXPORT COMPLETE")
    print("#"*80)
    print("\nNext steps:")
    print("1. Check the JSON file in your Documents folder")
    print("2. Use the companion Blender script to import this data")
    print("3. The script will re-parent spring bones correctly on import")
    
    return export_data


# Run if executed directly in CC5
if __name__ == "__main__":
    main()
