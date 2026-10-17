# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import statsd

from thumbor.metrics import BaseMetrics

if TYPE_CHECKING:
    from thumbor.config import Config


class Metrics(BaseMetrics):
    _client: Any

    @classmethod
    def client(cls, config: Config) -> Any:
        """
        Cache statsd client so it doesn't do a DNS lookup
        over and over
        """
        if not hasattr(cls, "_client"):
            cls._client = statsd.StatsClient(
                config.STATSD_HOST, config.STATSD_PORT, config.STATSD_PREFIX
            )
        return cls._client

    def incr(self, metricname: str, value: int = 1) -> None:
        Metrics.client(self.config).incr(metricname, value)

    def timing(self, metricname: str, value: float) -> None:
        Metrics.client(self.config).timing(metricname, value)
