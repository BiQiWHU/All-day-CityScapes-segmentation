from .DDRNet_23_slim import get_ddrnet_23_slim
from .DDRNet_39 import get_ddrnet_39
from .DDRNet_23 import get_ddrnet_23
from .DDRNet_23_vis1 import get_ddrnet_23_vis1

from .DDRNet_23 import get_CA_interact
from .DDRNet_23 import get_CA_merge

models = {
    'ddrnet_39': get_ddrnet_39,
    'ddrnet_23_slim': get_ddrnet_23_slim,
    'ddrnet_23': get_ddrnet_23,
    'ddrnet_23_vis1': get_ddrnet_23_vis1,
}

intermodule={'inter': get_CA_interact}

mergemodule={'merge': get_CA_merge}

def get_segmentation_model(model, **kwargs):
    """Segmentation models"""
    return models[model.lower()](**kwargs)

def get_inter_model(model, **kwargs):
    """interaction C-A module"""
    return intermodule[model.lower()](**kwargs)

def get_merge_model(model, **kwargs):
    """merge C-A models"""
    return mergemodule[model.lower()](**kwargs)
