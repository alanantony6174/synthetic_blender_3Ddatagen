#!/usr/bin/env python3
"""
Wrap an image onto a box or cylinder and export as Collada (.dae)
Usage (from terminal):
blender --background --python wrap_image_box.py -- -p box -i image.png -o output_dir
"""

import bpy
import sys
import os
import argparse
import bmesh

# ---- Argument parsing ----
def parse_args():
    argv = sys.argv
    if "--" in argv:
        idx = argv.index("--")
        cli_args = argv[idx+1:]
    else:
        cli_args = argv[1:]

    parser = argparse.ArgumentParser(description="Wrap image onto a primitive")
    parser.add_argument("-p", "--primitive", choices=["box", "cylinder"], default="box")
    parser.add_argument("-i", "--image", required=True, help="Path to image file")
    parser.add_argument("-o", "--outdir", required=True, help="Output directory")
    parser.add_argument("--width", type=float, default=1.0, help="Width in meters")
    parser.add_argument("--depth", type=float, default=1.0, help="Depth in meters")
    parser.add_argument("--height", type=float, default=1.0, help="Height in meters")
    return parser.parse_args(cli_args)

# ---- Blender helper functions ----
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_box(width, depth, height):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.active_object
    obj.scale = (width/2, depth/2, height/2)
    bpy.ops.object.transform_apply(scale=True)
    return obj

def create_cylinder(radius, height):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=height)
    return bpy.context.active_object

def apply_texture_to_single_face(obj, image_path):
    """Apply texture to only one face (front face) of the object"""
    
    # Create two materials: one textured, one plain
    textured_mat = bpy.data.materials.new(name="TexturedMaterial")
    textured_mat.use_nodes = True
    
    # Clear default nodes for textured material
    nodes = textured_mat.node_tree.nodes
    nodes.clear()
    
    # Create nodes for textured material
    tex_image = nodes.new("ShaderNodeTexImage")
    tex_image.image = bpy.data.images.load(image_path)
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    output = nodes.new("ShaderNodeOutputMaterial")
    
    # Link nodes for textured material
    links = textured_mat.node_tree.links
    links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Create plain material
    plain_mat = bpy.data.materials.new(name="PlainMaterial")
    plain_mat.use_nodes = True
    plain_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.8, 0.8, 1.0)  # Light gray
    
    # Clear existing materials and add both
    obj.data.materials.clear()
    obj.data.materials.append(plain_mat)    # Index 0 - plain material
    obj.data.materials.append(textured_mat) # Index 1 - textured material
    
    # Enter edit mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Select all faces and assign plain material first
    bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    
    for face in bm.faces:
        face.material_index = 0  # Assign plain material to all faces
    
    # Now select and assign textured material to front face only
    # In Blender, the front face typically has normal pointing in -Y direction for a default cube
    bpy.ops.mesh.select_all(action='DESELECT')
    
    for face in bm.faces:
        # Check if this is the front face (normal pointing in -Y direction)
        if face.normal.y < -0.9:
            face.select = True
            face.material_index = 1  # Assign textured material
            
            # Set up UV mapping for just this face
            if not obj.data.uv_layers:
                obj.data.uv_layers.new(name="UVMap")
            
            uv_layer = bm.loops.layers.uv.active
            
            # Simple planar projection for the selected face
            for loop in face.loops:
                vert = loop.vert.co
                # Map to UV coordinates (0-1 range)
                # For front face, use X and Z coordinates
                u = (vert.x / obj.dimensions.x) + 0.5
                v = (vert.z / obj.dimensions.z) + 0.5
                loop[uv_layer].uv = (u, v)
            break
    
    # Update mesh and return to object mode
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def export_collada(obj, outdir):
    os.makedirs(outdir, exist_ok=True)
    filename = os.path.join(outdir, f"{obj.name}.dae")
    bpy.ops.wm.collada_export(filepath=filename)
    print(f"✅ Exported {filename}")

# ---- Main ----
def main():
    args = parse_args()

    clear_scene()

    if args.primitive == "box":
        obj = create_box(args.width, args.depth, args.height)
    else:
        # For cylinder, use width as diameter and depth as height
        radius = args.width / 2
        obj = create_cylinder(radius, args.depth)

    apply_texture_to_single_face(obj, args.image)
    export_collada(obj, args.outdir)

if __name__ == "__main__":
    main()