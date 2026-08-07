from pathlib import Path

import pytest

from app.services.omr_storage import OMRScanStorage, build_omr_storage_backend


def test_omr_scan_storage_saves_files_in_configured_directory(tmp_path):
    storage = OMRScanStorage(str(tmp_path / "scans"))

    stored_path = storage.save(b"fake-image-bytes", "scan.png")

    assert stored_path.endswith(".png")
    assert (tmp_path / "scans").exists()
    assert (tmp_path / "scans").is_dir()
    assert (tmp_path / "scans" / Path(stored_path).name).exists()


def test_omr_scan_storage_rejects_invalid_extensions(tmp_path):
    storage = OMRScanStorage(str(tmp_path / "scans"))

    with pytest.raises(ValueError, match="Only JPG, JPEG, and PNG images are allowed."):
        storage.save(b"fake-image-bytes", "scan.pdf")


def test_omr_storage_factory_uses_local_backend_by_default(tmp_path):
    storage = build_omr_storage_backend(backend="local", local_dir=str(tmp_path / "scans"))

    assert isinstance(storage, OMRScanStorage)
    stored_path = storage.save(b"fake-image-bytes", "scan.jpg")
    assert Path(stored_path).exists()
