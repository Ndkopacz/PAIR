import unreal
import random
import os
import time

# the max distance the camera can move between each picture
MAX_DISTANCE = 500
# the max rotation that can happen between each picture
MAX_ROTATION = 45

# TODO 
# Make the script actually capture two images - right now it seems to be executing both image captures in the same tick after the camera has
#   already moved, so I've been trying to find a way to delay the main routine's execution while the script is running
# make sure that the camera does actually have 180 degrees of movement on the negative y axis - the positive y side of the scene has nothing in it
# make sure both images are the correct level of zoom
# put the image capture section in a loop
# remove all the damn comments

# Setup paths for saving images and labels
base_directory = r"C:\Users\firek\Desktop\School\Senior Year 2\Semester 1\ECE528\Project\PAIR\Training Data\UE5 Data"
image_directory = os.path.join(base_directory, "Images")
label_directory = os.path.join(base_directory, "Labels")
print("image directory: ", image_directory)


# Ensure directories exist
os.makedirs(image_directory, exist_ok=True)
os.makedirs(label_directory, exist_ok=True)

def capture_image(camera_actor, image_path, delay=0.0):
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, image_path, camera=camera_actor, delay=delay)


def capture_second_image(camera_actor, second_image_path, pair_id):
# Move the camera randomly and apply random rotation
    initial_location = camera_actor.get_actor_location()
    initial_rotation = camera_actor.get_actor_rotation()

    new_location, new_rotation = move_camera(camera_actor)

    # Capture the second image
    capture_image(camera_actor, second_image_path)

    # Calculate position and rotation differences
    label_data = calculate_differences(initial_location, new_location, initial_rotation, new_rotation)

    # Save the label
    label_path = os.path.join(label_directory, f"pair_{pair_id:05d}.txt")
    save_label(label_path, label_data)

    # Print the results
    # print(f"Images saved to: {first_image_path}, {second_image_path}")
    # print(f"Label saved to: {label_path}")



def get_scene_bounds():
    # Get all the actors in the level
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

    # Initialize min and max points
    min_point = unreal.Vector(float('inf'), float('inf'), float('inf'))
    max_point = unreal.Vector(float('-inf'), float('-inf'), float('-inf'))

    # Loop through all actors and find the minimum and maximum bounds
    for actor in all_actors:
        if isinstance(actor, unreal.StaticMeshActor):
            # Get the bounds of the actor (both location and extent)
            actor_location, actor_extent = actor.get_actor_bounds(only_colliding_components=False)
            
            # Update the min and max bounds
            min_point.x = min(min_point.x, actor_location.x - actor_extent.x)
            min_point.y = min(min_point.y, actor_location.y - actor_extent.y)
            min_point.z = min(min_point.z, actor_location.z - actor_extent.z)

            max_point.x = max(max_point.x, actor_location.x + actor_extent.x)
            max_point.y = max(max_point.y, actor_location.y + actor_extent.y)
            max_point.z = max(max_point.z, actor_location.z + actor_extent.z)

    return min_point, max_point

def move_camera(camera_actor, max_distance=MAX_DISTANCE, max_rotation=MAX_ROTATION, offset=30):
    # Get the current position and rotation
    current_location = camera_actor.get_actor_location()
    current_rotation = camera_actor.get_actor_rotation()

    # Generate a random offset in X, Y, Z directions for movement
    random_offset = unreal.Vector(
        random.uniform(-max_distance, max_distance),
        random.uniform(-max_distance, max_distance),
        random.uniform(-max_distance, max_distance)
    )

    # Constrain the camera's movement to stay within the bounds of the scene, with an offset
    new_location = current_location + random_offset
    new_location.x = max(min(new_location.x, scene_max.x - offset), scene_min.x + offset)
    new_location.y = max(min(new_location.y, scene_max.y - offset), scene_min.y + offset)
    new_location.z = max(min(new_location.z, scene_max.z - offset), scene_min.z + offset)

    random_pitch = random.uniform(-10, 10)  # Small random pitch tilt
    random_roll = random.uniform(-10, 10)   # Small random roll tilt
    random_yaw = random.uniform(-180, -1)  # Yaw between -180 and -1 degrees (negative Y direction)

    new_rotation = unreal.Rotator(random_pitch, random_yaw, random_roll)

    # Apply the new location and rotation to the camera
    camera_actor.set_actor_location(new_location, sweep=True, teleport=True)
    camera_actor.set_actor_rotation(new_rotation, teleport_physics=True)

    return new_location, new_rotation

# Function to calculate the difference in position and rotation between two vectors
def calculate_differences(old_location, new_location, old_rotation, new_rotation):
    # Position differences (delta_x, delta_y, delta_z)
    delta_position = new_location - old_location
    delta_x = delta_position.x
    delta_y = delta_position.y
    delta_z = delta_position.z

    # Rotation differences (delta_pitch, delta_roll, delta_yaw)
    delta_pitch = new_rotation.pitch - old_rotation.pitch
    delta_roll = new_rotation.roll - old_rotation.roll
    delta_yaw = new_rotation.yaw - old_rotation.yaw

    return (delta_x, delta_y, delta_z, delta_pitch, delta_roll, delta_yaw)

# Function to save the label to a text file
def save_label(label_path, label_data):
    with open(label_path, 'w') as file:
        file.write(",".join(map(str, label_data)))

# Main function to control the camera, capture images, and save labels
def main():
    # Get all SceneCapture2D actors in the level
    scene_capture_actors = unreal.GameplayStatics().get_all_actors_of_class(unreal.EditorLevelLibrary.get_editor_world(), unreal.SceneCapture2D)

    # Get all CameraActor actors in the level
    camera_actors = unreal.GameplayStatics().get_all_actors_of_class(unreal.EditorLevelLibrary.get_editor_world(), unreal.CameraActor)

    # Check if we have any SceneCapture2D actors and CameraActors in the level
    if len(scene_capture_actors) == 0 or len(camera_actors) == 0:
        unreal.SystemLibrary.print_string(None, "Error: Could not find any SceneCapture2D or CameraActor in the level.")
    else:
        # Select the first found SceneCapture2D actor and CameraActor actor
        scene_capture_actor = scene_capture_actors[0]
        camera_actor = camera_actors[0]
        
        # Print success message
        unreal.SystemLibrary.print_string(None, f"Found {len(scene_capture_actors)} SceneCapture2D and {len(camera_actors)} CameraActor actors!")
        
        # Use these references in your script...
        # For example:
        unreal.SystemLibrary.print_string(None, f"SceneCapture2D Actor: {scene_capture_actor.get_name()}")
        unreal.SystemLibrary.print_string(None, f"CameraActor: {camera_actor.get_name()}")

    # Get the bounds of the scene
    global scene_min, scene_max
    scene_min, scene_max = get_scene_bounds()

    # Generate a unique ID for this image pair
    pair_id = 1  # This could be incremented in a loop if you want to capture multiple pairs

    # Create a folder for this pair
    pair_folder = os.path.join(image_directory, f"pair_{pair_id:05d}")
    os.makedirs(pair_folder, exist_ok=True)

    # Paths for the images
    first_image_path = os.path.join(pair_folder, "image1.png")
    second_image_path = os.path.join(pair_folder, "image2.png")

    # Capture the first image
    capture_image(camera_actor, first_image_path)

    time.sleep(0.1)

    capture_second_image(camera_actor, second_image_path, pair_id)

# Run the main function to perform the camera movement and capture process
main()
