# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

from typing import TYPE_CHECKING

from thumbor.handler_lists import HandlerList
from thumbor.handlers.blacklist import BlacklistHandler

if TYPE_CHECKING:
    from thumbor.context import Context


def get_handlers(context: Context) -> HandlerList:
    is_blacklist_enabled = context.config.USE_BLACKLIST
    if not is_blacklist_enabled:
        return []

    return [(r"/blacklist/?", BlacklistHandler, {"context": context})]
