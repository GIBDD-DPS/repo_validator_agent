import os
import tempfile
import zipfile


class ZipBuilder:
    """
    Собирает ZIP-архив из директории (исправленного репозитория).
    """

    def build_zip_from_dir(self, root_dir: str) -> str:
        tmp_fd, zip_path = tempfile.mkstemp(suffix=".zip", prefix="fixed_repo_")
        os.close(tmp_fd)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(full_path, root_dir)
                    zf.write(full_path, arcname=rel_path)

        return zip_path
