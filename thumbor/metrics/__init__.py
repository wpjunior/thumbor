# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tornado.web import RequestHandler

    from thumbor.config import Config


class BaseMetrics:
    def __init__(self, config: Config) -> None:
        self.config = config

    def initialize(self, handler: RequestHandler) -> None:
        pass

    def incr(self, metricname: str, value: int = 1) -> None:
        raise NotImplementedError()

    def timing(self, metricname: str, value: float) -> None:
        raise NotImplementedError()
