"""Root package info."""
import logging
import os

_root_logger = logging.getLogger()
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

_console = logging.StreamHandler()
_console.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s: %(message)s")
_console.setFormatter(formatter)

# if root logger has handlers, propagate messages up and let root logger process them,
# otherwise use our own handler
if not _root_logger.hasHandlers():
    _logger.addHandler(_console)
    _logger.propagate = False


from lightning_app import components
from lightning_app.__about__ import *
from lightning_app.core.app import LightningApp
from lightning_app.core.flow import LightningFlow
from lightning_app.core.work import LightningWork
from lightning_app.utilities.imports import _module_available
from lightning_app.utilities.packaging.build_config import BuildConfig
from lightning_app.utilities.packaging.cloud_compute import CloudCompute

if _module_available("lightning_app.components.demo"):
    from lightning_app.components import demo

_PACKAGE_ROOT = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.dirname(_PACKAGE_ROOT)

__all__ = ["LightningApp", "LightningFlow", "LightningWork", "BuildConfig", "CloudCompute"]
