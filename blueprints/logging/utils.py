# -*- encoding: utf-8 -*-

from application.utils import create_config_func
from .models import ConfigVariables
from .config import MODULE_NAME

_config = create_config_func(MODULE_NAME, ConfigVariables)