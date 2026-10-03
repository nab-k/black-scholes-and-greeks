"""
Closed-form Black-Scholes-Merton Greeks: first-order (delta, gamma, vega,
theta, rho) and second-order (vanna, volga/vomma, charm).

All formulas share d1/d2 from european_bsm.py, so there is a single
source for the underlying math.

First-order Greeks:
  delta    : rate of change of option value w.r.t. underlying price
  gamma    : rate of change of delta w.r.t. underlying price (convexity risk)
  vega     : rate of change of option value w.r.t. volatility (per 1.00 vol)
  theta    : rate of change of option value w.r.t. time to expiration (annualised)
  rho      : rate of change of option value w.r.t. risk-free rate

Second-order Greeks:
  vanna    : rate of change of delta w.r.t. volatility (vol-spot correlation)
  volga    : rate of change of vega w.r.t. volatility (vol-of-vol risk)
  charm    : rate of change of delta w.r.t. time to expiration (theta on delta)
"""

import math
from scipy.stats import norm

from european_bsm import VALID_TYPES, d1 as _d1, d2 as _d2

_phi = norm.pdf 
_N = norm.cdf


def _check_type(option_type: str) -> str:
    option_type = option_type.lower()
    
    if option_type not in VALID_TYPES:
        raise ValueError(f"option_type must be one of {VALID_TYPES}, got {option_type!r}")
    return option_type


# first order greeks

def delta(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call") -> float:
    """dV/dS. Call delta in [0, 1]; put delta in [-1, 0]."""
    
    option_type = _check_type(option_type)
    D1 = _d1(S, K, T, r, sigma, q)
    
    if option_type == "call":
        return math.exp(-q * T) * _N(D1)
    return math.exp(-q * T) * (_N(D1) - 1.0)


def gamma(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """d^2V/dS^2. Identical for calls and puts; always positive."""
    D1 = _d1(S, K, T, r, sigma, q)
    return math.exp(-q * T) * _phi(D1) / (S * sigma * math.sqrt(T))


def vega(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """dV/d(sigma). Identical for calls and puts; always positive."""
    D1 = _d1(S, K, T, r, sigma, q)
    return S * math.exp(-q * T) * _phi(D1) * math.sqrt(T)


def theta(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call") -> float:
    """
    -d(V)/dT, i.e. rate of value change as calendar time passes and time
    to expiry T shrinks (same sign convention as charm). This is Hull's
    standard "theta": typically negative for a long option position.
    """
    option_type = _check_type(option_type)
    D1 = _d1(S, K, T, r, sigma, q)
    D2 = D1 - sigma * math.sqrt(T)
    
    decay_term = -(S * math.exp(-q * T) * _phi(D1) * sigma) / (2 * math.sqrt(T))
    
    if option_type == "call":
        return decay_term - r * K * math.exp(-r * T) * _N(D2) + q * S * math.exp(-q * T) * _N(D1)
    return decay_term + r * K * math.exp(-r * T) * _N(-D2) - q * S * math.exp(-q * T) * _N(-D1)


def rho(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call") -> float:
    """dV/dr."""
    option_type = _check_type(option_type)
    D2 = _d2(S, K, T, r, sigma, q)
    
    if option_type == "call":
        return K * T * math.exp(-r * T) * _N(D2)
    return -K * T * math.exp(-r * T) * _N(-D2)


# second order greeks

def vanna(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """
    d(delta)/d(sigma) == d(vega)/dS. Identical for calls and puts.
    Closed form: -e^{-qT} * phi(d1) * d2 / sigma.
    """
    D1 = _d1(S, K, T, r, sigma, q)
    D2 = D1 - sigma * math.sqrt(T)
    return -math.exp(-q * T) * _phi(D1) * D2 / sigma


def volga(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """
    d(vega)/d(sigma), a.k.a. vomma. Identical for calls and puts.
    Closed form: vega * d1 * d2 / sigma.
    """
    D1 = _d1(S, K, T, r, sigma, q)
    D2 = D1 - sigma * math.sqrt(T)
    v = vega(S, K, T, r, sigma, q)
    return v * D1 * D2 / sigma


def charm(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call") -> float:
    """
    -d(delta)/dT, i.e. how fast delta decays as calendar time passes
    (T here is time-to-expiry, so charm = -d(delta)/dT).
    """
    option_type = _check_type(option_type)
    D1 = _d1(S, K, T, r, sigma, q)
    common = math.exp(-q * T) * _phi(D1) * (D1 / (2 * T) - (r - q + 0.5 * sigma ** 2) / (sigma * math.sqrt(T)))
    
    if option_type == "call":
        return q * math.exp(-q * T) * _N(D1) + common
    return -q * math.exp(-q * T) * _N(-D1) + common


# all greeks combined

def all_greeks(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call") -> dict:
    """every Greek for one option, as a dict."""
    return {
        "delta": delta(S, K, T, r, sigma, q, option_type),
        "gamma": gamma(S, K, T, r, sigma, q),
        "vega": vega(S, K, T, r, sigma, q),
        "theta": theta(S, K, T, r, sigma, q, option_type),
        "rho": rho(S, K, T, r, sigma, q, option_type),
        "vanna": vanna(S, K, T, r, sigma, q),
        "volga": volga(S, K, T, r, sigma, q),
        "charm": charm(S, K, T, r, sigma, q, option_type)}
