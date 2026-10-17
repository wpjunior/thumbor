# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

import os
from os.path import exists
from typing import TYPE_CHECKING

from thumbor.engines import BaseEngine
from thumbor.loaders import LoaderResult

if TYPE_CHECKING:
    from datetime import datetime

    from thumbor.context import Context


class ResultStorageResult(LoaderResult):
    @property
    def last_modified(self) -> datetime | None:
        """
        Retrieves last_updated metadata if available
        :return:
        """
        return self.metadata.get("LastModified", None)

    @property
    def mime(self) -> str | None:
        """
        Retrieves mime metadata if available
        :return:
        """
        return (
            self.metadata["ContentType"]
            if "ContentType" in self.metadata
            else BaseEngine.get_mimetype(self.buffer)
        )

    def __len__(self) -> int:
        return (
            self.metadata["ContentLength"]
            if "ContentLength" in self.metadata
            else len(self.buffer)
        )


class BaseStorage:
    """Caches finished images.

    Not to be confused with thumbor.storages.BaseStorage, which stores
    source images and has a wider interface.
    """

    def __init__(self, context: Context) -> None:
        self.context = context

    async def put(self, image_bytes: bytes) -> str | None:
        raise NotImplementedError()

    async def get(self) -> ResultStorageResult | None:
        raise NotImplementedError()

    def last_updated(self) -> datetime:
        raise NotImplementedError()

    def ensure_dir(self, path: str) -> None:
        if not exists(path):
            try:
                os.makedirs(path)
            except OSError as err:
                # FILE ALREADY EXISTS = 17
                if err.errno != 17:
                    raise
