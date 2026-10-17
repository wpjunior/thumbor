# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

from thumbor.point import FocalPointDict
from thumbor.storages import BaseStorage


class Storage(BaseStorage):
    async def put(self, path: str, file_bytes: bytes) -> str | None:
        return path

    async def put_crypto(self, path: str) -> str | None:
        return path

    async def put_detector_data(
        self, path: str, data: list[FocalPointDict]
    ) -> str | None:
        return path

    async def get_crypto(self, path: str) -> str | None:
        return None

    async def get_detector_data(
        self, path: str
    ) -> list[FocalPointDict] | None:
        return None

    async def get(self, path: str) -> bytes | None:
        return None

    async def exists(self, path: str) -> bool:
        return False

    async def remove(self, path: str) -> None:
        pass
