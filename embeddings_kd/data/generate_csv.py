import os
import glob


def glob_all_images(paths: list[str], ext: str = "*.jpg"):
    """
    Finds all images in the given paths, including subdirectories
    """
    result = []
    for path in paths:
        result.extend(glob.glob(os.path.join(path, "**", ext), recursive=True))
    return result


def make_split(prefix: str, paths: list[str]) -> None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    images = glob_all_images(paths)
    print(f"Found {len(images)} {prefix} images")
    with open(f'{current_dir}/{prefix}.csv', 'w') as f:
        for image in images:
            f.write(f"{image}\n")


from config import TRAIN_PATHS, TEST_PATHS
make_split("train", TRAIN_PATHS)
make_split("test", TEST_PATHS)
print("Done")
