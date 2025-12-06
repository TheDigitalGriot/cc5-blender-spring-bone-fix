# CC5 Spring Bone Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Blender 3.0+](https://img.shields.io/badge/blender-3.0+-orange.svg)](https://www.blender.org/)

A toolkit for extracting spring bone data from Reallusion Character Creator 5 and fixing bone parenting issues when importing into Blender.

## The Problem

When exporting characters with spring bone hair from Character Creator 5 to Blender via FBX, the spring bones often lose their proper parenting relationships. This causes hair to "fall off" or deform incorrectly during animation because:

- Spring bones become disconnected from the head/neck skeleton
- Bone hierarchy information isn't fully preserved in FBX
- The CC5 PhysX physics system doesn't have a direct API for extracting spring parameters

This toolkit solves the problem by:
1. Extracting bone hierarchy data directly from CC5 via the RLPy Python API
2. Exporting that data as JSON metadata alongside your FBX
3. Using that metadata in Blender to reconstruct proper bone parenting

## Features

- 🔍 **API Explorer** - Discover available RLPy methods including undocumented physics-related functions
- 🦴 **Bone Hierarchy Extraction** - Full skeleton traversal with parent/child relationships
- 🎯 **Spring Bone Detection** - Automatic identification using naming conventions
- ⛓️ **Chain Building** - Groups connected spring bones into logical chains
- 📄 **JSON Export** - Portable data format for cross-application use
- 🔧 **Blender Fixer** - Automatic bone re-parenting after FBX import
- 🎨 **Blender UI Panel** - Integrated operator with file browser

## Requirements

### Character Creator 5
- Reallusion Character Creator 5
- Python scripting enabled (Plugins → Python)

### Blender
- Blender 3.0 or higher
- [CC/iC Blender Tools](https://github.com/soupday/cc_blender_tools) (recommended)

## Installation

### Option 1: Clone the repository
```bash
git clone https://github.com/yourusername/cc5-spring-bone-tools.git
```

### Option 2: Download ZIP
Download and extract the [latest release](https://github.com/yourusername/cc5-spring-bone-tools/releases).

## Usage

### Step 1: Export Spring Bone Data from CC5

1. Open Character Creator 5 with your character loaded (including hair with spring bones)
2. Ensure physics is activated on the hair (check Modify panel for PhysX properties)
3. Go to **Plugins → Python → Load Python**
4. Select `cc5_spring_bone_explorer.py`
5. Check the console output (Plugins → Python → Show Console)
6. Find the exported JSON in your Documents folder: `{AvatarName}_spring_bones.json`

#### Console Output Example
```
================================================================================
SPRING BONE SUMMARY
================================================================================

Avatar: MyCharacter
Total bones: 156
Spring bones: 24
Potential spring bones: 0

--- Spring Bone Chains ---

Chain: CC_Hair_Spine01
  Length: 6 bones
  Root parent: CC_Base_Head
  Bones: CC_Hair_Spine01 -> CC_Hair_Spine02 -> CC_Hair_Spine03 -> ...
```

### Step 2: Export FBX from CC5

For best results, use the [CC4/CC5 Blender Tools Plugin](https://github.com/soupday/CC4-Blender-Tools-Plugin):

1. In CC5, go to **Plugins → Blender Pipeline → Export Character**
2. Choose **"Blender Round Trip Workflow"** or **"Round Trip Export for Unity"**
3. Export to your desired location

### Step 3: Import and Fix in Blender

#### Method A: Using the UI Panel

1. Import your FBX using CC/iC Blender Tools standard import
2. In the 3D Viewport, open the sidebar (N key)
3. Find the **"CC5 Tools"** tab
4. Click **"Import JSON Data"**
5. Select your `{AvatarName}_spring_bones.json` file

#### Method B: Running the Script Directly

1. Open `blender_spring_bone_fixer.py` in Blender's Text Editor
2. Modify the `JSON_PATH` variable at the bottom:
   ```python
   JSON_PATH = r"C:\path\to\YourAvatar_spring_bones.json"
   ```
3. Run the script (Alt+P or Text → Run Script)

### Step 4: Set Up Spring Physics (Optional)

After fixing parenting, use CC/iC Blender Tools for physics:

1. Go to **CC/iC Create** tab → **Spring Rig** panel
2. Select your hair mesh(es)
3. Click **"Bind Hair"** to weight paint spring bone influence
4. Use **Scene Tools → Spring Bone Simulation** to test physics

## File Structure

```
cc5-spring-bone-tools/
├── README.md
├── LICENSE
├── cc5_spring_bone_explorer.py    # Main CC5 extraction script
├── blender_spring_bone_fixer.py   # Blender import/fix script
├── cc5_quick_reference.py         # Console snippets for debugging
└── examples/
    └── example_spring_bones.json  # Sample output format
```

## JSON Output Format

```json
{
  "metadata": {
    "exported_at": "2024-12-05T10:30:00",
    "avatar_name": "MyCharacter",
    "format_version": "1.0"
  },
  "skeleton": {
    "all_bones": [...],
    "spring_bones": [
      {
        "name": "CC_Hair_Spine01",
        "parent": "CC_Base_Head",
        "children": ["CC_Hair_Spine02"],
        "transform": {
          "local": {
            "translation": [0.0, 5.2, 0.0],
            "rotation": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0]
          }
        }
      }
    ],
    "spring_chains": {
      "CC_Hair_Spine01": [...]
    }
  },
  "bone_parenting": {
    "CC_Hair_Spine01": "CC_Base_Head",
    "CC_Hair_Spine02": "CC_Hair_Spine01"
  }
}
```

## Spring Bone Naming Conventions

The scripts detect spring bones using these patterns:

| Pattern | Description |
|---------|-------------|
| `CC_Hair_Spine*` | Official Reallusion hair products |
| `Hair_*`, `hair_*` | Generic hair bones |
| `Spring_*`, `spring_*` | Explicit spring bones |
| `Ponytail_*`, `Braid_*` | Specific hairstyle bones |
| `Dynamic_*`, `Phys_*` | Physics-enabled bones |
| `Ribbon_*`, `Accessory_*` | Accessory spring bones |

Bones parented to `Head` or `Neck` that don't match standard skeleton names are flagged as "potential spring bones."

## Known Limitations

1. **No Direct Physics Parameter Access**: The CC5 RLPy API doesn't expose PhysX spring parameters (stiffness, damping, etc.) through public methods. This tool extracts hierarchy data, not physics settings.

2. **Accessory Hair**: Hair imported as accessories in CC5 may have a separate skeleton. The script attempts to detect this but may require manual adjustment.

3. **Coordinate Systems**: CC5 uses Y-up, Blender uses Z-up. FBX import handles this, but transform data in JSON is in CC5's coordinate space.

4. **Round-Trip Limitations**: Re-exporting spring bones from Blender back to CC5 has [significant limitations](https://soupday.github.io/cc_blender_tools/spring-bones.html#exporting-back-to-character-creator) - hair rigs become separate accessories.

## Troubleshooting

### Spring bones not detected in CC5
- Ensure physics is activated on the hair (select hair → check Modify panel)
- Check if hair is a separate prop: `RLPy.RScene.GetProps()`
- Verify bone naming matches expected patterns

### Bones not found in Blender
- Check for naming convention differences (CC_ prefix)
- Ensure FBX was imported with armature
- Try importing with CC/iC Blender Tools instead of default FBX import

### Hair still falls off after fix
- Verify the JSON contains correct parent references
- Check that parent bones (Head, Neck) exist in Blender armature
- Re-run the fixer script after ensuring armature is selected

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution

- [ ] Discover undocumented physics APIs in RLPy
- [ ] Add support for cloth physics weight maps
- [ ] Create Unity import script
- [ ] Add Unreal Engine support
- [ ] Improve spring bone detection heuristics

## Related Projects

- [CC/iC Blender Tools](https://github.com/soupday/cc_blender_tools) - Essential Blender addon for CC characters
- [CC4 Blender Tools Plugin](https://github.com/soupday/CC4-Blender-Tools-Plugin) - CC4/CC5 export plugin
- [Reallusion Python API Wiki](https://wiki.reallusion.com/IC_Python_API) - Official RLPy documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Reallusion](https://www.reallusion.com/) for Character Creator and the RLPy API
- [Soupday](https://github.com/soupday) for the excellent CC Blender Tools
- The Reallusion community for documenting spring bone workflows

---

**Note**: This project is not affiliated with or endorsed by Reallusion. Character Creator and iClone are trademarks of Reallusion Inc.