import os
import shutil

class FileRepository:
    def __init__(self, root_path):
        self.root_path = root_path

    def move(self, src, relative_path):
        if not os.path.exists(src):
            return None

        target = os.path.join(self.root_path, relative_path)
        os.makedirs(target, exist_ok=True)

        dst = os.path.join(target, os.path.basename(src))
        dst = self._resolve_duplicate_path(dst)

        try:
            shutil.move(src, dst)
            return dst
        except FileNotFoundError:
            return None

    def _resolve_duplicate_path(self, destination_path):
        if not os.path.exists(destination_path):
            return destination_path

        directory = os.path.dirname(destination_path)
        filename = os.path.basename(destination_path)
        stem, extension = os.path.splitext(filename)

        counter = 2
        while True:
            candidate = os.path.join(directory, f"{stem}({counter}){extension}")
            if not os.path.exists(candidate):
                return candidate
            counter += 1