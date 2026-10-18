# -*- coding: utf-8 -*-
"""A result storage on the old contract: get() returns raw bytes."""

from datetime import datetime, timezone

from thumbor.result_storages import BaseStorage


class Storage(BaseStorage):
    async def put(self, image_bytes):
        return ""

    async def get(self):
        return b"\xff\xd8\xff\xe0 not-a-ResultStorageResult"

    def last_updated(self):
        return datetime(2020, 1, 1, tzinfo=timezone.utc)
