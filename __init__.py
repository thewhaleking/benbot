__author__ = "bhimes@uber.com"
__version__ = "5.2.0"

import os
import sys

__import__('pkg_resources').declare_namespace(__name__)

ABS_ROOT = os.path.abspath(os.path.dirname(__file__))

if not sys.path.count(ABS_ROOT):
    sys.path.append(ABS_ROOT)


def get_root():
    return ABS_ROOT
