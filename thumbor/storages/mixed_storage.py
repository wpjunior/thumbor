# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from thumbor.storages import BaseStorage

if TYPE_CHECKING:
    from thumbor.context import Context


class Storage(BaseStorage):
    # Lazily built: each public method calls the matching _init_* first, so
    # by the time anything reads these they are set. The None defaults are
    # a construction artifact -- see the rule in docs/typing.md.
    file_storage: BaseStorage
    crypto_storage: BaseStorage
    detector_storage: BaseStorage

    def __init__(
        self,
        context: Context,
        file_storage: BaseStorage | None = None,
        crypto_storage: BaseStorage | None = None,
        detector_storage: BaseStorage | None = None,
    ) -> None:
        BaseStorage.__init__(self, context)

        self.file_storage = file_storage  # ty: ignore[invalid-assignment]

        self.crypto_storage = crypto_storage  # ty: ignore[invalid-assignment]

        # ty: ignore[invalid-assignment]
        self.detector_storage = detector_storage

    def _init_file_storage(self) -> None:
        if self.file_storage is None:
            self.context.modules.importer.import_item(
                config_key="file_storage",
                item_value=self.context.config.MIXED_STORAGE_FILE_STORAGE,
                class_name="Storage",
            )
            self.file_storage = self.context.modules.file_storage = (
                self.context.modules.importer.file_storage(self.context)
            )

    def _init_crypto_storage(self) -> None:
        if self.crypto_storage is None:
            self.context.modules.importer.import_item(
                config_key="crypto_storage",
                item_value=self.context.config.MIXED_STORAGE_CRYPTO_STORAGE,
                class_name="Storage",
            )
            self.crypto_storage = self.context.modules.crypto_storage = (
                self.context.modules.importer.crypto_storage(self.context)
            )

    def _init_detector_storage(self) -> None:
        if self.detector_storage is None:
            self.context.modules.importer.import_item(
                config_key="detector_storage",
                item_value=self.context.config.MIXED_STORAGE_DETECTOR_STORAGE,
                class_name="Storage",
            )
            self.detector_storage = self.context.modules.detector_storage = (
                self.context.modules.importer.detector_storage(self.context)
            )

    async def put(self, path: str, file_bytes: bytes) -> str | None:
        self._init_file_storage()
        return await self.file_storage.put(path, file_bytes)

    async def put_detector_data(self, path: str, data: Any) -> str | None:
        self._init_detector_storage()
        return await self.detector_storage.put_detector_data(path, data)

    async def put_crypto(self, path: str) -> str | None:
        self._init_crypto_storage()
        return await self.crypto_storage.put_crypto(path)

    async def get_crypto(self, path: str) -> str | None:
        self._init_crypto_storage()
        result = await self.crypto_storage.get_crypto(path)
        return result

    async def get_detector_data(self, path: str) -> Any | None:
        self._init_detector_storage()
        result = await self.detector_storage.get_detector_data(path)
        return result

    async def get(self, path: str) -> bytes | None:
        self._init_file_storage()
        result = await self.file_storage.get(path)
        return result

    async def exists(self, path: str) -> bool:
        self._init_file_storage()
        result = await self.file_storage.exists(path)
        return result

    def resolve_original_photo_path(self, request: Any, filename: str) -> Any:
        # No storage shipped with thumbor defines this method, and no
        # _init_file_storage() runs first either, so this raises
        # AttributeError whichever way it is reached. Kept as is because it
        # is public; see the open findings in docs/typing.md.
        return self.file_storage.resolve_original_photo_path(  # ty: ignore[unresolved-attribute]
            request, filename
        )
