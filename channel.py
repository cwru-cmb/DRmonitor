import pandas as pd
from datetime import datetime
import os
import io


class Channel:
    """
    This as a class for storing all the time series data from a given
    channel

    Attributes:
        data: a pandas.DataFrame object with the data
        paths: an array of the paths of files that contributed to the data (must be added manually)
        file: (only after Channel.open_recent()) the file object of the most recent file. Kept open so that one may poll for new data using file.read() 
        name: the name of the channel
    """

    def __init__(self, name: str | None = None):
        self.name: str = name
        self.paths: list[str] = []
        self.data: pd.DataFrame | None = None
        self.file: io.TextIOWrapper | None = None

        return

    def _d(self, date): return datetime.strptime(date, "%y-%m-%d")
    
    def add_data(self, newData: pd.DataFrame | list):
        """Appends newData to previous data using pandas.concat"""
        # TODO retest live data
        if (self.data is None): self.data = pd.DataFrame(newData)
        else: self.data = pd.concat((self.data, pd.DataFrame(newData)))
    
    def add_path(self, path: str):
        """"Adds file path to the list of contributing file paths"""
        self.paths.append(path)

    def most_recent_path(self) -> str | None:
        """
        Returns the path with the most recent date. Assumes all paths are of the form "[name]yy-mm-dd.[3 letter extension]"
        """
        if (len(self.paths) is 0): return None

        mrp = self.paths[0]
        for path in self.paths:
            # isolate the yy-mm-dd portion of the filename
            prev_date = mrp[-12:-4]
            cur_date = path[-12:-4]

            if (self._d(cur_date) > self._d(prev_date)):
                mrp = path
        
        return mrp
    
    def open_recent(self):
        """
        Opens the most recent file in paths
        """
        path = self.most_recent_path()
        
        self.file = open(path, 'r')

        # place the current read head at the end of the file
        self.file.seek(0, os.SEEK_END)




