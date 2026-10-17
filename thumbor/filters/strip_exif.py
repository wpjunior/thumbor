# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from thumbor.filters import BaseFilter, filter_method


class Filter(BaseFilter):
    # Reads self.engine; run() will not execute it without one.
    uses_engine = True

    @filter_method()
    async def strip_exif(self):
        self.engine.strip_exif()
