import unreal
import os
import random

'''
TO USE:
1. change NUM_PAIRS_IMAGES to whatever number of pairs you want
2. change base_directory to the UE5 Data folder in the PAIR repo wherever that is stored on your computer
3. In unreal, click on "tools" (in the top bar), scroll down to near the bottom, and click "Execute Python Script"
4. The script should run and take screenshots that will be stored in the "Images" and "Labels" folders in UE5 Data 
5. The first time you run the script it skips a lot of pairs for whatever reason, so run it once with not very many pairs
    and then delete that data and run it using the real number of pairs you wanted
'''


# number of pairs of images you want
NUM_PAIRS_IMAGES = 5
base_directory = r"C:\Users\firek\Desktop\School\Senior Year 2\Semester 1\ECE528\Project\PAIR\Training Data\UE5 Data"

# the max distance the camera can move between each picture (x, y, z)
MAX_DISTANCE = unreal.Vector(1000, 1000, 30)
# the max rotation that can happen from 0, 0, 0 (roll, pitch, yaw)
MAX_ROTATION = unreal.Rotator(10, 10, 30)


# Helper functions
def calculate_differences(old_location, new_location, old_rotation, new_rotation):
    delta_position = new_location - old_location
    delta_x = delta_position.x
    delta_y = delta_position.y
    delta_z = delta_position.z

    delta_pitch = new_rotation.pitch - old_rotation.pitch
    delta_roll = new_rotation.roll - old_rotation.roll
    delta_yaw = new_rotation.yaw - old_rotation.yaw

    return (delta_x, delta_y, delta_z, delta_pitch, delta_roll, delta_yaw)


def get_scene_bounds():
        all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

        min_point = unreal.Vector(float('inf'), float('inf'), float('inf'))
        max_point = unreal.Vector(float('-inf'), float('-inf'), float('-inf'))

        for actor in all_actors:
            if isinstance(actor, unreal.StaticMeshActor):
                actor_location, actor_extent = actor.get_actor_bounds(only_colliding_components=False)

                # Ignoring skybox
                if (actor_extent.x > 1000000):
                    continue
                
                min_point.x = min(min_point.x, actor_location.x - actor_extent.x)
                min_point.y = min(min_point.y, actor_location.y - actor_extent.y)
                min_point.z = min(min_point.z, actor_location.z - actor_extent.z)

                max_point.x = max(max_point.x, actor_location.x + actor_extent.x)
                max_point.y = max(max_point.y, actor_location.y + actor_extent.y)
                max_point.z = max(max_point.z, actor_location.z + actor_extent.z)

        return min_point, max_point


def save_label(label_path, label_data):
    with open(label_path, 'w') as file:
        file.write(",".join(map(str, label_data)))



class OnTick(object):
    image_directory = os.path.join(base_directory, "Images")
    label_directory = os.path.join(base_directory, "Labels")


    def __init__(self):
        camera_actors = unreal.GameplayStatics().get_all_actors_of_class(unreal.EditorLevelLibrary.get_editor_world(), unreal.CameraActor)

        if len(camera_actors) == 0:
            print(None, "Error: Could not find any CameraActor in the level.")
        else:
            self.camera_actor = camera_actors[0]
            print(None, f"Found {len(camera_actors)} CameraActor actors!")
            print(None, f"CameraActor: {self.camera_actor.get_name()}")

        os.makedirs(self.image_directory, exist_ok=True)
        os.makedirs(self.label_directory, exist_ok=True)

        self.min_point, self.max_point = get_scene_bounds()
    

    def start(self):
        self.tickcount = 0
        self.slate_post_tick_handle = unreal.register_slate_post_tick_callback(self.__tick__)
    

    def move_camera(self, max_distance=MAX_DISTANCE, max_rotation=MAX_ROTATION, offset=300):
        current_location = self.camera_actor.get_actor_location()

        random_offset = unreal.Vector(
            random.uniform(-max_distance.x, max_distance.x),
            random.uniform(-max_distance.y, max_distance.y),
            random.uniform(-max_distance.z, max_distance.z)
        )

        new_location = current_location + random_offset
        new_location.x = max(min(new_location.x, self.max_point.x - offset), self.min_point.x + offset)
        new_location.y = max(min(new_location.y, self.max_point.y - offset), self.min_point.y + offset)
        new_location.z = max(min(new_location.z, self.max_point.z - offset), self.min_point.z + offset)

        random_pitch = random.uniform(-max_rotation.pitch, max_rotation.pitch)
        random_roll = random.uniform(-max_rotation.roll, max_rotation.roll)
        random_yaw = random.uniform(-max_rotation.yaw, max_rotation.yaw)

        new_rotation = unreal.Rotator(random_pitch, random_yaw, random_roll)

        self.camera_actor.set_actor_location(new_location, sweep=True, teleport=True)
        self.camera_actor.set_actor_rotation(new_rotation, teleport_physics=True)

        return new_location, new_rotation

    
    def take_screenshot_1(self):
        self.pair_id = self.tickcount // 2
        self.pair_folder = os.path.join(self.image_directory, f"pair_{self.pair_id:05d}")
        os.makedirs(self.pair_folder, exist_ok=True)

        first_image_path = os.path.join(self.pair_folder, "image1.png")

        print("Taking screenshot 1 for pair " + str(self.pair_id))

        unreal.AutomationLibrary.take_high_res_screenshot(
            1920,
            1080,
            first_image_path,
            camera=self.camera_actor,
            comparison_tolerance=unreal.ComparisonTolerance.HIGH,
            delay=0.0
        )
    

    def take_screenshot_2(self):
        initial_location = self.camera_actor.get_actor_location()
        initial_rotation = self.camera_actor.get_actor_rotation()

        new_location, new_rotation = self.move_camera()

        second_image_path = os.path.join(self.pair_folder, "image2.png")

        print("\nTaking screenshot 2 for pair " + str(self.pair_id))

        unreal.AutomationLibrary.take_high_res_screenshot(
            1920,
            1080,
            second_image_path,
            camera=self.camera_actor,
            comparison_tolerance=unreal.ComparisonTolerance.HIGH,
            delay=0.0
        )

        label_data = calculate_differences(initial_location, new_location, initial_rotation, new_rotation)

        label_path = os.path.join(self.label_directory, f"pair_{self.pair_id:05d}.txt")
        save_label(label_path, label_data)

    
    def __tick__(self, deltatime):
        # Function called every tick
        try:
            if (self.tickcount < NUM_PAIRS_IMAGES * 2):
                print(". ")
                print("Time since last tick:", deltatime) # Print the deltatime just for sanity check so we know a tick was made
                
                if (self.tickcount % 2 == 0):
                    self.take_screenshot_1()
                else:
                    self.take_screenshot_2()

                self.tickcount = self.tickcount + 1
            else:
                print("Finished! Unregistering tick handler")
                unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)

        except Exception as error:
            print("ERROR:", error)
            try:
                print("unregistering tick after error")
                unreal.unregister_slate_post_tick_callback(self.slate_post_tick_handle)
            except Exception as error:
                print("exception in unregistering tick")
                pass



instance = OnTick()
instance.start()
