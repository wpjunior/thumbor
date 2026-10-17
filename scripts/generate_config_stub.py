#!/usr/bin/env python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

"""Generates thumbor/config.pyi from the Config.define calls in config.py.

derpconf builds every option at runtime, so a type checker sees none of
them and reports an unresolved attribute for each `config.SOMETHING` read.
The names are all statically known, though: they are the first argument of
the `Config.define` calls in thumbor/config.py. This script imports that
module and writes the stub those definitions imply.

Run it with `make config-stub` after adding, removing or renaming an
option. `tests/test_config_stub.py` fails when the checked-in stub no
longer matches what this script produces.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from derpconf.config import Config

import thumbor.config  # noqa: F401  pylint: disable=unused-import

STUB_PATH = Path(__file__).resolve().parent.parent / "thumbor" / "config.pyi"

HEADER = '''# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

# GENERATED FILE -- DO NOT EDIT.
# Regenerate with `make config-stub` after changing the Config.define calls
# in thumbor/config.py. See docs/typing.md.

import re
from typing import Any, Collection, Sequence

from derpconf.config import Config as _DerpConfig

HOME: str

def generate_config() -> None: ...
def format_value(value: Any) -> Any: ...

class Config(_DerpConfig):
    """Options declared through Config.define in thumbor/config.py.

    derpconf resolves these through __getattr__ at runtime; declaring them
    here is what lets a type checker see them. Most annotations come from
    the default value; the ones a default cannot describe -- None, or an
    empty list -- are listed in TYPE_OVERRIDES in the generator, each
    derived from how thumbor actually reads the option.
    """
'''

# An option whose default is None or an empty list says nothing about its
# type, and Any says nothing to the reader. These are read off the call
# sites instead; the comment on each group is the evidence.
TYPE_OVERRIDES = {
    # Passed to Pillow as the `quality` or `speed` encoder argument.
    "AVIF_QUALITY": "int | None",
    "AVIF_SPEED": "int | None",
    "HEIF_QUALITY": "int | None",
    "WEBP_QUALITY": "int | None",
    # Seconds, per its own description.
    "GC_INTERVAL": "int | None",
    # Dotted module paths the importer resolves.
    "COMPATIBILITY_LEGACY_LOADER": "str | None",
    "COMPATIBILITY_LEGACY_RESULT_STORAGE": "str | None",
    "COMPATIBILITY_LEGACY_STORAGE": "str | None",
    "RESULT_STORAGE": "str | None",
    # Filesystem paths.
    "ERROR_FILE_LOGGER": "str | None",
    "HTTP_LOADER_CA_CERTS": "str | None",
    "HTTP_LOADER_CLIENT_CERT": "str | None",
    "HTTP_LOADER_CLIENT_KEY": "str | None",
    "SRGB_PROFILE": "str | None",
    # Credentials and hostnames, passed straight to the clients.
    "HTTP_LOADER_PROXY_HOST": "str | None",
    "HTTP_LOADER_PROXY_PASSWORD": "str | None",
    "HTTP_LOADER_PROXY_USERNAME": "str | None",
    "REDIS_QUEUE_SENTINEL_MASTER_PASSWORD": "str | None",
    "REDIS_QUEUE_SENTINEL_PASSWORD": "str | None",
    "REDIS_QUEUE_SERVER_PASSWORD": "str | None",
    "SQS_QUEUE_KEY_ID": "str | None",
    "SQS_QUEUE_KEY_SECRET": "str | None",
    "SENTRY_ENVIRONMENT": "str | None",
    "STATSD_HOST": "str | None",
    "STATSD_PREFIX": "str | None",
    # A JSONP function name.
    "META_CALLBACK_NAME": "str | None",
    "HTTP_LOADER_PROXY_PORT": "int | None",
    # Passed to tornado as validate_cert.
    "HTTP_LOADER_VALIDATE_CERTS": "bool | None",
    # Handed to logging.config.dictConfig.
    "THUMBOR_LOG_CONFIG": "dict[str, Any] | None",
    # "Be careful to use int for 0,1,2 and string for 4:4:4 notation",
    # says its own description.
    "PILLOW_JPEG_SUBSAMPLING": "int | str | None",
    # Pillow accepts "keep", a list, a tuple or a dict here.
    "PILLOW_JPEG_QTABLES": "str | Sequence[Any] | dict[int, Any] | None",
    # validate_allowed_sizes accepts a list, tuple, set or frozenset of
    # strings, and _is_size_allowed only needs membership.
    "ALLOWED_SIZES": "Collection[str]",
    # warn_legacy_allowed_sources iterates over strings and compiled
    # patterns alike.
    "ALLOWED_SOURCES": "Sequence[str | re.Pattern[str]]",
    "AUTO_IMAGE_FORMAT_PREFERENCE": "Sequence[str]",
    "HTTP_LOADER_FORWARD_HEADERS_WHITELIST": "Sequence[str]",
    # Dotted module paths, like FILTERS and HANDLER_LISTS.
    "DETECTORS": "Sequence[str]",
    "OPTIMIZERS": "Sequence[str]",
}


def annotation_for(value: Any) -> str:
    """Infers an annotation from an option's default value.

    Deliberately conservative: an ambiguous default widens to Any rather
    than guessing. A wrong annotation here would produce false positives
    across the whole codebase, which costs more than a missing one.
    """

    if value is None:
        # The default says nothing about the type the option accepts.
        return "Any"

    if isinstance(value, bool):
        # Checked before int: bool is a subclass of int.
        return "bool"

    if isinstance(value, (int, float, str)):
        return type(value).__name__

    if isinstance(value, (list, tuple)):
        item_types = {type(item).__name__ for item in value}
        if len(item_types) == 1:
            return f"list[{item_types.pop()}]"
        return "list[Any]"

    return "Any"


def annotation_of(name: str, defaults: Dict[str, Any]) -> str:
    """Returns the annotation for one option, overrides first."""

    if name in TYPE_OVERRIDES:
        return TYPE_OVERRIDES[name]

    return annotation_for(defaults[name])


def collect_options() -> List[Tuple[str, List[Tuple[str, str]]]]:
    """Returns the options as (group, [(name, annotation)]) pairs.

    Grouping follows the fourth argument of Config.define so the stub reads
    in the same order as the generated config file.
    """

    defaults: Dict[str, Any] = Config.class_defaults
    aliases: Dict[str, str] = Config.class_aliased_items
    seen = set()
    groups = []

    for group in Config.class_groups:
        options = []

        for name in Config.class_group_items[group]:
            if name in seen:
                continue

            seen.add(name)
            options.append((name, annotation_of(name, defaults)))

        if options:
            groups.append((group, options))

    # Deprecated spellings still resolve through __getattr__, so code that
    # reads them should type-check too.
    deprecated = [
        (name, annotation_of(target, defaults))
        for name, target in sorted(aliases.items())
        if target in defaults
    ]

    if deprecated:
        groups.append(("Deprecated aliases", deprecated))

    return groups


def render() -> str:
    lines = [HEADER]

    for group, options in collect_options():
        lines.append(f"\n    # {group}\n")
        for name, annotation in options:
            lines.append(f"    {name}: {annotation}\n")

    return "".join(lines)


def main() -> int:
    content = render()

    if "--check" in sys.argv:
        current = STUB_PATH.read_text() if STUB_PATH.exists() else ""

        if current != content:
            print(
                f"{STUB_PATH} is out of date. Run `make config-stub`.",
                file=sys.stderr,
            )
            return 1

        print(f"{STUB_PATH} is up to date.")
        return 0

    STUB_PATH.write_text(content)
    option_count = sum(len(options) for _, options in collect_options())
    print(f"Wrote {STUB_PATH} with {option_count} options.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
