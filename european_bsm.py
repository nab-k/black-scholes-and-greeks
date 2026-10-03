"""
Black-Scholes-Merton closed-form pricing for European options.

Notation:
  S     : spot price of the underlying
  K     : strike price
  T     : time to expiry, in years
  r     : continuously-compounded risk-free rate (annualised)
  sigma : annualised volatility of the underlying
  q     : continuously-compounded dividend yield (annualised); 0 for
          non-dividend-paying underlyings
"""

import math
from scipy.stats import norm

VALID_TYPES = ("call", "put")


def _validate_inputs(S: float, K: float, T: float, r: float, sigma: float, q: float) -> None:
    if S <= 0:
        raise ValueError(f"spot price S must be positive, got {S}")
    if K <= 0:
        raise ValueError(f"strike K must be positive, got {K}")
    if T <= 0:
        raise ValueError(f"time to expiry T must be positive, got {T}")
    if sigma <= 0:
        raise ValueError(f"volatility sigma must be positive, got {sigma}")


def d1(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """First BSM auxiliary variable, d1."""
    _validate_inputs(S, K, T, r, sigma, q)
    return (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))


def d2(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """Second BSM auxiliary variable, d2 = d1 - sigma * sqrt(T)."""
    return d1(S, K, T, r, sigma, q) - sigma * math.sqrt(T)


def call_price(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """European call price under Black-Scholes-Merton."""
    D1 = d1(S, K, T, r, sigma, q)
    D2 = D1 - sigma * math.sqrt(T)
    return S * math.exp(-q * T) * norm.cdf(D1) - K * math.exp(-r * T) * norm.cdf(D2)


def put_price(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    """European put price under Black-Scholes-Merton."""
    D1 = d1(S, K, T, r, sigma, q)
    D2 = D1 - sigma * math.sqrt(T)
    return K * math.exp(-r * T) * norm.cdf(-D2) - S * math.exp(-q * T) * norm.cdf(-D1)


# entry point to calculate option price
def price(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call") -> float:
    """Single entry point dispatch to call_price or put_price by option_type."""
    option_type = option_type.lower()
    if option_type not in VALID_TYPES:
        raise ValueError(f"option_type must be one of {VALID_TYPES}, got {option_type!r}")
    return call_price(S, K, T, r, sigma, q) if option_type == "call" else put_price(S, K, T, r, sigma, q)


def put_call_parity_check(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, tol: float = 1e-8) -> bool:
    """Check: C - P == S*exp(-qT) - K*exp(-rT)."""
    c = call_price(S, K, T, r, sigma, q)
    p = put_price(S, K, T, r, sigma, q)
    lhs = c - p
    rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
    return abs(lhs - rhs) < tol
