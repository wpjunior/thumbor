# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com


from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from thumbor.detectors import BaseDetector
from thumbor.detectors.local_detector import CascadeLoaderDetector

if TYPE_CHECKING:
    from thumbor.context import Context

HAIR_OFFSET = 0.12


class Detector(CascadeLoaderDetector):
    def __init__(
        self,
        context: Context,
        index: int,
        detectors: Sequence[type[BaseDetector]],
    ) -> None:
        super().__init__(context, index, detectors)
        self.load_cascade_file(
            __file__, self.context.config.FACE_DETECTOR_CASCADE_FILE
        )

    def get_origin(self) -> str:
        return "Face Detection"

    def get_detection_offset(
        self, left: int, top: int, width: int, height: int
    ) -> dict[str, float]:
        top_offset = -1 * height * HAIR_OFFSET

        if top - height * HAIR_OFFSET < 0.0:
            top_offset = 0.0

        return {"top": top_offset}
