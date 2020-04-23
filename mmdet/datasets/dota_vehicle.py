from .coco import CocoDataset
from .registry import DATASETS


@DATASETS.register_module
class DotaVehicleDataset(CocoDataset):
    CLASSES = ('small-vehicle', )
