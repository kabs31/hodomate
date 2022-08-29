from tsp.core import TSP, IndexedTSP
from tsp.misc import _is_depth_column
from tsp.plots.static import trumpet_curve
from tsp.readers import read_gtnp, read_geotop, read_geoprecision, read_hoboware, read_ntgs

#TSP.__module__ = "teaspoon"

__all__ = ["TSP", "IndexedTSP"]