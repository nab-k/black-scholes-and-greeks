'''
Performs data-driven regression tests against test_data.json
for calculated price and first order greeks.

Run with: pytest -v tester.py
'''

from pathlib import Path
import pytest
import json

import european_bsm as bsm
import greeks

# open test data
data_path = Path(__file__).resolve().parent / "test_data.json"
with data_path.open() as f:
    TEST_CASES = json.load(f)

PRICE_TOL = 1e-6
GREEK_TOL = 1e-6


# check BSM price calculation
@pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: f"{c['source'][:12]}_{c['option_type']}_S{c['S']}K{c['K']}")
def test_price_matches_reference(case):
    got = bsm.price(case["S"], case["K"], case["T"], case["r"], case["sigma"], case["q"], case["option_type"])
    assert got == pytest.approx(case["expected_price"], abs=PRICE_TOL)


# check first order greeks
@pytest.mark.parametrize("case", [c for c in TEST_CASES if c["expected_delta"] is not None],
                         ids=lambda c: f"{c['option_type']}_S{c['S']}K{c['K']}_d{c['days_to_expiry']}")
def test_greeks_match_reference(case):
    S, K, T, r, sigma, q, opt = case["S"], case["K"], case["T"], case["r"], case["sigma"], case["q"], case["option_type"]
    assert greeks.delta(S, K, T, r, sigma, q, opt) == pytest.approx(case["expected_delta"], abs=GREEK_TOL)
    assert greeks.gamma(S, K, T, r, sigma, q) == pytest.approx(case["expected_gamma"], abs=GREEK_TOL)
    assert greeks.vega(S, K, T, r, sigma, q) == pytest.approx(case["expected_vega"], abs=GREEK_TOL)
    assert greeks.theta(S, K, T, r, sigma, q, opt) == pytest.approx(case["expected_theta"], abs=GREEK_TOL)
    assert greeks.rho(S, K, T, r, sigma, q, opt) == pytest.approx(case["expected_rho"], abs=GREEK_TOL)