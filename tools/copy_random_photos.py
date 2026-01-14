import os
import random
import shutil



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

