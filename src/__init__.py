__author__ = "bhimes@uber.com"
__version__ = "6.0.0"

import os
import sys
import yaml

__import__('pkg_resources').declare_namespace(__name__)

ABS_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

if not sys.path.count(ABS_ROOT):
    sys.path.append(ABS_ROOT)

with open(os.path.join(ABS_ROOT, "config", "config.yml")) as conf:
    CONFIG = yaml.safe_load(conf)
