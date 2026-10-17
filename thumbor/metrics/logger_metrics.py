# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from thumbor.metrics import BaseMetrics
from thumbor.utils import logger


class Metrics(BaseMetrics):
    def incr(self, metricname: str, value: int = 1) -> None:
        logger.debug("METRICS: inc: %s:%d", metricname, value)

    def timing(self, metricname: str, value: float) -> None:
        logger.debug("METRICS: timing: %s:%d", metricname, value)
