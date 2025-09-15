import uuid
from typing import Optional

import boto3
from botocore.client import Config as BotoConfig

from app.core.config import settings


class StorageService:
    def __init__(self) -> None:
        self.bucket = settings.aws_s3_bucket
        self.enabled = bool(self.bucket and settings.aws_access_key_id and settings.aws_secret_access_key)
        if self.enabled:
            self.client = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                config=BotoConfig(s3={"addressing_style": "virtual"}),
            )
        else:
            self.client = None

    def upload_bytes(self, data: bytes, key_prefix: str, content_type: Optional[str] = None) -> str:
        key = f"{key_prefix}/{uuid.uuid4().hex}"
        if self.enabled and self.client:
            extra = {"ContentType": content_type} if content_type else None
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **(extra or {}))
            return f"https://{self.bucket}.s3.amazonaws.com/{key}"
        # Fallback: pretend uploaded and return pseudo URL
        return f"https://example.local/{key}"


storage_service = StorageService()
