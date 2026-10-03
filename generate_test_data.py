"""
Script that generates expected option prices and Greeks for the tests 
using QuantLib, an industry-standard pricing library, as a check on 
our results.

It calculates results for 10 scenarios, testing both calls and puts. 
It also adds one textbook example. Results are saved to test_data.json.

You don't need to run this to use the tests but you can regenerate it 
yourself if you want:
    pip install QuantLib
    python generate_test_data.py
"""

import json
from pathlib import Path

import QuantLib as ql

DAY_COUNT = ql.Actual365Fixed()
CALENDAR = ql.NullCalendar()
TODAY = ql.Date(1, 1, 2024)


def days_to_T(days: int) -> float:
    """Exact year-fraction QuantLib will use internally for `days` days out."""
    return DAY_COUNT.yearFraction(TODAY, TODAY + days)


def quantlib_reference(S, K, days, r, sigma, q, option_type):
    ql.Settings.instance().evaluationDate = TODAY
    maturity = TODAY + days

    spot = ql.QuoteHandle(ql.SimpleQuote(S))
    rf_curve = ql.YieldTermStructureHandle(ql.FlatForward(TODAY, r, DAY_COUNT))
    div_curve = ql.YieldTermStructureHandle(ql.FlatForward(TODAY, q, DAY_COUNT))
    vol_curve = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(TODAY, CALENDAR, sigma, DAY_COUNT))
    process = ql.BlackScholesMertonProcess(spot, div_curve, rf_curve, vol_curve)

    opt_type = ql.Option.Call if option_type == "call" else ql.Option.Put
    payoff = ql.PlainVanillaPayoff(opt_type, K)
    exercise = ql.EuropeanExercise(maturity)
    option = ql.VanillaOption(payoff, exercise)
    option.setPricingEngine(ql.AnalyticEuropeanEngine(process))

    return {
        "price": option.NPV(),
        "delta": option.delta(),
        "gamma": option.gamma(),
        "vega": option.vega(),
        "theta": option.thetaPerDay() * 365,  # annualised, to match convention
        "rho": option.rho()}


# scenarios cover different expiry lengths, option prices, volatility, interest rates, and dividend yields
SCENARIOS = [
    (100.0, 100.0, 30, 0.03, 0.20, 0.00),
    (100.0, 100.0, 182, 0.03, 0.20, 0.00),
    (100.0, 100.0, 365, 0.03, 0.20, 0.00),
    (100.0, 110.0, 90, 0.03, 0.20, 0.00),   # OTM call / ITM put
    (100.0, 90.0, 90, 0.03, 0.20, 0.00),    # ITM call / OTM put
    (50.0, 55.0, 182, 0.05, 0.35, 0.00),    # higher vol, higher rate
    (100.0, 100.0, 182, 0.03, 0.20, 0.02),  # with dividend yield
    (100.0, 100.0, 730, 0.04, 0.15, 0.01),  # long-dated, lower vol
    (200.0, 180.0, 7, 0.02, 0.45, 0.00),    # short-dated, high vol
    (25.0, 30.0, 365, 0.03, 0.30, 0.00)]    # deep OTM call / deep ITM put

if __name__ == "__main__":
    rows = []
    
    for S, K, days, r, sigma, q in SCENARIOS:
        T = days_to_T(days)
        
        for option_type in ("call", "put"):
            ref = quantlib_reference(S, K, days, r, sigma, q, option_type)
            rows.append({
                "source": "QuantLib AnalyticEuropeanEngine",
                "S": S, "K": K, "days_to_expiry": days, "T": round(T, 10),
                "r": r, "sigma": sigma, "q": q, "option_type": option_type,
                "expected_price": ref["price"],
                "expected_delta": ref["delta"],
                "expected_gamma": ref["gamma"],
                "expected_vega": ref["vega"],
                "expected_theta": ref["theta"],
                "expected_rho": ref["rho"]})

    # add a textbook example with a fixed half-year expiry
    # this value is entered directly rather than calculated with QuantLib
    rows.append({
        "source": "Hull 'Options, Futures, and Other Derivatives' worked example (verify independently)",
        "S": 42.0, "K": 40.0, "days_to_expiry": None, "T": 0.5,
        "r": 0.10, "sigma": 0.20, "q": 0.0, "option_type": "call",
        "expected_price": 4.759422392871532,
        "expected_delta": None, "expected_gamma": None, "expected_vega": None,
        "expected_theta": None, "expected_rho": None})

    output_path = Path(__file__).resolve().parent / "test_data.json"
    output_path.write_text(json.dumps(rows, indent=2))

    print(f"Wrote {len(rows)} test cases to {output_path}")