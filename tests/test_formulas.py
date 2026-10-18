from datetime import date

import pytest

from pulse import derive as d
from pulse.events import decayed


def test_real_rates_sep_2026_example():
    assert d.real_rate(19.0, 13.9) == pytest.approx(5.1)
    assert d.real_rate(19.0, 14.1) == pytest.approx(4.9)
    assert d.real_rate(19.0, 16.6) == pytest.approx(2.4)
    assert d.real_rate(20.0, 13.9) == pytest.approx(6.1)


def test_gold_implied_fx_sanity_16_oct_2026():
    # spec §5: 21K EGP 6,245 and XAU $4,157.85 → implied ≈ 53.4 vs market ≈ 53.45 → gap ≈ 0%
    implied = d.gold_implied_fx(6245, 4157.85, "21k")
    assert implied == pytest.approx(53.39, abs=0.05)
    assert abs(d.gap_pct(implied, 53.45)) < 0.2


def test_gold_24k_purity_and_premium():
    assert d.gold_implied_fx(7166, 4165.42, "24k") == pytest.approx(7166 / (4165.42 / 31.1035 * 0.999))
    prem = d.local_premium_egp(6245, 4157.85, 53.45)
    assert prem == pytest.approx(6245 - 4157.85 / 31.1035 * 0.875 * 53.45)
    assert abs(prem) < 50  # inside the ±EGP 50/gram noise band on that date


def test_pmi_implied_gdp():
    assert d.pmi_implied_gdp(47.2) == pytest.approx(47.2 * 0.269 - 8.62)
    assert d.pmi_implied_gdp(50) == pytest.approx(4.83)


def test_ca_pressure_rule_of_thumb():
    assert d.ca_pressure_pct_gdp(10) == pytest.approx(0.3)
    assert d.ca_pressure_pct_gdp(34.86) == pytest.approx(1.0458)


def test_eda_signal_weights():
    assert d.eda_signal(10, 5, 0) == pytest.approx(7.5)
    assert d.eda_signal(0, 0, 10) == pytest.approx(1.0)
    assert d.cumulative_from_mom([1.0, 1.0]) == pytest.approx(2.01)


def test_carry():
    assert d.carry_ex_post(24.0, 2.0) == pytest.approx(4.0)
    assert d.carry_ex_ante(25.7, 0.5) == pytest.approx(25.2)


def test_realized_vol_flat_is_zero():
    assert d.realized_vol([50.0] * 21) == pytest.approx(0.0)


def test_decay_half_life():
    e = date(2026, 10, 1)
    assert decayed(4, 1, 30, e, e) == pytest.approx(4)
    assert decayed(4, 1, 30, e, date(2026, 10, 31)) == pytest.approx(2)
    assert decayed(4, -1, 30, e, date(2026, 11, 30)) == pytest.approx(-1)
    assert decayed(4, 1, 30, e, date(2026, 9, 1)) == 0  # future events never count
