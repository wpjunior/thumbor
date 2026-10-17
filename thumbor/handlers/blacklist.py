# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from thumbor.handlers import ContextHandler
from thumbor.utils import logger


class BlacklistHandler(ContextHandler):
    # tornado types its verb handlers as (*args: str, **kwargs: str);
    # thumbor declares the concrete arguments its routes capture.
    # ty: ignore[invalid-method-override]
    async def get(self):
        blacklist = await self.get_blacklist_contents()

        self.write(blacklist)
        self.set_header("Content-Type", "text/plain")
        self.set_status(200)

    # tornado types its verb handlers as (*args: str, **kwargs: str);
    # thumbor declares the concrete arguments its routes capture.
    # ty: ignore[invalid-method-override]
    async def put(self):
        blacklist = await self.get_blacklist_contents()
        # tornado declares request.query with a legacy type comment over a
        # None class attribute, which ty reads as None | Unknown | str.
        # ty: ignore[unsupported-operator]
        blacklist += self.request.query + "\n"
        logger.debug("Adding to blacklist: %s", self.request.query)
        await self.context.modules.storage.put(
            "blacklist.txt", blacklist.encode()
        )
        self.set_status(200)
