# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2015 popsugar.com vtodorov@popsugar.com

from __future__ import annotations

from thumbor.result_storages import BaseStorage, ResultStorageResult


class Storage(BaseStorage):
    async def put(self, image_bytes: bytes) -> str | None:
        return ""

    async def get(self) -> ResultStorageResult | None:
        return None
