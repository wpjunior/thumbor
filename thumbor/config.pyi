# -*- coding: utf-8 -*-

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

    # Logging
    THUMBOR_LOG_CONFIG: Any
    THUMBOR_LOG_FORMAT: str
    THUMBOR_LOG_DATE_FORMAT: str

    # Imaging
    MAX_WIDTH: int
    MAX_HEIGHT: int
    MAX_PIXELS: float
    MIN_WIDTH: int
    MIN_HEIGHT: int
    ALLOWED_SIZES: list[Any]
    ALLOWED_SOURCES: list[Any]
    QUALITY: int
    PROGRESSIVE_JPEG: bool
    PILLOW_JPEG_SUBSAMPLING: Any
    PILLOW_JPEG_QTABLES: Any
    PILLOW_RESAMPLING_FILTER: str
    WEBP_QUALITY: Any
    AVIF_QUALITY: Any
    AVIF_SPEED: Any
    AVIF_CODEC: str
    AVIF_CODEC_FALLBACK: str
    HEIF_QUALITY: Any
    SRGB_PROFILE: Any
    PNG_COMPRESSION_LEVEL: int
    PILLOW_PRESERVE_INDEXED_MODE: bool
    AUTO_WEBP: bool
    AUTO_AVIF: bool
    AUTO_JPG: bool
    AUTO_HEIF: bool
    AUTO_PNG: bool
    AUTO_PNG_TO_JPG: bool
    AUTO_IMAGE_FORMAT_PREFERENCE: list[Any]
    SVG_DPI: int
    MAX_AGE: int
    MAX_AGE_TEMP_IMAGE: int
    RESPECT_ORIENTATION: bool
    IGNORE_SMART_ERRORS: bool
    SEND_IF_MODIFIED_LAST_MODIFIED_HEADERS: bool
    PRESERVE_EXIF_INFO: bool
    PRESERVE_EXIF_COPYRIGHT_INFO: bool
    PRESERVE_IPTC_INFO: bool
    ALLOW_ANIMATED_GIFS: bool
    ALLOW_ANIMATED_WEBP: bool
    USE_GIFSICLE_ENGINE: bool
    USE_BLACKLIST: bool
    ENGINE_THREADPOOL_SIZE: int

    # Extensibility
    METRICS: str
    LOADER: str
    STORAGE: str
    RESULT_STORAGE: Any
    ENGINE: str
    GIF_ENGINE: str
    URL_SIGNER: str

    # Security
    SECURITY_KEY: str
    ALLOW_UNSAFE_URL: bool

    # HTTP
    ENABLE_ETAGS: bool

    # Storage
    MAX_ID_LENGTH: int

    # Performance
    GC_INTERVAL: Any

    # Healthcheck
    HEALTHCHECK_ROUTE: str

    # Metrics
    STATSD_HOST: Any
    STATSD_PORT: int
    STATSD_PREFIX: Any

    # File Loader
    FILE_LOADER_ROOT_PATH: str

    # HTTP Loader
    HTTP_LOADER_CONNECT_TIMEOUT: int
    HTTP_LOADER_REQUEST_TIMEOUT: int
    HTTP_LOADER_FOLLOW_REDIRECTS: bool
    HTTP_LOADER_MAX_REDIRECTS: int
    HTTP_LOADER_MAX_CLIENTS: int
    HTTP_LOADER_FORWARD_USER_AGENT: bool
    HTTP_LOADER_FORWARD_ALL_HEADERS: bool
    HTTP_LOADER_FORWARD_HEADERS_WHITELIST: list[Any]
    HTTP_LOADER_DEFAULT_USER_AGENT: str
    HTTP_LOADER_PROXY_HOST: Any
    HTTP_LOADER_PROXY_PORT: Any
    HTTP_LOADER_PROXY_USERNAME: Any
    HTTP_LOADER_PROXY_PASSWORD: Any
    HTTP_LOADER_CA_CERTS: Any
    HTTP_LOADER_VALIDATE_CERTS: Any
    HTTP_LOADER_CLIENT_KEY: Any
    HTTP_LOADER_CLIENT_CERT: Any
    HTTP_LOADER_CURL_ASYNC_HTTP_CLIENT: bool

    # General
    HTTP_LOADER_CURL_LOW_SPEED_TIME: int
    HTTP_LOADER_CURL_LOW_SPEED_LIMIT: int
    NON_BLOCKING_SOCKETS: bool
    APP_CLASS: str
    ACCESS_CONTROL_ALLOW_ORIGIN_HEADER: bool

    # File Storage
    STORAGE_EXPIRATION_SECONDS: int
    STORES_CRYPTO_KEY_FOR_EACH_IMAGE: bool
    FILE_STORAGE_ROOT_PATH: str

    # Upload
    UPLOAD_MAX_SIZE: int
    UPLOAD_ENABLED: bool
    UPLOAD_PHOTO_STORAGE: str
    UPLOAD_DELETE_ALLOWED: bool
    UPLOAD_PUT_ALLOWED: bool
    UPLOAD_DEFAULT_FILENAME: str

    # Mixed Storage
    MIXED_STORAGE_FILE_STORAGE: str
    MIXED_STORAGE_CRYPTO_STORAGE: str
    MIXED_STORAGE_DETECTOR_STORAGE: str

    # Meta
    META_CALLBACK_NAME: Any

    # Detection
    DETECTORS: list[Any]
    FACE_DETECTOR_CASCADE_FILE: str
    GLASSES_DETECTOR_CASCADE_FILE: str
    PROFILE_DETECTOR_CASCADE_FILE: str

    # Optimizers
    OPTIMIZERS: list[Any]
    JPEGTRAN_PATH: str
    JPEGTRAN_SCANS_FILE: str
    FFMPEG_PATH: str

    # Filters
    FILTERS: list[str]

    # Result Storage
    RESULT_STORAGE_EXPIRATION_SECONDS: int
    RESULT_STORAGE_FILE_STORAGE_ROOT_PATH: str
    RESULT_STORAGE_STORES_UNSAFE: bool

    # Queued Redis Detector
    REDIS_QUEUE_SERVER_HOST: str
    REDIS_QUEUE_SERVER_PORT: int
    REDIS_QUEUE_SERVER_DB: int
    REDIS_QUEUE_SERVER_PASSWORD: Any
    REDIS_QUEUE_MODE: str
    REDIS_QUEUE_SENTINEL_INSTANCES: str
    REDIS_QUEUE_SENTINEL_PASSWORD: Any
    REDIS_QUEUE_SENTINEL_MASTER_INSTANCE: str
    REDIS_QUEUE_SENTINEL_MASTER_PASSWORD: Any
    REDIS_QUEUE_SENTINEL_MASTER_DB: int
    REDIS_QUEUE_SENTINEL_SOCKET_TIMEOUT: float

    # Queued SQS Detector
    SQS_QUEUE_KEY_ID: Any
    SQS_QUEUE_KEY_SECRET: Any
    SQS_QUEUE_REGION: str

    # Errors
    USE_CUSTOM_ERROR_HANDLING: bool
    ERROR_HANDLER_MODULE: str
    ERROR_FILE_LOGGER: Any
    ERROR_FILE_NAME_USE_CONTEXT: bool

    # Errors - Sentry
    SENTRY_DSN_URL: str
    SENTRY_ENVIRONMENT: Any

    # Server
    MAX_WAIT_SECONDS_BEFORE_SERVER_SHUTDOWN: int
    MAX_WAIT_SECONDS_BEFORE_IO_SHUTDOWN: int

    # HandlerLists
    HANDLER_LISTS: list[str]

    # Compatibility
    COMPATIBILITY_LEGACY_LOADER: Any
    COMPATIBILITY_LEGACY_STORAGE: Any
    COMPATIBILITY_LEGACY_RESULT_STORAGE: Any

    # Deprecated aliases
    ALLOW_ORIGINAL_PHOTO_DELETION: bool
    ALLOW_ORIGINAL_PHOTO_PUTTING: bool
    ENABLE_ORIGINAL_PHOTO_UPLOAD: bool
    MAX_SIZE: int
    ORIGINAL_PHOTO_STORAGE: str
