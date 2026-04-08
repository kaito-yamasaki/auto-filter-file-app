import os
import shutil
import time

class FileRepository:
    def __init__(self, root_path):
        self.root_path = root_path

    def move(self, src, relative_path):
        target = os.path.join(self.root_path, relative_path)
        os.makedirs(target, exist_ok=True)

        dst = os.path.join(target, os.path.basename(src))

        for _ in range(5):
            try:
                shutil.move(src, dst)
                return
            except PermissionError:
                time.sleep(0.5)