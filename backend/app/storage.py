"""Upload storage: local disk in dev, S3 when AWS_S3_BUCKET is set."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

_BACKEND_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = _BACKEND_DIR / "static" / "uploads"
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _content_type(ext: str) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(ext, "application/octet-stream")


def save_image(data: bytes, original_filename: str | None) -> str:
    """Persist an image and return a URL the frontend can load directly."""
    ext = os.path.splitext(original_filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise ValueError(f"Unsupported image type '{ext}'. Allowed: {sorted(ALLOWED_IMAGE_EXT)}")

    filename = f"{uuid.uuid4().hex}{ext}"

    if settings.aws_s3_bucket:
        return _save_s3(data, filename, ext)
    return _save_local(data, filename)


def _save_local(data: bytes, filename: str) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / filename).write_bytes(data)
    return f"/static/uploads/{filename}"


def _save_s3(data: bytes, filename: str, ext: str) -> str:
    prefix = (settings.aws_s3_prefix or "costsheet/uploads").strip("/")
    key = f"{prefix}/{filename}"
    region = settings.aws_region or "ap-south-1"

    client = boto3.client("s3", region_name=region)
    try:
        client.put_object(
            Bucket=settings.aws_s3_bucket,
            Key=key,
            Body=data,
            ContentType=_content_type(ext),
            CacheControl="public, max-age=31536000, immutable",
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"S3 upload failed: {exc}") from exc

    return f"https://{settings.aws_s3_bucket}.s3.{region}.amazonaws.com/{key}"
