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
    async def upscale(self):
        target_width = self.context.request.width
        target_height = self.context.request.height

        # A dimension arrives as the string "orig" when the URL asks for the
        # source size, in which case there is no target to scale up to.
        # Comparing it against the source raised TypeError before this.
        if isinstance(target_width, str) or isinstance(target_height, str):
            return

        source_width, source_height = self.engine.size

        if source_width >= target_width or source_height >= target_height:
            return

        if (
            source_width * 1.0 / target_width
            >= source_height * 1.0 / target_height
        ):
            new_width = target_width
            new_height = int(source_height * target_width / source_width)
        else:
            new_width = int(source_width * target_height / source_height)
            new_height = target_height

        self.engine.resize(new_width, new_height)
