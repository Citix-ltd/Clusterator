import os
import glob


FILE_FORMAT = "jpg"


def Storage():
    def __init__(self, root_dir: str) -> None:
        self.root_dir = root_dir

    def get_all_raw(self) -> None:
        return glob.glob(self.root_dir + f"/**/*.{FILE_FORMAT}", recursive = True)
