from __future__ import annotations

import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from uuid import uuid4


class OMRStorageBackend(ABC):
    """Abstract storage backend for uploaded OMR files."""

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    @abstractmethod
    def save(self, file_bytes: bytes, filename: str) -> str:
        raise NotImplementedError

    def _validate_extension(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Only JPG, JPEG, and PNG images are allowed.")
        return ext


class OMRScanStorage(OMRStorageBackend):
    """Filesystem-based storage backend used in development and tests."""

    def __init__(self, base_dir: str = "uploads/scans"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file_bytes: bytes, filename: str) -> str:
        ext = self._validate_extension(filename)
        unique_filename = f"{uuid4()}{ext}"
        filepath = self.base_dir / unique_filename
        filepath.write_bytes(file_bytes)
        return str(filepath)


class MinIOOMRScanStorage(OMRStorageBackend):
    """MinIO/S3-compatible storage backend for future production deployments."""

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
        public_base_url: Optional[str] = None,
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.secure = secure
        self.public_base_url = public_base_url
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            from minio import Minio
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "MinIO storage backend requires the optional 'minio' package."
            ) from exc

        self._client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )
        return self._client

    def save(self, file_bytes: bytes, filename: str) -> str:
        ext = self._validate_extension(filename)
        object_name = f"{uuid4()}{ext}"
        client = self._get_client()

        if not client.bucket_exists(self.bucket_name):  # pragma: no cover - optional backend
            client.make_bucket(self.bucket_name)

        client.put_object(
            self.bucket_name,
            object_name,
            io.BytesIO(file_bytes),
            length=len(file_bytes),
        )

        if self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/{self.bucket_name}/{object_name}"
        return f"minio://{self.bucket_name}/{object_name}"


def build_omr_storage_backend(
    *,
    backend: str = "local",
    local_dir: str = "uploads/scans",
    minio_endpoint: Optional[str] = None,
    minio_access_key: Optional[str] = None,
    minio_secret_key: Optional[str] = None,
    minio_bucket: str = "cola-zero-omr",
    minio_secure: bool = False,
    minio_public_base_url: Optional[str] = None,
) -> OMRStorageBackend:
    backend_normalized = backend.lower().strip()
    if backend_normalized in {"local", ""}:
        return OMRScanStorage(local_dir)
    if backend_normalized == "minio":
        if not minio_endpoint or not minio_access_key or not minio_secret_key:
            raise ValueError(
                "MinIO storage backend requires endpoint, access key and secret key."
            )
        return MinIOOMRScanStorage(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            bucket_name=minio_bucket,
            secure=minio_secure,
            public_base_url=minio_public_base_url,
        )
    raise ValueError(f"Unknown OMR storage backend: {backend}")
