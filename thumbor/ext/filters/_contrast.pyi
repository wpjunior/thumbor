# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

# Stub for the C extension of the same name. A type checker cannot read a
# compiled .so, so these signatures are transcribed by hand from the
# PyArg_ParseTuple format string in _contrast.c. Keep them in sync when the
# C signature changes. See docs/typing.md.

def apply(image_mode: str, delta: int, buffer: bytes) -> bytes: ...
