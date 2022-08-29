from typing import Optional, Type

from tsp.dataloggers.AbstractReader import AbstractReader
from tsp.dataloggers.FG2 import FG2
from tsp.dataloggers.GP5W import GP5W

import re

firmwares = {GP5W: re.compile("GP5W", re.IGNORECASE),
             FG2: re.compile("FG2", re.IGNORECASE)}

def detect_geoprecision_type(file: str) -> "Optional[Type[AbstractReader]]":
    """ Detect whether a geoprecision file uses from a 'GP5W' or 'FG2' firmware and return a 

    Parameters
    ----------
    file : str
        Path to a geoprecision file.

    Returns
    -------
    Optional[Type[AbstractReader]]
        An appropriate file reader. If the file corresponds to neither GP5W or FG2, None is returned.
    """
    with open(file, 'r') as f:
        
        header = f.readline()
        
        for g, pattern in firmwares.items():
            if pattern.search(header):
                return g

    return None

