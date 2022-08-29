import numpy as np
from typing import Optional


def analytical_fourier(depths: "np.ndarray", times: "np.ndarray",
              Q:"Optional[float]"=0.2, 
              c:"Optional[float]"=1.6e6,
              k:"Optional[float]"=2.5,
              A:"Optional[float]"=6,
              MAGST:"Optional[float]"=-0.5) -> "np.ndarray":
    """Create sinusoidal synthetic data for examples and testing

    Parameters
    ----------
    depths : np.ndarray
        array of depths in m
    times : np.ndarray
        array of times in seconds
    Q : Optional[float], optional
        Geothermal heat flux [W m-2], by default 0.2
    c : Optional[float], optional
        heat capacity [J m-3 K-1], by default 1.6e6
    k : Optional[float], optional
       thermal conductivity [W m-1 K-1], by default 2.5
    A : Optional[float], optional
        Amplitude of temperature fluctuation [C], by default 6
    MAGST : Optional[float], optional
        mean annual ground surface temperature [C], by default -0.5

    Returns
    -------
    TSP
        _description_
    """
    Q = 0.2  # [W m-2]
    c = 1.6e6  # J m-3 K-1
    k = 2.5  # [W m-1 K-1]
    tau = 31536000  # [s]
    w = 2 * np.pi / tau  # []
    A = 6  # [C]
    MAGST = -0.5  # [C]
    alpha = k / c

    initial = initial_analytic(MAGST, Q, k, depths) 
    initial = np.repeat(initial[np.newaxis, :], len(times), axis=0) 
    
    T = initial + delta_analytic(A0=A, z=depths, w=w, alpha=alpha, t=times)
    
    return T


def initial_analytic(MAGST:float, Q:float, k:float, z:np.ndarray) -> np.ndarray:
    """ Initial conditions for steady-state analytical temperature oscillation
    
    Parameters
    ----------
    MAGST : float
        mean annual ground surface temperature [C]
    Q : float
        Geothermal heat flux [W m-2]
    k : float
        thermal conductivity [W m-1 K-1]
    z : np.ndarray
        ordered list of depths [m]

    Returns
    -------
    np.ndarray
        initial temperature conditions [C]

    """
    z = np.atleast_1d(z)
    initial = MAGST - (Q / k) * -np.abs(sorted(z))
   
    return initial


def delta_analytic(A0:float, z:np.ndarray, w:float, alpha:float, t:np.ndarray) -> np.ndarray:
    """ Analytical solution to heat conduction equation 
    
    Parameters
    ----------
    A0 : float
        Amplitude of temperature fluctuation [C]
    z : np.ndarray
        depth [m]
    w : float
        period of temperature fluctuation [s]
    kappa : float
        thermal diffusivity [W m-1 K-1]
    t : np.ndarray
        time in seconds [s]

    Returns
    -------
    np.ndarray 
    """
    nz = len(z)
    nt = len(t)
    z = np.repeat(np.atleast_1d(z)[np.newaxis, :], nt, axis=0)
    t = np.repeat(np.atleast_1d(t)[:, np.newaxis], nz, axis=1)
    S = np.sqrt(w / (2 * alpha))
    A = A0 * np.exp(-z * S)
    osc = np.cos(w * t - z * S)
    
    return A * osc
