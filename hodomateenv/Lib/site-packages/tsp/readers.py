import datetime
import numpy as np
import pandas as pd
import re
import warnings

try:
    import netCDF4 as nc
except ModuleNotFoundError:
    warnings.warn("Missing netCDF4 library. Some functionality will be limited.")

from pathlib import Path
from typing import Union, Optional

from tsp.dataloggers.Geoprecision import detect_geoprecision_type
from tsp.dataloggers.HOBO import HOBO, HOBOProperties

from tsp.core import TSP, IndexedTSP
from tsp.misc import _is_depth_column


def read_csv(filepath: str,
              datecol: "Union[str, int]",
              datefmt:str = "%Y-%m-%d %H:%M:%S",
              depth_pattern: str = r"^(-?[0-9\.]+)$",
              na_values:list = [],
              **kwargs) -> TSP:
    r"""Read an arbitrary CSV file 
   
    Date and time must be in a single column, and the csv must be in the
    'wide' data format (each depth is a separate column)

    Parameters
    ----------
    filepath : str
        Path to csv file
    datecol : Union[str, int]
        Either the numeric index (starting at 0) of date column (if int) or name of date column or regular expression (if str)
    datefmt : str, optional
        The format of the datetime values. Use `python strftime format codes <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes>`_, 
        by default ``"%Y-%m-%d %H:%M:%S"``
    depth_pattern : str, optional
        A regular expression that matches the column names with depths. The regular expression must
        have a single capture group that extracts just the numeric part of the column header, by default r"^(-?[0-9\.]+)$".
        If column names were in the form ``"+/-1.0_m"`` (i.e. included 'm' to denote units), you could use the regular expression ``r"^(-?[0-9\.]+)_m$"``
    na_values : list, optional
        Additional strings to recognize as NA. Passed to pandas.read_csv, by default []

    Returns
    -------
    TSP
        A TSP
    """
    
    raw = pd.read_csv(filepath, na_values=na_values, **kwargs)
    
    if not datecol in raw.columns and isinstance(datecol, str):
        datecol = [re.search(datecol, c).group(1) for c in raw.columns if re.search(datecol, c)][0]
    
    time = pd.to_datetime(raw[datecol], format=datefmt).to_numpy()

    depth = [re.search(depth_pattern, c).group(1) for c in raw.columns if _is_depth_column(c, depth_pattern)]
    depth_numeric = np.array([float(d) for d in depth])

    values = raw.loc[:, depth].to_numpy()

    t = TSP(time, depth_numeric, values)

    return t


def read_gtnp(filename: str, metadata_filepath=None) -> TSP:
    """Read test file from GTN-P database export

    Parameters
    ----------
    filename : str
        Path to file.
    metadata_file : str, optional
        Path to GTN-P metadata file, by default None

    Returns
    -------
    TSP
        A TSP
    """
    t = read_csv(filename,
                   na_values=[-999.0],
                   datecol="Date/Depth",
                   datefmt="%Y-%m-%d %H:%M:%S",
                   depth_pattern=r"^(-?[0-9\.]+)$")

    return t


def read_geotop(file: str) -> TSP:
    """Read a GEOtop soil temperature output file

    Parameters
    ----------
    file : str
        Path to file.

    Returns
    -------
    TSP
        A TSP
    """
    t = read_csv(file,
                   na_values=[-9999.0],
                   datecol="^(Date.*)",
                   datefmt=r"%d/%m/%Y %H:%M",
                   depth_pattern=r"^(-?[0-9\.]+)$")
    
    t._depths *= 0.001  # Convert to [m]

    return t


def read_gtpem(file: str) -> "list[TSP]":
    output = list()
    try:
        with nc.Dataset(file) as ncdf:
            n_sim = len(ncdf['geotop']['sitename'][:])
            time = 1
            for i, name in enumerate(ncdf['geotop']['sitename'][:]):
                pass
                #t = TSP()
    except NameError:
        warnings.warn("netCDF4 library must be installed.")
    
    return output


def read_ntgs(filename: str) -> TSP:
    """Read a file from the NTGS permafrost database

    Parameters
    ----------
    filename : str
        Path to file.

    Returns
    -------
    TSP
        A TSP
    """
    if Path(filename).suffix == ".csv":
        try:
            raw = pd.read_csv(filename, keep_default_na=False,na_values=[''], parse_dates={"time": [4,5]}, date_parser=__nt_date_parser)
        except IndexError:
            raise IndexError("There are insufficient columns, the file format is invalid.")
    elif Path(filename).suffix in [".xls", ".xlsx"]:
        raise NotImplementedError("Convert to CSV")
        #try:
        #    raw = pd.read_excel(filename, keep_default_na=False, parse_dates={"time": [4,5]}, date_parser=self.getISOFormat)
        #except IndexError:
        #    raise IndexError("There are insufficient columns, the file format is invalid.") 
    else:
        raise TypeError("Unsupported file extension.")

    metadata = {
                'project_name': raw['project_name'][0],
                'site_id': raw['site_id']
                }
    match_depths = [c for c in [re.search(r"(-?[0-9\.]+)_m$", C) for C in raw.columns] if c]
    values = raw.loc[:, [d.group(0) for d in match_depths]].values
    times = raw['time'].dt.to_pydatetime()
        
    t = TSP(times=times,
              depths=[float(d.group(1)) for d in match_depths],
              values=values,
              latitude=raw['latitude'].values[0],
              longitude=raw['longitude'].values[0],
              metadata=metadata)

    return t


def __nt_date_parser(date, time) -> datetime.datetime:
        if isinstance(date, str):
            # Case from CSV files where the date is string
            try:
                year, month, day = [int(dateVal) for dateVal in date.split("-")]
            except ValueError:
                raise ValueError(f"The date {date} was unable to be parsed. The format required is YYYY-MM-DD.")
        elif isinstance(date, datetime.datetime):
            # Case XLSX files - are "timestamp" objects
            year, month, day = date.year, date.month, date.day
        else:
            raise ValueError(f"The date {date} was unable to be parsed.")
            
        if isinstance(time, str):
            try:
                h, m, s = [int(timeVal) for timeVal in time.split(":")]
            except ValueError:
                raise ValueError(f"The time {time} was unable to be parsed. The format required is (H)H:MM:SS.")
        
        elif isinstance(time, datetime.time):
            h, m, s = int(time.hour), time.minute, time.second
        
        else:
            raise ValueError(f"The time {time} was unable to be parsed.")
        
        return datetime.datetime(year, month, day, hour=h, minute=m, second=s)


def read_geoprecision(filepath: str) -> IndexedTSP:
    """Read a Geoprecision datalogger export (text file)

    Reads GP5W- and FG2-style files from geoprecision.

    Parameters
    ----------
    filepath : str
        Path to file.

    Returns
    -------
    IndexedTSP
        An IndexedTSP
    """
    reader = detect_geoprecision_type(filepath)
    
    if reader is None:
        raise RuntimeError("Could not detect type of geoprecision file (GP5W or FG2 missing from header")

    data = reader().read(filepath)

    t = IndexedTSP(times=data['TIME'].dt.to_pydatetime(),
                     values=data.drop("TIME", axis=1).values)

    return t



def read_hoboware(filepath: str, hoboware_config: Optional[HOBOProperties]=None) -> IndexedTSP:
    """Read Onset HoboWare datalogger exports

    Parameters
    ----------
    filepath : str
        Path to a file
    hoboware_config : HOBOProperties, optional
        A HOBOProperties object with information about how the file is configured. If not 
        provided, the configuration will be automatically detected if possible, by default None

    Returns
    -------
    IndexedTSP
        An IndexedTSP. Use the `set_depths` method to provide depth information
    """
    reader = HOBO(properties=hoboware_config)
    data = reader.read(filepath)

    t = IndexedTSP(times=data['TIME'].dt.to_pydatetime(),
                     values=data.drop("TIME", axis=1).values)

    return t


def read_classic(filepath: str, init_file: "Optional[str]"=None) -> TSP:
    """Read output from CLASSIC land surface model

    Depth values, if provided, represent the midpoint of the model cells.

    Parameters
    ----------
    filepath : str
        Path to an output file
    init_file : str
        Path to a classic init file. If provided, depth values will be calculated. Otherwise an :py:class:`~tsp.core.IndexedTSP` is returned
    
    Returns
    -------
    TSP
        An IndexedTSP. Use :py:meth:`~tsp.core.IndexedTSP.set_depths` to provide depth information if init_file is not provided.
    """
    try:
        nc
    except NameError:
        warnings.warn("netCDF4 library must be installed.")

    # tbaracc_d / tbaracc_m / tbaracc_y
    with nc.Dataset(filepath, 'r') as ncdf:
        lat = ncdf['lat'][:]
        lon = ncdf['lon'][:]
        temp = ncdf['tsl'][:]  # t, z
        
        try:
            time = nc.num2date(ncdf['time'][:], ncdf['time'].units, ncdf['time'].calendar,
                            only_use_cftime_datetimes=False,
                            only_use_python_datetimes=True)
        except ValueError:
            cf_time = nc.num2date(ncdf['time'][:], ncdf['time'].units, ncdf['time'].calendar)
            time = np.array([datetime.datetime.fromisoformat(t.isoformat()) for t in cf_time])
    
    if init_file:
        with nc.Dataset(init_file, 'r') as init:
            delz = init["DELZ"][:]
        depths = np.round(np.cumsum(delz) - np.multiply(delz, 0.5), 7)  # delz precision is lower so we get some very small offsets

    if len(lat) > 1:
        warnings.warn("Multiple points in file. Returning the first one found.")
        # TODO: return Ensemble if multiple points
        lat = lat[0]
        lon = lon[0]
        temp = temp[:,:,0,0]
    else:
        temp = temp[:,:,0,0]

    t = IndexedTSP(times=time, values=temp, latitude=lat, longitude=lon)
    
    if init_file:
        t.set_depths(depths)

    return t
