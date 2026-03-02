#!/usr/bin/env python3
import os, re, sys, subprocess, shutil, tempfile

# --- SPETS DAE Prep ---
# Use a combination of XML syntax cleanup and blender sanitizing
# to make sure everything is clean and ready for import into SPETS

# --- CONFIGURATION ---
# Blender dropped native Collada functions after the 4.5 branch
# Install it on your system and give the path to the binary here
BLENDER_PATH = "/opt/blender-4.5/blender"

def stage_1_xml_scrub(filepath):
    print(f"[*] Stage 1: Scrubbing XML syntax: {os.path.basename(filepath)}")
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        xml = f.read()

    # Kill unneeded attributes and blocks
    xml = re.sub(r'\s+opaque="(RGB_ONE|A_ONE)"', '', xml)
    for block in ['library_images', 'library_materials', 'library_effects', 
                  'library_controllers', 'library_animations', 'extra']:
        xml = re.sub(f'<{block}>.*?</{block}>', f'<{block}/>', xml, flags=re.DOTALL)

    # Strip material bindings
    xml = re.sub(r'<instance_material.*?>', '', xml)
    xml = re.sub(r'<bind_material>.*?</bind_material>', '', xml, flags=re.DOTALL)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".dae")
    with os.fdopen(tmp_fd, 'w') as f:
        f.write(xml)
    return tmp_path

def stage_2_blender_repair(input_dae, output_dae):
    print("[*] Stage 2: Repairing geometry with Blender 4.5...")
    
    # Corrected collada_export for Blender 4.5 API
    py_cmd = f"""
import bpy, sys
try:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.collada_import(filepath=r'{input_dae}', import_units=False)
    
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if meshes:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        
        # Geometry Cleanup
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Export - Fixed parameters for 4.5 LTS
    # Note: 'include_animations=False' often strips the junk effectively
    bpy.ops.wm.collada_export(
        filepath=r'{output_dae}', 
        apply_modifiers=True,
        include_animations=False,
        selected=False
    )
    print("PYTHON_FINISH_SUCCESS")
except Exception as e:
    import traceback
    print(f"BLENDER_PY_ERROR: {{e}}")
    traceback.print_exc()
    sys.exit(1)
"""
    try:
        proc = subprocess.run([BLENDER_PATH, "--background", "--python-expr", py_cmd], 
                              capture_output=True, text=True)
        if "PYTHON_FINISH_SUCCESS" in proc.stdout:
            for line in proc.stdout.splitlines():
                if "Removed" in line: print(f"    [+] {line.strip()}")
            return True
        print(f"[!] Blender Logic Error:\n{proc.stdout}\n{proc.stderr}")
        return False
    except Exception as e:
        print(f"[!] Subprocess Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: ./dae_prep.py <file.dae>")
        sys.exit(1)

    target_file = os.path.abspath(sys.argv[1])
    tmp_scrubbed = stage_1_xml_scrub(target_file)
    
    tmp_dir = tempfile.mkdtemp()
    tmp_repaired = os.path.join(tmp_dir, "repaired.dae")
    
    if stage_2_blender_repair(tmp_scrubbed, tmp_repaired):
        if os.path.exists(tmp_repaired):
            # Final verification: is it non-zero size?
            if os.path.getsize(tmp_repaired) > 0:
                shutil.move(tmp_repaired, target_file)
                print(f"[SUCCESS] {os.path.basename(target_file)} cleaned and overwritten.")
    else:
        print("[FAILURE] Cleanup failed. Original file is safe.")

    if os.path.exists(tmp_scrubbed): os.remove(tmp_scrubbed)
    shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
