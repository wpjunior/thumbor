# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

import concurrent.futures

from tornado.ioloop import IOLoop

from thumbor.utils import logger


class ThreadPool:
    # Declared so the guard in instance() can test it directly instead of
    # reaching for getattr with a default.
    _instance: dict[int, ThreadPool] | None = None

    @classmethod
    def instance(cls, size: int) -> ThreadPool:
        """
        Cache threadpool since context is
        recreated for each request
        """
        instances = cls._instance
        if instances is None:
            instances = cls._instance = {}
        if size not in instances:
            instances[size] = ThreadPool(size)
        return instances[size]

    @classmethod
    def reset(cls) -> None:
        if cls._instance is not None:
            for instance in cls._instance.values():
                instance.cleanup()
        cls._instance = None

    def __init__(self, thread_pool_size):
        if thread_pool_size:
            self.pool = concurrent.futures.ThreadPoolExecutor(thread_pool_size)
        else:
            self.pool = None

    async def _execute_in_foreground(self, operation, *args):
        return operation(*args)

    async def _execute_in_pool(self, operation, *args):
        loop = IOLoop.current()
        return await loop.run_in_executor(self.pool, operation, *args)

    async def queue(self, operation, *args):
        if not self.pool:
            return await self._execute_in_foreground(operation, *args)

        return await self._execute_in_pool(operation, *args)

    def cleanup(self):
        if self.pool:
            logger.info("Shutting down threads")
            self.pool.shutdown()
