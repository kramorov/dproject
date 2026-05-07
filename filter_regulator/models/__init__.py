#filter_requlator/models/__init__.py
from .fr_options import *
from .fr_body import *
from .fr_model_line import *
from .fr_model_line_item import *

__all__ = [
    # все модели, которые должны быть доступны извне
    'FilterRegulatorBody' ,
    'DrainVariety' ,
    'FilterRegulatorVariety' ,
    'FilterRegulatorModelLine' ,
    'FilterRegulator' ,
    # '',
]

