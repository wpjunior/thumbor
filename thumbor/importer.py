# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Protocol, Sequence

from thumbor.utils import logger

if TYPE_CHECKING:
    from thumbor.config import Config
    from thumbor.detectors import BaseDetector
    from thumbor.engines import BaseEngine
    from thumbor.filters import BaseFilter
    from thumbor.handler_lists import HandlerListModule
    from thumbor.loaders import LoaderModule
    from thumbor.metrics import BaseMetrics
    from thumbor.optimizers import BaseOptimizer
    from thumbor.result_storages import BaseStorage as BaseResultStorage
    from thumbor.storages import BaseStorage


class UrlSigner(Protocol):
    """The signer interface thumbor uses, as libthumbor defines it.

    Declared here because thumbor/url_signers/__init__.py replaces itself
    in sys.modules with libthumbor's package, so it cannot host a type,
    and libthumbor ships no annotations of its own.
    """

    def __init__(self, security_key: str | bytes) -> None: ...
    def validate(self, actual_signature: bytes, url: str) -> bool: ...
    def signature(self, url: str) -> bytes: ...


def import_class(name: str, get_module: bool = False) -> Any:
    module_name = name if get_module else ".".join(name.split(".")[:-1])
    klass = name.split(".")[-1]

    module = import_module(module_name)
    return module if get_module else getattr(module, klass)


def noop(func: Callable[..., Any]) -> Callable[..., Any]:
    def noop_decorator(*args: Any, **kw: Any) -> Any:
        return func(*args, **kw)  # pass through

    return noop_decorator


# Unfortunately this is a very useful class and rearchitecting it is going to be hard
# So while we agree that it has too many attributes, it will remain like that for now
class Importer:  # pylint: disable=too-many-instance-attributes
    # import_item assigns these through setattr, so they are declared
    # rather than inferred. The ones config.validates_presence_of demands
    # -- engine, gif_engine, loader, storage, metrics, detectors, filters,
    # url_signer, handler_lists -- plus optimizers are always set once
    # import_modules() has run, so they are declared as always-present and
    # the None initialisers below are suppressed. The rest are genuinely
    # conditional on config and keep their None.
    config: Config
    engine: type[BaseEngine]
    gif_engine: type[BaseEngine]
    loader: LoaderModule
    url_signer: type[UrlSigner]
    storage: type[BaseStorage]
    metrics: type[BaseMetrics]
    # load_multiple_item replaces the initial list with a tuple, hence
    # Sequence rather than either concrete type.
    detectors: Sequence[type[BaseDetector]]
    filters: Sequence[type[BaseFilter]]
    optimizers: Sequence[type[BaseOptimizer]]
    handler_lists: Sequence[HandlerListModule]

    upload_photo_storage: type[BaseStorage] | None
    result_storage: type[BaseResultStorage] | None
    error_handler_module: Any | None
    error_handler_class: Any | None
    # Assigned from outside, by server.py, once the class is resolved.
    error_handler: Any
    # Injected on demand by MixedStorage, which calls import_item with its
    # own config keys rather than going through import_modules.
    file_storage: type[BaseStorage]
    crypto_storage: type[BaseStorage]
    detector_storage: type[BaseStorage]

    compatibility_legacy_loader: ModuleType | None
    compatibility_legacy_storage: type[BaseStorage] | None
    compatibility_legacy_result_storage: type[BaseStorage] | None

    def __init__(self, config: Config) -> None:
        self.config = config
        self.engine = None  # ty: ignore[invalid-assignment]
        self.gif_engine = None  # ty: ignore[invalid-assignment]
        self.loader = None  # ty: ignore[invalid-assignment]
        self.url_signer = None  # ty: ignore[invalid-assignment]
        self.upload_photo_storage = None
        self.storage = None  # ty: ignore[invalid-assignment]
        self.metrics = None  # ty: ignore[invalid-assignment]
        self.result_storage = None
        self.detectors = []
        self.filters = []
        self.optimizers = []
        self.handler_lists = []
        self.error_handler_module = None
        self.error_handler_class = None
        self.compatibility_legacy_loader = None
        self.compatibility_legacy_storage = None
        self.compatibility_legacy_result_storage = None

    @staticmethod
    def import_class(
        name: str,
        get_module: bool = False,
        validate_fn: Callable[[Any], None] | None = None,
    ) -> Any:
        kls = import_class(name, get_module)
        if validate_fn is not None:
            validate_fn(kls)
        return kls

    def import_modules(self) -> None:
        if (
            self.config.COMPATIBILITY_LEGACY_LOADER
            or self.config.COMPATIBILITY_LEGACY_STORAGE
            or self.config.COMPATIBILITY_LEGACY_RESULT_STORAGE
        ):
            Importer.deprecated_monkey_patch_tornado_return_future()

        self.config.validates_presence_of(
            "ENGINE",
            "GIF_ENGINE",
            "LOADER",
            "STORAGE",
            "DETECTORS",
            "FILTERS",
            "URL_SIGNER",
            "METRICS",
            "HANDLER_LISTS",
        )

        self.import_item("ENGINE", "Engine")
        self.import_item("GIF_ENGINE", "Engine")
        self.import_item("LOADER")
        self.import_item("STORAGE", "Storage")
        self.import_item("METRICS", "Metrics")
        self.import_item("DETECTORS", "Detector", is_multiple=True)
        self.import_item(
            "FILTERS", "Filter", is_multiple=True, ignore_errors=True
        )
        self.import_item("HANDLER_LISTS", is_multiple=True)
        self.import_item("OPTIMIZERS", "Optimizer", is_multiple=True)
        self.import_item("URL_SIGNER", "UrlSigner")

        if self.config.RESULT_STORAGE:
            self.import_item("RESULT_STORAGE", "Storage")

        if self.config.UPLOAD_PHOTO_STORAGE:
            self.import_item("UPLOAD_PHOTO_STORAGE", "Storage")

        if self.config.USE_CUSTOM_ERROR_HANDLING:
            self.import_item("ERROR_HANDLER_MODULE", "ErrorHandler")
            self.error_handler_class = self.error_handler_module

        if self.config.COMPATIBILITY_LEGACY_LOADER:
            self.import_item("COMPATIBILITY_LEGACY_LOADER")

        if self.config.COMPATIBILITY_LEGACY_STORAGE:
            self.import_item("COMPATIBILITY_LEGACY_STORAGE", "Storage")

        if self.config.COMPATIBILITY_LEGACY_RESULT_STORAGE:
            self.import_item("COMPATIBILITY_LEGACY_RESULT_STORAGE", "Storage")

    @staticmethod
    def deprecated_monkey_patch_tornado_return_future() -> None:
        import tornado.concurrent  # pylint: disable=import-outside-toplevel

        if not hasattr(tornado.concurrent, "return_future"):
            setattr(tornado.concurrent, "return_future", noop)

    def import_item(  # pylint: disable=too-many-positional-arguments
        self,
        config_key: str | None = None,
        class_name: str | None = None,
        is_multiple: bool = False,
        item_value: Any = None,
        ignore_errors: bool = False,
        validate_fn: Callable[[Any], None] | None = None,
    ) -> None:
        # Every caller passes config_key; the None default is vestigial,
        # and the method cannot do anything useful without it.
        if item_value is None:
            conf_value = getattr(
                self.config, config_key  # ty: ignore[invalid-argument-type]
            )
        else:
            conf_value = item_value

        if is_multiple:
            self.load_multiple_item(
                config_key,  # ty: ignore[invalid-argument-type]
                conf_value,
                class_name,
                ignore_errors,
                validate_fn,
            )
        else:
            if class_name is not None:
                module = self.import_class(f"{conf_value}.{class_name}")
            else:
                module = self.import_class(conf_value, get_module=True)
            setattr(self, config_key.lower(), module)

    def load_multiple_item(  # pylint: disable=too-many-positional-arguments
        self,
        config_key: str,
        conf_value: Sequence[str] | None,
        class_name: str | None,
        ignore_errors: bool,
        validate_fn: Callable[[Any], None] | None,
    ) -> None:
        modules = []
        if conf_value:
            for module_name in conf_value:
                try:
                    if class_name is not None:
                        if class_name == "*":
                            module = self.import_class(
                                module_name, validate_fn=validate_fn
                            )
                        else:
                            module = self.import_class(
                                f"{module_name}.{class_name}",
                                validate_fn=validate_fn,
                            )
                    else:
                        module = self.import_class(
                            module_name,
                            get_module=True,
                            validate_fn=validate_fn,
                        )
                    modules.append(module)
                except ImportError as error:
                    if ignore_errors:
                        logger.warning(
                            "Module %s could not be imported: %s",
                            module_name,
                            error,
                        )
                    else:
                        raise
        setattr(self, config_key.lower(), tuple(modules))
