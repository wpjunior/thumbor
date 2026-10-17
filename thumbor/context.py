# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from thumbor.filters import FiltersFactory
from thumbor.metrics.logger_metrics import Metrics
from thumbor.threadpool import ThreadPool

if TYPE_CHECKING:
    from types import TracebackType

    from tornado.httputil import HTTPServerRequest
    from tornado.web import RequestHandler

    from thumbor.config import Config
    from thumbor.importer import Importer
    from thumbor.metrics import BaseMetrics
    from thumbor.point import FocalPoint


def _split_http_header(value, delimiter):
    parts = []
    current_part = []
    quoted = False
    escaped = False

    for character in value:
        if escaped:
            current_part.append(character)
            escaped = False
            continue

        if quoted and character == "\\":
            current_part.append(character)
            escaped = True
            continue

        if character == '"':
            quoted = not quoted
        elif character == delimiter and not quoted:
            parts.append("".join(current_part))
            current_part = []
            continue

        current_part.append(character)

    parts.append("".join(current_part))
    return parts


def _parse_accept_quality(value):
    try:
        quality = float(value.strip())
    except ValueError:
        return 0.0

    return quality if 0 <= quality <= 1 else 0.0


def _parse_accept_media_range(media_range):
    parts = [part.strip() for part in _split_http_header(media_range, ";")]
    media_type = parts[0].lower()

    if not media_type:
        return None

    for parameter in parts[1:]:
        name, separator, value = parameter.partition("=")
        if not separator:
            continue

        if name.strip().lower() == "q":
            return media_type, _parse_accept_quality(value)

        # Parameters before q apply to the media type itself. Since thumbor
        # cannot match those variants, the media range is not applicable.
        return None

    return media_type, 1.0


def _parse_accept_header(accept_header):
    accepted_media_types = {}

    for media_range in _split_http_header(accept_header or "", ","):
        parsed_media_range = _parse_accept_media_range(media_range)
        if parsed_media_range is None:
            continue

        media_type, quality = parsed_media_range
        accepted_media_types[media_type] = max(
            quality,
            accepted_media_types.get(media_type, 0.0),
        )

    return accepted_media_types


def _accepts_media_type(accepted_media_types, *media_types, allow_any=False):
    for media_type in media_types:
        if media_type in accepted_media_types:
            return accepted_media_types[media_type] > 0

    if "image/*" in accepted_media_types:
        return accepted_media_types["image/*"] > 0

    return allow_any and accepted_media_types.get("*/*", 0) > 0


# Same logic as Importer. This class is very useful and will remain like so for now
class Context:  # pylint: disable=too-many-instance-attributes
    """
    Class responsible for containing:
    * Server Configuration Parameters (port, ip, key, etc);
    * Configurations read from config file (or defaults);
    * Importer with imported modules (engine, filters, detectors, etc);
    * Request Parameters (width, height, smart, meta, etc).

    Each instance of this class MUST be unique per request.
    This class should not be cached in the server.
    """

    # A running server always builds a Context with a server, a config and
    # an importer; the None defaults below only exist so that tests can
    # build a bare one. Declaring these as always-present is what lets
    # `context.config.MAX_WIDTH` and friends type-check across the
    # codebase, at the cost of the two suppressions in __init__.
    server: ServerParameters
    config: Config
    modules: ContextImporter
    metrics: BaseMetrics
    request_handler: RequestHandler | None
    request: RequestParameters
    app_class: str
    filters_factory: FiltersFactory
    thread_pool: ThreadPool
    headers: dict[str, Any]

    def __init__(
        self,
        server: ServerParameters | None = None,
        config: Config | None = None,
        importer: Importer | None = None,
        request_handler: RequestHandler | None = None,
    ) -> None:
        self.server = server  # ty: ignore[invalid-assignment]
        self.config = config  # ty: ignore[invalid-assignment]

        if importer:
            self.modules = ContextImporter(self, importer)

            if importer.metrics:
                self.metrics = importer.metrics(self.config)
            else:
                self.metrics = Metrics(self.config)
        else:
            self.modules = None  # ty: ignore[invalid-assignment]
            self.metrics = Metrics(self.config)

        self.app_class = "thumbor.app.ThumborServiceApp"

        if hasattr(self.config, "APP_CLASS"):
            self.app_class = self.config.APP_CLASS

        if (
            hasattr(self.server, "app_class")
            and self.server.app_class != "thumbor.app.ThumborServiceApp"
        ):
            self.app_class = self.server.app_class

        self.filters_factory = FiltersFactory(
            self.modules.filters if self.modules else []
        )
        self.request_handler = request_handler
        self.thread_pool = ThreadPool.instance(
            getattr(config, "ENGINE_THREADPOOL_SIZE", 0)
        )
        self.headers = {}

    def __enter__(self) -> Context:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.modules:
            self.modules.cleanup()

        self.thread_pool.cleanup()


class ServerParameters:  # pylint: disable=too-many-instance-attributes
    port: int
    ip: str
    config_path: str | None
    keyfile: str | None
    log_level: str
    app_class: str
    debug: bool
    # argparse does not coerce --fd, so it arrives as a socket name or a
    # file descriptor spelled as a string.
    fd: str | int | None
    gifsicle_path: str | None
    use_environment: bool
    processes: int

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        port: int,
        ip: str,  # pylint: disable=invalid-name
        config_path: str | None,
        keyfile: str | None,
        log_level: str,
        app_class: str,
        debug: bool = False,
        fd: str | int | None = None,  # pylint: disable=invalid-name
        gifsicle_path: str | None = None,
        use_environment: bool = False,
        processes: int = 1,
    ) -> None:
        self.port = port
        self.ip = (  # Other people may depend on this pylint: disable=invalid-name
            ip
        )
        self.config_path = config_path
        self.keyfile = keyfile
        self.log_level = log_level
        self.app_class = app_class
        self.debug = debug
        self._security_key: str | bytes | None = None
        self.load_security_key()
        self.fd = (  # Other people may depend on this pylint: disable=invalid-name
            fd
        )
        self.gifsicle_path = gifsicle_path
        self.use_environment = use_environment
        self.processes = processes

    @property
    def security_key(self) -> str | bytes | None:
        return self._security_key

    @security_key.setter
    def security_key(self, key: str | bytes | None) -> None:
        self._security_key = key

    def load_security_key(self) -> None:
        if not self.keyfile:
            return

        configured_path = Path(self.keyfile)
        path = configured_path

        try:
            if configured_path.is_absolute():
                allowed_directory = configured_path.parent.resolve(strict=True)
                path = allowed_directory / configured_path.name
            else:
                allowed_directory = Path.cwd().resolve(strict=True)
                path = allowed_directory / configured_path

            path = path.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise ValueError(
                (
                    f"Could not find security key file at {path.absolute()}. "
                    "Please verify the keypath argument."
                )
            ) from error

        if not path.is_relative_to(allowed_directory):
            raise ValueError(
                (
                    f"Security key file path {configured_path} resolves "
                    "outside its allowed directory. Please verify the "
                    "keypath argument."
                )
            )

        if not path.is_file():
            raise ValueError(
                (
                    f"Could not find security key file at {path}. "
                    "Please verify the keypath argument."
                )
            )

        with path.open("rb") as security_key_file:
            security_key = security_key_file.read().strip()

        self.security_key = security_key


class RequestParameters:  # pylint: disable=too-few-public-methods,too-many-instance-attributes,too-many-locals
    # Only assigned when `trim` is given, but read unconditionally by the
    # transformer, so they are declared rather than inferred.
    trim_pos: str
    trim_tolerance: int

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        debug: bool = False,
        meta: bool = False,
        trim: str | None = None,
        crop_left: int | str | None = None,
        crop_top: int | str | None = None,
        crop_right: int | str | None = None,
        crop_bottom: int | str | None = None,
        crop: dict[str, int | str | None] | None = None,
        adaptive: bool = False,
        full: bool = False,
        fit_in: bool = False,
        stretch: bool = False,
        width: int | str = 0,
        height: int | str = 0,
        horizontal_flip: bool = False,
        vertical_flip: bool = False,
        halign: str = "center",
        valign: str = "middle",
        # Comes off the URL as a string, but defaults to an empty list.
        filters: str | list[Any] | None = None,
        smart: bool = False,
        quality: int = 80,
        image: str | None = None,
        url: str | None = None,
        extension: str | None = None,  # pylint: disable=unused-argument
        buffer: bytes | None = None,  # pylint: disable=unused-argument
        focal_points: list[FocalPoint] | None = None,
        unsafe: bool | str = False,
        # pylint: disable-next=unused-argument,redefined-builtin
        hash: str | None = None,
        accepts_webp: bool = False,
        request: HTTPServerRequest | None = None,
        max_age: int | None = None,
        auto_png_to_jpg: bool | None = None,
        accepts_avif: bool = False,
        accepts_heif: bool = False,
        accepts_png: bool = False,
        accepts_jpeg: bool = False,
    ) -> None:
        self.debug = bool(debug)
        self.meta = bool(meta)
        self.trim = trim

        if trim is not None:
            trim_parts = trim.split(":")
            self.trim_pos = (
                trim_parts[1] if len(trim_parts) > 1 else "top-left"
            )
            self.trim_tolerance = (
                int(trim_parts[2]) if len(trim_parts) > 2 else 0
            )

        if crop is not None:
            self.crop = {k: self.int_or_0(v) for k, v in crop.items()}
        else:
            self.crop = {
                "left": self.int_or_0(crop_left),
                "right": self.int_or_0(crop_right),
                "top": self.int_or_0(crop_top),
                "bottom": self.int_or_0(crop_bottom),
            }

        self.should_crop = (
            self.crop["left"] > 0
            or self.crop["top"] > 0
            or self.crop["right"] > 0
            or self.crop["bottom"] > 0
        )

        self.adaptive = bool(adaptive)
        self.full = bool(full)
        self.fit_in = bool(fit_in)
        self.stretch = bool(stretch)

        self.width = "orig" if width == "orig" else self.int_or_0(width)
        self.height = "orig" if height == "orig" else self.int_or_0(height)
        self.horizontal_flip = bool(horizontal_flip)
        self.vertical_flip = bool(vertical_flip)
        self.halign = halign or "center"
        self.valign = valign or "middle"
        self.smart = bool(smart)

        if filters is None:
            filters = []

        self.filters = filters
        self.image_url = image
        self.url = url
        self.detection_error = None
        self.quality = quality
        self.buffer = None

        if focal_points is None:
            focal_points = []

        self.focal_points = focal_points
        self.hash = hash
        self.prevent_result_storage = False
        self.unsafe = unsafe == "unsafe" or unsafe is True
        self.format = None
        self._set_accepted_image_formats(
            (
                accepts_webp,
                accepts_avif,
                accepts_heif,
                accepts_png,
                accepts_jpeg,
            )
        )
        self.max_bytes = None
        self.no_upscale = False
        self.max_age = max_age
        self.auto_png_to_jpg = auto_png_to_jpg
        self.headers = None
        self._accepted_media_types = {}

        if request:
            self._set_request_headers(request)

    def _set_request_headers(self, request: HTTPServerRequest) -> None:
        accept_header = ""
        self.url = request.path
        if request.headers:
            self.headers = request.headers
            accept_header = request.headers.get("Accept", "")

        self._set_accepted_image_formats_from_header(accept_header)

    def _set_accepted_image_formats_from_header(
        self, accept_header: str
    ) -> None:
        accepted_media_types = _parse_accept_header(accept_header)
        self._accepted_media_types = accepted_media_types
        self._set_accepted_image_formats(
            (
                _accepts_media_type(accepted_media_types, "image/webp"),
                _accepts_media_type(accepted_media_types, "image/avif"),
                _accepts_media_type(accepted_media_types, "image/heif"),
                _accepts_media_type(accepted_media_types, "image/png"),
                _accepts_media_type(
                    accepted_media_types,
                    "image/jpeg",
                    "image/jpg",
                    allow_any=True,
                ),
            )
        )

    def _set_accepted_image_formats(
        self, accepted_formats: tuple[bool, bool, bool, bool, bool]
    ) -> None:
        (
            self.accepts_webp,
            self.accepts_avif,
            self.accepts_heif,
            self.accepts_png,
            self.accepts_jpeg,
        ) = accepted_formats

    @staticmethod
    def int_or_0(value: int | str | None) -> int:
        return 0 if value is None else int(value)


class ContextImporter:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self, context: Context, importer: Importer) -> None:
        self.context = context
        self.importer = importer

        self.engine = None

        if importer.engine:
            self.engine = importer.engine(context)

        self.gif_engine = None

        if importer.gif_engine:
            self.gif_engine = importer.gif_engine(context)

        self.storage = None

        if importer.storage:
            self.storage = importer.storage(context)

        self.result_storage = None

        if importer.result_storage:
            self.result_storage = importer.result_storage(context)

        self.upload_photo_storage = None

        if importer.upload_photo_storage:
            self.upload_photo_storage = importer.upload_photo_storage(context)

        self.loader = importer.loader
        self.detectors = importer.detectors
        self.filters = importer.filters
        self.optimizers = importer.optimizers
        self.url_signer = importer.url_signer

        self.compatibility_legacy_loader = importer.compatibility_legacy_loader

        self.compatibility_legacy_storage = None

        if importer.compatibility_legacy_storage is not None:
            self.compatibility_legacy_storage = (
                importer.compatibility_legacy_storage(context)
            )

        self.compatibility_legacy_result_storage = None

        if importer.compatibility_legacy_result_storage is not None:
            self.compatibility_legacy_result_storage = (
                importer.compatibility_legacy_result_storage(context)
            )

    def cleanup(self) -> None:
        if self.engine:
            self.engine.cleanup()
