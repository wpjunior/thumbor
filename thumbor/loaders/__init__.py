# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Pattern, Protocol

from thumbor.utils import logger

if TYPE_CHECKING:
    from thumbor.context import Context

LEGACY_ALLOWED_SOURCE_REGEX_MARKERS = re.compile(r"[\\^$*+?{}\[\]()|]")
WARNED_LEGACY_ALLOWED_SOURCE_REGEXES = set()


def looks_like_legacy_allowed_source_regex(pattern):
    return isinstance(pattern, str) and bool(
        LEGACY_ALLOWED_SOURCE_REGEX_MARKERS.search(pattern)
    )


def warn_legacy_allowed_source_regex(pattern):
    if pattern in WARNED_LEGACY_ALLOWED_SOURCE_REGEXES:
        return

    WARNED_LEGACY_ALLOWED_SOURCE_REGEXES.add(pattern)
    logger.warning(
        "ALLOWED_SOURCES regex strings are deprecated; "
        "use re.compile(%r) instead.",
        pattern,
    )


def warn_legacy_allowed_sources(allowed_sources):
    for pattern in allowed_sources or []:
        if isinstance(  # pylint: disable=isinstance-second-argument-not-valid-type
            pattern, Pattern
        ):
            continue

        if looks_like_legacy_allowed_source_regex(pattern):
            warn_legacy_allowed_source_regex(pattern)


class LoaderResult:
    ERROR_NOT_FOUND = "not_found"
    ERROR_UPSTREAM = "upstream"
    ERROR_TIMEOUT = "timeout"
    ERROR_BAD_REQUEST = "bad_request"

    buffer: bytes | None
    successful: bool
    error: str | None
    metadata: dict[str, Any]
    extras: dict[str, Any]

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        buffer: bytes | None = None,
        successful: bool = True,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
        extras: dict[str, Any] | None = None,
    ) -> None:
        """
        :param buffer: The media buffer

        :param successful: True when the media has been loaded.
        :type successful: bool

        :param error: Error code
        :type error: str

        :param metadata: Dictionary of metadata about the buffer
        :type metadata: dict

        :param extras: Dictionary of extra information about the error
        :type metadata: dict
        """

        if metadata is None:
            metadata = {}

        if extras is None:
            extras = {}

        self.buffer = buffer
        self.successful = successful
        self.error = error
        self.metadata = metadata
        self.extras = extras


class LoaderModule(Protocol):
    """The interface a loader module exposes to the rest of thumbor.

    Loaders are modules rather than classes: the importer resolves the
    LOADER config value to a module and thumbor calls these functions on
    it, so the members are declared as static methods.

    `validate` is not implemented by every loader -- `file_loader` has no
    such restriction to apply -- which is why BaseHandler.validate guards
    on `hasattr` before calling it. It is declared here because it is part
    of the interface thumbor asks for; a loader that omits it is tolerated
    rather than rejected.
    """

    @staticmethod
    async def load(context: Context, url: str) -> LoaderResult: ...
    @staticmethod
    def validate(context: Context, url: str) -> bool: ...
