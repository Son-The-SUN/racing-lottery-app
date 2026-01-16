import os
import random
import shutil
from PIL import Image, ExifTags



def copyRandomPhotos(source_dir, dest_dir, num_photos):
    """
    copy a specified number of random photos from source_dir to dest_dir
    the source dir can contain subfolders, also search within those subfolders to select a number of random photos
    the dest_dir will contain only the selected photos (no subfolders)
    """
    valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')
    all_photos = []

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(valid_extensions):
                all_photos.append(os.path.join(root, file))

    if not all_photos:
        print(f"No photos found in {source_dir}")
        return

    num_to_copy = min(len(all_photos), num_photos)
    selected_photos = random.sample(all_photos, num_to_copy)

    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)

    for photo_path in selected_photos:
        file_name = os.path.basename(photo_path)
        dest_path = os.path.join(dest_dir, file_name)

        # Handle filename collisions
        base, extension = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{extension}")
            counter += 1

        shutil.copy2(photo_path, dest_path)
        fixPhotoOrientation(dest_path)

def fixPhotoOrientation(photo_path):
    """
    Fix the orientation of a photo based on its EXIF data.
    """
    try:
        with Image.open(photo_path) as image:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            
            exif = image._getexif()
            if exif is None:
                return

            orientation_value = exif.get(orientation)
            
            if orientation_value == 3:
                image = image.rotate(180, expand=True)
            elif orientation_value == 6:
                image = image.rotate(270, expand=True)
            elif orientation_value == 8:
                image = image.rotate(90, expand=True)
            else:
                return

            image.save(photo_path)
            
    except (AttributeError, KeyError, IndexError):
        # cases: image don't have getexif
        pass
    except Exception as e:
        print(f"Error fixing orientation for {photo_path}: {e}")



ASSETS_DIR = os.path.join(os.path.dirname(__file__).split("racing-lottery-app")[0], 'racing-lottery-app', 'assets')
RANDOM_PHOTOS_DIR = os.path.join(ASSETS_DIR, 'random_photos')
RANDOM_PHOTOS_SOURCE_DIR = r"C:\Users\tsont\OneDrive - Group GSA\GSA Photos"

# Copy random photos if not already done
copyRandomPhotos(RANDOM_PHOTOS_SOURCE_DIR, RANDOM_PHOTOS_DIR, 300)
