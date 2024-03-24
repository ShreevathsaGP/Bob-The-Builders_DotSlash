
import os
import bpy
import math
from math import ceil, floor

# constants
WALL_BASE_DEPTH = 2
WALL_TYPE_SIDE = 0
WALL_TYPE_FRONT = 1
BASE_HOUSE_DIMS = (30, 40)
THRESHOLD = 128

WALL_THICKNESS = 1
WALL_HEIGHT = 15
CEIL_TO_FLOOR = 5

full_plan_path = "C:/Users/Shashank/OneDrive/Desktop/downloads/floor_plans/Floor_plan_1.png"
print(full_plan_path)

def load_image(path):
    bpy.data.images.load(path)
    
def print_matrix(mat):
    for r in mat:
        print(r)
    
def is_pixel_black(r, g, b):
    float_threshold = 128 / 256
    return (r < float_threshold) and (g < float_threshold) and (b < float_threshold)

def is_pixel_red(r, g, b):
    float_threshold = 128 / 256
    return (r > float_threshold) and (g < float_threshold) and (b < float_threshold)
    
def get_bool_array(path):
    image_name = path.split('/')[-1]
    load_image(path)
    
    image = bpy.data.images[image_name]
    
    width, height = image.size
    
    flat_pixels = list(image.pixels)
    
    bool_array = []
    
    for i in range(height):
        row = []
        for j in range(width):
            index = (width * i * 4) + (j * 4)
            r, g, b, _ = flat_pixels[index: index + 4]
            
            if is_pixel_black(r, g, b):
                num = 1
            elif is_pixel_red(r, g, b):
                num = 2
            else:
                num = 0
            
            row.append(num)
            
        bool_array.append(row)
        
    # correct vertical flip
    bool_array.reverse()
        
    return bool_array, width, height

# given a boolean array (1 = wall | 0 = no wall)
# find and output list of walls
# reutrn format array of: (wall_type, (start_x, start_y), length) [wall_type: 0 = front face(row)| 1 = side face(col)]
def get_walls(ba, width, height):
    visited = [[0 for _ in range(width)] for _ in range(height)]
    walls = []

    # row wise wall search
    for r_index, row in enumerate(ba):
        starting_wall = None
        for c_index, pixel in enumerate(row):
            if pixel == 1:
                if starting_wall is None:
                    starting_wall = c_index
                else:
                    visited[r_index][c_index] = 1
            else:
                if starting_wall is not None:
                    wall_length = c_index - starting_wall
                    if wall_length > 1:
                        visited[r_index][starting_wall] = 1
                        walls.append([WALL_TYPE_FRONT, (starting_wall, r_index), wall_length])
                    starting_wall = None

        # rightmost pixel is end of wall?
        if starting_wall is not None:
            wall_length = width - starting_wall
            if wall_length > 1:
                visited[r_index][starting_wall] = 1
                walls.append([WALL_TYPE_FRONT, (starting_wall, r_index), wall_length])

    # column wise wall search
    for c_index in range(width):
        starting_wall = None
        for r_index in range(height):

            # pixel cannot be part of existing row wall
            if visited[r_index][c_index] == 0:
                if ba[r_index][c_index] == 1:
                    if starting_wall is None:
                        starting_wall = r_index
                    else:
                        visited[r_index][c_index] = 1
                else:
                    if starting_wall is not None:
                        wall_length = r_index - starting_wall
                        if wall_length > 1:
                            visited[starting_wall][c_index] = 1
                            walls.append([WALL_TYPE_SIDE, (c_index, starting_wall), wall_length])
                        starting_wall = None

        # bottommost pixel is end of wall?
        if starting_wall is not None:
            wall_length = height - starting_wall
            if wall_length > 1:
                visited[starting_wall][c_index] = 1
                walls.append([WALL_TYPE_SIDE, (c_index, starting_wall), wall_length])

    # print walls
    for wall in walls:
        if wall[0] == WALL_TYPE_FRONT:
            print(f"Row wall starting at {wall[1]} of length {wall[2]}")
        elif wall[0] == WALL_TYPE_SIDE:
            print(f"Column wall starting at {wall[1]} of length {wall[2]}")

    return walls
            
def new_wall(name, wall_type, x, y, height, width, depth):
    if wall_type not in [0, 1]:
        raise Exception("Invalid wall type!")
    
    vertices = [
        (-width / 2, -depth / 2, 0),        # Bottom front left
        (-width / 2, depth / 2, 0),         # Bottom back left
        (width / 2, depth / 2, 0),          # Bottom back right
        (width / 2, -depth / 2, 0),         # Bottom front right
        (-width / 2, -depth / 2, height),   # Top front left
        (-width / 2, depth / 2, height),    # Top back left
        (width / 2, depth / 2, height),     # Top back right
        (width / 2, -depth / 2, height),    # Top front right
    ]

    for index in range(len(vertices)):        
        new_x = vertices[index][0] + (x if wall_type == WALL_TYPE_FRONT else y)
        new_y = vertices[index][1] + (y if wall_type == WALL_TYPE_FRONT else x)
        
        if wall_type == WALL_TYPE_FRONT:
            modified = (new_x, new_y, vertices[index][2])
        else:
            modified = (new_y, new_x, vertices[index][2])
            
        vertices[index] = modified
    
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]
    faces = [
        (0, 1, 2, 3),   # Bottom face
        (4, 5, 6, 7),   # Top face
        (0, 1, 5, 4),   # Front face
        (1, 2, 6, 5),   # Right face
        (2, 3, 7, 6),   # Back face
        (3, 0, 4, 7),   # Left face
    ]
    
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    collection_name = "Objects"
    col = bpy.data.collections.get(collection_name)
    if col is None:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
        
    col = bpy.data.collections.get("Objects")
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.from_pydata(vertices, edges, faces)

def get_staircases(ba, width, height):
    staircases = []
    visited = [[0 for j in range(width)] for i in range(height)]
    
    # [x_start, y_start, width, height] LIST OF
    
    # row wise search of staircases
    for r_index, row in enumerate(ba):
        stair_left = None
        for c_index, pixel in enumerate(row):
            if pixel == 2:
                if (stair_left == None) and not visited[r_index][c_index]:
                    stair_left = c_index
            else:
                if stair_left is not None:
                    stair_width = c_index - stair_left
                    stair_height = 0
                    
                    # search downwards for complete staircase
                    for r in range(r_index, height):
                        x = ba[r][stair_left: stair_left + stair_width]
                        m = list(map(lambda x: x == 2, x))
                        
                        if all(m):
                            stair_height += 1
                            for j in range(stair_left, stair_left + stair_width):
                                visited[r][j] = 1
                        else:
                            break
                        
                    # find the direction of stairs
                    top = r_index - 1
                    bottom = r_index + stair_height
                    
                    top_row = ba[top][stair_left: stair_left + stair_width]
                    bottom_row = ba[bottom][stair_left: stair_left + stair_width]
                    
                    check_wall = lambda y: all(list(map(lambda x: x == 1, y)))
                    
                    
                    if check_wall(top_row) and check_wall(bottom_row):
                        raise Exception("Stairs have no entry!")
                    elif not check_wall(top_row) and not check_wall(bottom_row):
                        raise Exception("Stairs direction cannot be determined!")
                    else:
                        direction = 0 if check_wall(top_row) else 1
                    
                    staircases.append([stair_left, r_index, stair_width, stair_height, direction] )    
                    stair_left = None
                
    print_matrix(visited)
    return staircases

# direction: 0 = right/forward | 1 = left/backward
def new_staircase(name, direction, x, y, width, depth, plan_width, plan_height):
    if direction not in [0, 1]:
        raise Exception("Invalid staircase direction!")
        
    height = 15
    
    vertices = [
        (0, 0, 0),               # Bottom front left
        (width, 0, 0),           # Bottom front right
        (0, 0, height),          # Top front left
        (width, 0, height),      # Top front right
        (0, -depth, 0),          # Bottom back left
        (width, -depth, 0),      # Bottom back right
    ]
    
    if (direction == 1):
        vertices = [
            (0, -depth, 0),
            (width, -depth, 0),
            (0, -depth, height),
            (width, -depth, height),
            (0, 0, 0),
            (width, 0, 0)
        ]
    
    if (width > height):
        vertices = [
            (width, 0, 0),
            (width, -depth, 0),
            (width, 0, height),
            (width, -depth, height),
            (0, 0, 0),
            (0, -depth, 0)
        ]
        
        if (direction == 1):
            vertices = [
                (0, 0, 0),
                (0, -depth, 0),
                (0, 0, height),
                (0, -depth, height),
                (width, 0, 0),
                (width, -depth, 0)
            ]

    for index in range(len(vertices)):        
        new_x = -(vertices[index][0] + x - (plan_width / 2))
        new_y = -(vertices[index][1] - y + (plan_height / 2))
        modified = (new_x, new_y, vertices[index][2])
        vertices[index] = modified
    
    edges = [
        (0, 1), (0, 2), (1, 3), (2, 3),
        (0, 4), (1, 5), (4, 5),
        (2, 4), (3, 5)
    ]
    
    faces = [
        (0, 1, 3, 2),
        (0, 4, 5, 1),
        (0, 2, 4),
        (1, 3, 5),
        (2, 4, 5, 3)
    ]
    
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    collection_name = "Objects"
    col = bpy.data.collections.get(collection_name)
    if col is None:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
        
    col = bpy.data.collections.get("Objects")
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.from_pydata(vertices, edges, faces)

# clear existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# -----MAIN-----
bool_array, width, height = get_bool_array(full_plan_path)

print_matrix(bool_array)

# create the ground plane
bpy.ops.mesh.primitive_plane_add(size=max(width, height) + (5 * WALL_THICKNESS), enter_editmode=False, location=(0, 0, 0))

# add colour to ground plane
plane = bpy.context.object
material = bpy.data.materials.new(name="Dark Brown")
material.diffuse_color = (0.0, 0.0, 0.4, 1) # dark brown colour
# assign material to plane
if plane.data.materials:
    plane.data.materials[0] = material
else:
    plane.data.materials.append(material)

#new_wall("base wall", WALL_TYPE_FRONT, 0, 0, 10, 200, 3)
#new_staircase("Staircase", 1, 0, 0, 5, 20)

walls = get_walls(bool_array, width, height)
staircases = get_staircases(bool_array, width, height)

print(staircases)

for i, s in enumerate(staircases):
    new_staircase(f'stair_{i}', s[4], s[0], s[1], s[2], s[3], width, height)

for i, w in enumerate(walls):  
    length = w[2] / 2
      
    if w[0] == WALL_TYPE_FRONT:
        
        if int(length) != length:
            pass    
        
        new_wall(f'wall_{i}', w[0], -(w[1][0] + (w[2]/2) - (width/2)), w[1][1] - (height/2) + WALL_THICKNESS, 15, w[2], WALL_THICKNESS)
    else:
        new_wall(f'wall_{i}', w[0], -(w[1][0] - (width/2)) - 0.5, w[1][1] + (w[2]/2) - (height/2), 15, w[2], WALL_THICKNESS)
        pass
    
#    if w[0] == WALL_TYPE_FRONT:    
#        new_wall(f'wall_{i}', w[0], w[1][0] + ceil(w[2]/2), w[1][1], 15, w[2], WALL_THICKNESS)
#    else:
#        new_wall(f'wall_{i}', w[0], w[1][0], w[1][1] + floor(w[2]/2), 15, w[2], WALL_THICKNESS)
#print(walls)