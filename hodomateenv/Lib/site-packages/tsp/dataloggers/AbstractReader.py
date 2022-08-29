from abc import ABCMeta, abstractmethod
import pandas as pd

class AbstractReader(object):
    __metaclass__ = ABCMeta

    def __init__(self, datefmt=None):
        self.DATA = []
        self.META = dict()
        if datefmt:
            self.DATEFMT = datefmt

    @abstractmethod
    def read(self, file) -> "pd.DataFrame":
        """read data from a file"""

    def get_data(self):
        return self.DATA
