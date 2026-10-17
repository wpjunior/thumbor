# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com


from __future__ import annotations

import os
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thumbor.context import Context


class BaseOptimizer:
    def __init__(self, context: Context) -> None:
        self.context = context

    def should_run(  # pylint: disable=unused-argument
        self, image_extension: str, image_buffer: bytes
    ) -> bool:
        return True

    def run_optimizer(self, image_extension: str, buffer: bytes) -> bytes:
        if not self.should_run(image_extension, buffer):
            return buffer

        ifile = NamedTemporaryFile(  # pylint: disable=consider-using-with
            delete=False
        )
        ofile = NamedTemporaryFile(  # pylint: disable=consider-using-with
            delete=False
        )
        try:
            ifile.write(buffer)
            ifile.close()
            ofile.close()

            self.optimize(buffer, ifile.name, ofile.name)

            with open(
                ofile.name, "rb"
            ) as output_file:  # reopen with file thats been changed with the optimizer
                return output_file.read()
        finally:
            os.unlink(ifile.name)
            os.unlink(ofile.name)

    def optimize(
        self, image_buffer: bytes, input_file: str, output_file: str
    ) -> None:
        raise NotImplementedError()
