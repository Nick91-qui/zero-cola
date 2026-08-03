from pathlib import Path
from uuid import uuid4


class OMRScanStorage:
    """Handles persistence for uploaded OMR scan files."""

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def __init__(self, base_dir: str = "uploads/scans"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file_bytes: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Only JPG, JPEG, and PNG images are allowed.")

        unique_filename = f"{uuid4()}{ext}"
        filepath = self.base_dir / unique_filename
        filepath.write_bytes(file_bytes)
        return str(filepath)
