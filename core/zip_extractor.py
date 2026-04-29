import os
import tempfile
import zipfile


class ZipExtractor:
    def extract_to_tempdir(self, zip_path: str) -> str:
        if not zipfile.is_zipfile(zip_path):
            raise RuntimeError("Файл не является ZIP-архивом")

        tmp_dir = tempfile.mkdtemp(prefix="repo_src_")

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        entries = os.listdir(tmp_dir)
        if len(entries) == 1:
            root = os.path.join(tmp_dir, entries[0])
            if os.path.isdir(root):
                return root

        return tmp_dir
