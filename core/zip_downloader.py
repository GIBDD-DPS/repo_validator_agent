import os
import tempfile
import requests


class ZipDownloader:
    def download_to_tempfile(self, zip_url: str) -> str:
        resp = requests.get(zip_url, stream=True)

        if resp.status_code != 200:
            raise RuntimeError(
                f"Не удалось скачать ZIP-архив. "
                f"Статус: {resp.status_code}, ответ: {resp.text[:300]}"
            )

        fd, tmp_path = tempfile.mkstemp(suffix=".zip", prefix="repo_")
        os.close(fd)

        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return tmp_path
