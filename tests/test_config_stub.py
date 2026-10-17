# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest import TestCase

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "scripts" / "generate_config_stub.py"


def load_generator():
    """Imports the generator, which lives outside the package."""

    spec = importlib.util.spec_from_file_location(
        "generate_config_stub", GENERATOR
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConfigStubTestCase(TestCase):
    def test_stub_is_up_to_date(self):
        """thumbor/config.pyi must match the current Config.define calls.

        The generator runs in a subprocess on purpose. derpconf keeps its
        options in class-level state, and tests/test_config.py registers
        extra aliases there, so comparing against the live Config from
        inside the suite would report a stale stub that is in fact current.
        """

        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )

        assert result.returncode == 0, (
            "thumbor/config.pyi is out of date. Run `make config-stub`.\n"
            f"{result.stdout}{result.stderr}"
        )

    def test_stub_declares_every_option(self):
        generator = load_generator()
        declared = {
            name
            for _, options in generator.collect_options()
            for name, _ in options
        }

        # Read through the generator so this sees the same Config state it
        # does, aliases from other tests included.
        for option in generator.Config.class_defaults:
            assert option in declared, f"{option} missing from the stub"

    def test_infers_annotations_from_defaults(self):
        generator = load_generator()

        assert generator.annotation_for(True) == "bool"
        # bool before int, since bool subclasses int.
        assert generator.annotation_for(1) == "int"
        assert generator.annotation_for(75e6) == "float"
        assert generator.annotation_for("thumbor") == "str"
        assert generator.annotation_for(["a", "b"]) == "list[str]"

    def test_widens_ambiguous_defaults_to_any(self):
        generator = load_generator()

        # A None default says nothing about the accepted type, and an
        # empty or mixed list says nothing about its items.
        assert generator.annotation_for(None) == "Any"
        assert generator.annotation_for([]) == "list[Any]"
        assert generator.annotation_for(["a", 1]) == "list[Any]"
        assert generator.annotation_for(object()) == "Any"

    def test_no_orphan_type_overrides(self):
        """Every TYPE_OVERRIDES key must still be a defined option.

        An override whose option was renamed or removed would sit there
        silently, and the option it was meant to describe would quietly go
        back to Any.
        """

        generator = load_generator()
        defined = set(generator.Config.class_defaults)

        orphans = sorted(set(generator.TYPE_OVERRIDES) - defined)

        assert (
            not orphans
        ), f"TYPE_OVERRIDES names options that no longer exist: {orphans}"

    def test_overrides_only_cover_uninferable_defaults(self):
        """Overrides exist for defaults that say nothing about their type.

        A default that already implies a type should not be overridden by
        hand: the inference is the single source of truth there.
        """

        generator = load_generator()
        defaults = generator.Config.class_defaults

        for name in generator.TYPE_OVERRIDES:
            default = defaults[name]

            assert default is None or default == [], (
                f"{name} has the informative default {default!r}; drop its "
                "override and let the generator infer it"
            )

    def test_no_option_is_left_as_bare_any(self):
        """Any as a whole annotation means we failed to describe an option."""

        generator = load_generator()
        bare_any = [
            name
            for _, options in generator.collect_options()
            for name, annotation in options
            if annotation == "Any"
        ]

        assert not bare_any, f"options still annotated Any: {bare_any}"
