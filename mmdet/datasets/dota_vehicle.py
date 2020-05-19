from .coco import CocoDataset
from .builder import DATASETS


@DATASETS.register_module
class DotaVehicleDataset(CocoDataset):
    CLASSES = ('small-vehicle', )
