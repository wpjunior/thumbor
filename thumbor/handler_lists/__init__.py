# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from tornado.routing import _RuleList

if TYPE_CHECKING:
    from thumbor.context import Context

BUILTIN_HANDLERS = [
    "thumbor.handler_lists.healthcheck",
    "thumbor.handler_lists.upload",
    "thumbor.handler_lists.blacklist",
]

HandlerList = _RuleList


class HandlerListModule(Protocol):
    """The interface a handler list module exposes to the importer.

    Like loaders, handler lists are modules, not classes, so the member is
    declared as a static method.
    """

    @staticmethod
    def get_handlers(context: Context) -> HandlerList: ...
