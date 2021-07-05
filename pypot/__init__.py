import logging

from . import dynamixel
from ._version import __version__

logging.getLogger(__name__).addHandler(logging.NullHandler())
