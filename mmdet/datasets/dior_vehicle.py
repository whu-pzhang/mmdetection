from .builder import DATASETS
from .coco import CocoDataset


@DATASETS.register_module
class DiorVehicleDataset(CocoDataset):
    CLASSES = ('vehicle', )
