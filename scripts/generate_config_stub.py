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

from typing import Any

from derpconf.config import Config as _DerpConfig

HOME: str

def generate_config() -> None: ...
def format_value(value: Any) -> Any: ...

class Config(_DerpConfig):
    """Options declared through Config.define in thumbor/config.py.

    derpconf resolves these through __getattr__ at runtime; declaring them
    here is what lets a type checker see them. An option whose default is
    None has no inferable type and is annotated Any.
    """
'''


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
            options.append((name, annotation_for(defaults[name])))

        if options:
            groups.append((group, options))

    # Deprecated spellings still resolve through __getattr__, so code that
    # reads them should type-check too.
    deprecated = [
        (name, annotation_for(defaults[target]))
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
