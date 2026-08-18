from fastapi import FastAPI

from app.main import configure_omr_upload_mount


def test_configure_omr_upload_mount_exposes_local_static_files(tmp_path):
    app = FastAPI()

    configure_omr_upload_mount(
        app,
        backend="local",
        local_dir=str(tmp_path / "uploads" / "scans"),
    )

    assert any(getattr(route, "path", None) == "/uploads" for route in app.routes)
    assert (tmp_path / "uploads").exists()


def test_configure_omr_upload_mount_skips_non_local_backends(tmp_path):
    app = FastAPI()

    configure_omr_upload_mount(
        app,
        backend="minio",
        local_dir=str(tmp_path / "uploads" / "scans"),
    )

    assert all(getattr(route, "path", None) != "/uploads" for route in app.routes)
    assert not (tmp_path / "uploads").exists()
