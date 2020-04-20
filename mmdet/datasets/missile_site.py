from .coco import CocoDataset
from .registry import DATASETS


@DATASETS.register_module
class MissileSiteDataset(CocoDataset):
    CLASSES = ('A1', 'A2', 'A3')
