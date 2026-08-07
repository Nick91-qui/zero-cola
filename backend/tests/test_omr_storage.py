from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

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


def test_omr_storage_factory_uses_minio_backend(monkeypatch):
    fake_client = MagicMock()
    fake_client.bucket_exists.return_value = False

    fake_minio_module = ModuleType("minio")

    class FakeMinio:
        def __init__(self, endpoint, access_key, secret_key, secure):
            self.endpoint = endpoint
            self.access_key = access_key
            self.secret_key = secret_key
            self.secure = secure

        def bucket_exists(self, bucket_name):
            return fake_client.bucket_exists(bucket_name)

        def make_bucket(self, bucket_name):
            fake_client.make_bucket(bucket_name)

        def put_object(self, bucket_name, object_name, data, length):
            fake_client.put_object(bucket_name, object_name, data, length)

    fake_minio_module.Minio = FakeMinio
    monkeypatch.setitem(__import__("sys").modules, "minio", fake_minio_module)

    storage = build_omr_storage_backend(
        backend="minio",
        minio_endpoint="localhost:9000",
        minio_access_key="minio-access",
        minio_secret_key="minio-secret",
        minio_bucket="cola-zero-omr",
        minio_secure=False,
        minio_public_base_url="https://files.example.com",
    )

    stored_path = storage.save(b"fake-image-bytes", "scan.png")

    assert stored_path.startswith("https://files.example.com/cola-zero-omr/")
    fake_client.make_bucket.assert_called_once_with("cola-zero-omr")
    fake_client.put_object.assert_called_once()
