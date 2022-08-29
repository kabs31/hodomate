from __future__ import annotations

import pandas as pd
import re
import numpy as np
import functools
import warnings

try:
    import netCDF4 as nc

    try:
        from pfit.pfnet_standard import make_temperature_base
    except ModuleNotFoundError:
        warnings.warn("Missing pfit library. Some functionality will be limited.")

except ModuleNotFoundError:
    warnings.warn("Missing netCDF4 library. Some functionality will be limited.")

from typing import Union, Optional
from datetime import datetime

import tsp
from tsp.physics import analytical_fourier
from tsp.plots.static import trumpet_curve, colour_contour, time_series

if False:  # work-around for type hints error (F821 undefined name)
    import matplotlib


class TSP:
    """ A Time Series Profile (a collection of time series data at different depths)
    
    A TSP can also be:
    Thermal State of Permafrost
    Temperature du Sol en Profondeur
    Temperatures, Secondes, Profondeurs

    Parameters
    ----------
    times : list-like
        t-length array of datetime objects
    depths : list-like
        d-length array of depths
    values : numpy.ndarray
        array with shape (t,d) containing values at (t)emperatures and (d)epths
    longitude : float, optional
        Longitude at which data were collected
    latitude : float, optional
        Latitude at which data were collected
    site_id : str, optional
        Name of location at which data were collected
    metadata : dict
        Additional metadata
    """

    def __repr__(self) -> str:
        return repr(self.wide)

    def __str__(self) -> str:
        return str(self.wide)

    def __init__(self, times, depths, values, 
                 latitude: Optional[float]=None, 
                 longitude: Optional[float]=None,
                 site_id: Optional[str]=None,
                 metadata:dict={}):

        self._times = np.atleast_1d(times)
        self._depths = np.atleast_1d(depths)
        self._values = np.atleast_2d(values)
        self.__counts = np.ones_like(values) * ~np.isnan(values)
        self.metadata = metadata
        self.latitude = latitude
        self.longitude = longitude
        self.site_id = site_id

    @property
    @functools.lru_cache()
    def long(self) -> "pd.DataFrame":
        """ Return the data in a 'long' or 'tidy' format (one row per observation, one column per variable)

        Returns
        -------
        DataFrame
            Time series profile data with columns:
                - **time**: time
                - **depth**: depth 
                - **temperature_in_ground**: temperature
                - **count**: If data are aggregated, how many observations are used in the aggregation
        """
        values = self.wide.melt(id_vars='time',
                                var_name="depth",
                                value_name="temperature_in_ground")

        counts = self.counts.melt(id_vars='time',
                                  var_name="depth",
                                  value_name="counts")
                              
        values['count'] = counts['counts']

        return values

    @property
    @functools.lru_cache()
    def wide(self) -> "pd.DataFrame":
        """ Return the data in a 'wide' format (one depth per column)

        Returns
        -------
        DataFrame
            Time series profile data
        """
        tabular = pd.DataFrame(self._values)
        tabular.columns = self._depths
        tabular.index = self._times
        tabular.insert(0, "time", self._times)

        return tabular

    @property
    @functools.lru_cache()
    def counts(self) -> "pd.DataFrame":
        """ The number of observations for an average at a particular depth or time.

        For pure observational data, the observation count will always be '1'. When data are aggregated, 
        (e.g. using :py:meth:`~tsp.core.TSP.monthly` or :py:meth:`~tsp.core.TSP.daily`) these numbers
        will be greater than 1.

        Returns
        -------
        DataFrame
            Number of observations 
        """
        tabular = pd.DataFrame(self.__counts, dtype=int)
        tabular.columns = self._depths
        tabular.index = self._times
        tabular.insert(0, "time", self._times)

        return tabular

    @counts.setter
    def counts(self, value):
        raise ValueError(f"You can't assign {value} to this variable (no assignment allowed).")

    def __nly(self, 
              freq_fmt:str,
              min_count:int,
              max_gap:int,
              min_span:int) -> "TSP":
        """
        Temporal aggregation by grouping according to a string-ified time

        Parameters
        ----------
        freq_fmt : str
            Python date format string  used to aggregate and recover time 
        
        """
        data = self.long
        index = data['time'].dt.strftime(freq_fmt)
        grouped = data.groupby([index, "depth"])

        # calculate data
        agg_avg = grouped['temperature_in_ground'].mean().unstack()
        agg_counts = grouped['count'].sum().unstack() 
        times = pd.to_datetime(agg_avg.index, format=freq_fmt)
        
        # apply masks
        count_mask = _observation_count_mask(counts=agg_counts,
                                             min_count=min_count)
        interval_mask = _temporal_gap_mask(grouped, max_gap, min_span)
        mask = np.logical_or(count_mask, interval_mask)
        values = np.ma.masked_array(agg_avg, mask=mask)

        # make TSP
        t = TSP(times=times, depths=self.depths, values=values)
        t.__counts = agg_counts
        
        return t

    def monthly(self,
                min_count:int=24,
                max_gap:int=3600*24*8,
                min_span:int=3600*24*21) -> "TSP":
        """ Monthly averages, possibly with some months unavailable (NaN) if there is insufficient data

        Parameters
        ----------
        min_count : int
            Minimum number of observations in a month to be considered a valid average, defaults to 24
        max_gap : int
            Maximum gap (in seconds) between data points to be considered a valid average, defaults to 691200 (8 days)
        min_span : int
            Minimum total data range (in seconds) to be consiered a valid average, defaults to 1814400 (21 days)
            
        Returns
        -------
        TSP
            A TSP object with data aggregated to monthly averages
        """
        t = self.__nly(freq_fmt="%Y%m", 
                         min_count=min_count,
                         max_gap=max_gap,
                         min_span=min_span)
        
        return t

    def daily(self, 
              min_count:int=8,
              max_gap:int=3600*3,
              min_span:int=3600*18) -> "TSP":
        """ Daily averages, possibly with some days unavailable (NaN) if there is insufficient data

        Parameters
        ----------
        min_count : int
            Minimum number of observations in a day to be considered a valid average, defaults to 8
        max_gap : int
            Maximum gap (in seconds) between data points to be considered a valid average, defaults to 10800 (3 hours)
        min_span : int
            Minimum total data range (in seconds) to be consiered a valid average, defaults to 64800 (18 hours)
        
        Returns
        -------
        TSP
            A TSP object with data aggregated to daily averages
        """
        t = self.__nly(freq_fmt="%Y%m%d", 
                         min_count=min_count,
                         max_gap=max_gap,
                         min_span=min_span)
        
        return t

    def yearly(self,
               min_count:int=270,
               max_gap:int=3600*24*35,
               min_span:int=3600*24*330) -> "TSP":
        """ Yearly averages, possibly with some years unavailable (NaN) if there is insufficient data

        Parameters
        ----------
        min_count : int
            Minimum number of observations in a month to be considered a valid average, defaults to 270
        max_gap : int
            Maximum gap (in seconds) between data points to be considered a valid average, defaults to 3024000 (35 days)
        min_span : int
            Minimum total data range (in seconds) to be consiered a valid average, defaults to 28512000 (330 days)
        
        Returns
        -------
        TSP
            A TSP object with data aggregated to yearly averages
        """
        t = self.__nly(freq_fmt="%Y", 
                         min_count=min_count,
                         max_gap=max_gap,
                         min_span=min_span)
        
        return t

    @property
    def depths(self) -> "np.ndarray":
        """ Return the depth values in the profile 

        Returns
        -------
        numpy.ndarray
            The depths in the profile
        """
        return self._depths

    @depths.setter
    def depths(self, value):
        depths = np.atleast_1d(value)
        
        if not len(depths) == len(self._depths):
            raise ValueError(f"List of depths must have length of {len(self._depths)}.")

        self._depths = depths

    @property
    def times(self):
        """ Return the timestamps in the time series 

        Returns
        -------
        numpy.ndarray
            The timestamps in the time series
        """
        return self._times

    @property
    def values(self):
        return self._values

    def to_gtnp(self, filename: str) -> None:
        """ Write the data in GTN-P format
        
        Parameters
        ----------
        filename : str
            Path to the file to write to
        """
        df = self.wide.rename(columns={'time': 'Date/Depth'})
        df['Date/Depth'] = df['Date/Depth'].dt.strftime("%Y-%m-%d %H:%M:%S")

        df.to_csv(filename, index=False, na_rep="-999")

    def to_ntgs(self, filename:str, project_name:str="", site_id:"Optional[str]" = None, latitude:"Optional[float]"=None, longitude:"Optional[float]"=None) -> None:
        """ Write the data in NTGS template format 

        Parameters
        ----------
        filename : str
            Path to the file to write to
        project_name : str, optional
            The project name, by default ""
        site_id : str, optional
            The name of the site , by default None
        latitude : float, optional
            WGS84 latitude at which the observations were recorded, by default None
        longitude : float, optional
            WGS84 longitude at which the observations were recorded, by default None
        """
        if latitude is None:
            latitude = self.latitude if self.latitude is not None else ""

        if longitude is None:
                longitude = self.longitude if self.longitude is not None else ""

        if site_id is None:
                site_id = self.site_id if self.site_id is not None else ""
        data = self.values
        
        df = pd.DataFrame()
        df["project_name"] = project_name
        df["site_id"] = site_id
        df["latitude"] = latitude
        df["longitude"] = longitude
        df["date_YYYY-MM-DD"] = pd.Series(self.times).dt.strftime(r"%Y-%m-%d")
        df["time_HH:MM:SS"] = pd.Series(self.times).dt.strftime(r"%H:%M:%S")
        
        headers = [str(d) + "_m" for d in self.depths]
        
        for i, h in enumerate(headers):
            df[h] = data[:, i]

        df.to_csv(filename, index=False)

    def to_netcdf(self, file: str) -> None:
        """  Write the data as a netcdf"""
        try:
            ncf = make_temperature_base(file, len(self.depths))
        except NameError:
            warnings.warn("Missing required packages. Try installing with `pip install tsp[nc]`")
            return
        
        with nc.Dataset(ncf, 'a') as ncd:
            pytime = pd.to_datetime(self.times).to_pydatetime()

            ncd['depth_below_ground_surface'][:] = self.depths

            
            ncd['time'][:] = nc.date2num(pytime, ncd['time'].units, ncd['time'].calendar)
            ncd['ground_temperature'][:] = self.values
            
            if self.latitude:
                ncd['latitude'][:] = self.latitude
            if self.longitude:
                ncd['longitude'][:] = self.longitude
            if self.site_id:
                ncd['site_name'] = self.site_id
            
            for key, value in self.metadata:
                try:
                    ncd.setncattr(key, value)
                except Exception:
                    warnings.warn(f"Could not set metadata item: {key}")

    def to_json(self, file: str) -> None:
        """ Write the data to a serialized json file """
        with open(file, 'w') as f:
            f.write(self._to_json())

    def _to_json(self) -> str:
        return self.wide.to_json()

    @classmethod
    def from_json(cls, json_file) -> "TSP":
        """ Read data from a json file 

        Parameters
        ----------
        json_file : str
            Path to a json file from which to read
        """
        df = pd.read_json(json_file)
        depth_pattern = r"^(-?[0-9\.]+)$"

        times = pd.to_datetime(df['time']).values
        depths = [re.search(depth_pattern, c).group(1) for c in df.columns if tsp._is_depth_column(c, depth_pattern)]
        values = df.loc[:, depths].to_numpy()
        
        t = cls(times=times, depths=depths, values=values)
        
        return t

    @classmethod
    def synthetic(cls, depths: "np.ndarray", start="2000-01-01", end="2003-01-01",
                  Q:"Optional[float]"=0.2, 
                  c:"Optional[float]"=1.6e6,
                  k:"Optional[float]"=2.5,
                  A:"Optional[float]"=6,
                  MAGST:"Optional[float]"=-0.5) -> "TSP":
        """
        Create a 'synthetic' temperature time series using the analytical solution to the heat conduction equation.
        Suitable for testing 
        
        Parameters
        ----------   
        depths : np.ndarray
            array of depths in m
        start : str
            array of times in seconds
        Q : Optional[float], optional
            Ground heat flux [W m-2], by default 0.2
        c : Optional[float], optional
            heat capacity [J m-3 K-1], by default 1.6e6
        k : Optional[float], optional
            thermal conductivity [W m-1 K-1], by default 2.5
        A : Optional[float], optional
            Amplitude of temperature fluctuation [C], by default 6
        MAGST : Optional[float], optional
            Mean annual ground surface temperature [C], by default -0.5
        
        Returns 
        -------
        TSP 
            A timeseries profile (TSP) object
        """
        times = pd.date_range(start=start, end=end).to_pydatetime()
        t_sec = np.array([(t-times[0]).total_seconds() for t in times])
        
        values = analytical_fourier(depths=depths, times=t_sec, Q=Q, c=c, k=k, A=A, MAGST=MAGST)
        
        this = cls(depths=depths, times=times, values=values)
        
        return this

    def plot_trumpet(self, year: Optional[int]=None, begin: Optional[datetime]=None, end: Optional[datetime]=None, **kwargs) -> 'matplotlib.figure.Figure':
        """ Create a trumpet plot from the data
        
        Parameters
        ----------
        year : int, optional
            Which year to plot
        begin : datetime, optional
            If 'end' also provided, the earliest measurement to include in the averaging for the plot
        end : datetime, optional
            If 'begin' also provided, the latest measurement to include in the averaging for the plot
        **kwargs : dict, optional
            Extra arguments to the plotting function: refer to the documentation for :func:`~tsp.plots.static.trumpet_curve` for a
            list of all possible arguments.

        Returns
        -------
        Figure
            a matplotlib `Figure` object
        """
        df = self.long.dropna()
        grouped = df.groupby('depth')
        if year is not None:
            df = df[df['time'].dt.year == year]
        
        elif begin is not None or end is not None:
            pass
        
        else:
            raise ValueError("One of 'year', 'begin', 'end' must be provided.")

        max_t = grouped.max().get('temperature_in_ground').values
        min_t = grouped.min().get('temperature_in_ground').values
        mean_t = grouped.mean().get('temperature_in_ground').values
        depth = np.array([d for d in grouped.groups.keys()])

        fig = trumpet_curve(depth=depth, t_max=max_t, t_min=min_t, t_mean=mean_t, **kwargs)
        fig.show()

        return fig
    
    def plot_contour(self, **kwargs) -> 'matplotlib.figure.Figure':
        """ Create a contour plot
        
        Parameters
        ----------
        **kwargs : dict, optional
            Extra arguments to the plotting function: refer to the documentation for :func:`~tsp.plots.static.colour_contour` for a
            list of all possible arguments.

        Returns
        -------
        Figure
            matplotlib `Figure` object
        """
        fig = colour_contour(depths=self.depths, times=self.times, values=self._values, **kwargs)
        fig.show()

        return fig

    def plot_timeseries(self, depths: list=[], **kwargs) -> 'matplotlib.figure.Figure':
        """Create a time series T(t) plot 

        Parameters
        ----------
        depths : list, optional
            If non-empty, restricts the depths to include in the plot, by default []
        **kwargs : dict, optional
            Extra arguments to the plotting function: refer to the documentation for :func:`~tsp.plots.static.time_series` for a
            list of all possible arguments.

        Returns
        -------
        Figure
            matplotlib `Figure` object
        """
        if depths == []:
            depths = self.depths
        
        d_mask = np.isin(self.depths, depths)
        
        fig = time_series(self.depths[d_mask], self.times, self.values[:, d_mask], **kwargs)
        
        fig.show()
        
        return fig


class AggregatedTSP(TSP):
    """ A Time Series Profile that uses indices (1,2,3,...) instead of depth values. 
    
    Used in situations when depths are unknown (such as when reading datlogger exports
    that don't have depth measurements.)
    
    Parameters
    ----------
    times : list-like
        t-length array of datetime objects
    values : numpy.ndarray
        array with shape (t,d) containing values at (t)emperatures and (d)epths
    **kwargs : dict
        Extra arguments to parent class: refer to :py:class:`tsp.core.TSP` documentation for a
        list of all possible arguments.
    """


class IndexedTSP(TSP):
    """ A Time Series Profile that uses indices (1,2,3,...) instead of depth values. 
    
    Used in situations when depths are unknown (such as when reading datlogger exports
    that don't have depth measurements.)
    
    Parameters
    ----------
    times : list-like
        t-length array of datetime objects
    values : numpy.ndarray
        array with shape (t,d) containing values at (t)emperatures and (d)epths
    **kwargs : dict
        Extra arguments to parent class: refer to :py:class:`~tsp.core.TSP` documentation for a
        list of all possible arguments.
    """

    def __init__(self, times, values, **kwargs):
        depths = np.arange(0, values.shape[1]) + 1
        super().__init__(times=times, depths=depths, values=values, **kwargs)

    @property
    def depths(self) -> np.ndarray:
        """Depth indices 

        Returns
        -------
        numpy.ndarray
            An array of depth indices
        """
        warnings.warn("This TSP uses indices (1,2,3,...) instad of depths. Use set_depths() to use measured depths.")
        return self._depths

    @depths.setter
    def depths(self, value):
        TSP.depths.__set__(self, value)

    def set_depths(self, depths: np.ndarray):
        """Assign depth values to depth indices. Change the object to a :py:class:`~tsp.core.TSP`

        Parameters
        ----------
        depths : np.ndarray
            An array or list of depth values equal in lenth to the depth indices
        """
        self.depths = depths
        self.__class__ = TSP

def _temporal_gap_mask(grouped: "pd.core.groupby.DataFrameGroupBy", max_gap: int, min_span: int) -> np.ndarray:
    """ Mask out observational groups in which there is more than a certain size temporal gap

    Controls for gaps in the data within an aggregation group (using max_gap) and missing data at the beginning
    or end of the aggregation group (using min_span).
    
    Parameters
    ----------
    grouped : pandas.core.groupby.DataFrameGroupBy
        groupby  with 'time' and 'depth' columns
    max_gap : int
        maximum gap in seconds to tolerate between observations in a group
    min_span : int
        minimum data range (beginning to end) in seconds. 

    Returns
    -------
    numpy.ndarray
        boolean array with ``True`` where measurement spacing or range in group does not satisfy tolerances
    """    
    max_diff = grouped.time.apply(np.diff).apply(lambda x: np.max(x, initial=0)).apply(lambda x: x.total_seconds())
    max_diff = max_diff.unstack().to_numpy()
    diff_mask = np.where((max_diff == 0) | (max_diff >= max_gap), True, False)
    
    total_span = grouped.time.apply(np.ptp).apply(lambda x: x.total_seconds()).unstack().to_numpy()
    span_mask = np.where(total_span < min_span, True, False)

    mask = diff_mask * span_mask

    return mask

def _observation_count_mask(counts: np.ndarray, min_count:int) -> np.ndarray:
    """ Create a mask array for an
    
    Parameters
    ----------
    counts : numpy.ndarray
        Array of how many data points are in aggregation
    min_count : int
        Minimum number of data points for aggregation to be 'valid'

    Returns
    -------
    np.ndarray
        a mask, True where data should be masked
    """
    valid = counts < min_count
    return valid