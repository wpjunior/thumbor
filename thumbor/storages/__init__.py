# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

import os
from os.path import exists
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from thumbor.context import Context


class BaseStorage:
    """Stores source images, crypto keys and detector results.

    Not to be confused with thumbor.result_storages.BaseStorage, which
    caches finished images and has a different, smaller interface.
    """

    def __init__(self, context: Context) -> None:
        self.context = context

    async def put(self, path: str, file_bytes: bytes) -> str | None:
        """
        :returns: The stored path, when the storage reports one.
        """
        raise NotImplementedError()

    async def put_crypto(self, path: str) -> str | None:
        """
        :returns: The stored path, or None when crypto storage is off.
        """
        raise NotImplementedError()

    async def put_detector_data(self, path: str, data: Any) -> str | None:
        """
        :returns: The stored path, when the storage reports one.
        """
        raise NotImplementedError()

    async def get_crypto(self, path: str) -> str | None:
        raise NotImplementedError()

    async def get_detector_data(self, path: str) -> Any | None:
        raise NotImplementedError()

    async def get(self, path: str) -> bytes | None:
        raise NotImplementedError()

    async def exists(self, path: str) -> bool:
        raise NotImplementedError()

    async def remove(self, path: str) -> None:
        raise NotImplementedError()

    def ensure_dir(self, path: str) -> None:
        if not exists(path):
            try:
                os.makedirs(path)
            except OSError as err:
                # FILE ALREADY EXISTS = 17
                if err.errno != 17:
                    raise
