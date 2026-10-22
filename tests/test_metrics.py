from pathlib import Path

import numpy as np
import pytest

from hillstrom_ab import arm_metrics, connect, query, srm

FIXTURE = Path(__file__).parent / "fixtures" / "mini.csv"


@pytest.fixture
def con():
    return connect(FIXTURE)


def test_arm_metrics(con):
    m = arm_metrics(con).set_index("arm")
    assert m.loc["control", "n"] == 2
    assert m.loc["control", "visit_rate"] == pytest.approx(0.5)
    assert m.loc["mens", "spend_per_customer"] == pytest.approx(20.0)
    assert m.loc["womens", "visit_rate"] == pytest.approx(2 / 3)
    assert m.loc["womens", "spend_per_visitor"] == pytest.approx(10.0)
    assert np.isnan(m.loc["control", "spend_per_converter"])


def test_delta_method_matches_gradient_form(con):
    raw = con.execute("SELECT spend, visit FROM customers WHERE arm = 'womens'").df()
    s = raw["spend"].to_numpy(float)
    v = raw["visit"].to_numpy(float)
    grad = np.array([1 / v.mean(), -s.mean() / v.mean() ** 2])
    expected = np.sqrt(grad @ np.cov(np.vstack([s, v])) @ grad / len(s))
    got = arm_metrics(con).set_index("arm").loc["womens", "se_spend_per_visitor"]
    assert got == pytest.approx(expected)


def test_srm(con):
    tab, stat, p = srm(con)
    assert list(tab["arm"]) == ["control", "mens", "womens"]
    assert list(tab["n"]) == [2, 2, 3]
    assert stat == pytest.approx(2 / 7)
    assert 0 < p < 1


def test_balance_smd(con):
    b = query(con, "balance").set_index(["covariate", "arm"])
    # mens arm: 2 of 2 bought mens items, control: 1 of 2
    assert b.loc[("mens", "mens"), "smd"] == pytest.approx(1.0)


def test_checks_pass_on_clean_rows(con):
    c = query(con, "data_checks").set_index("check_name")
    assert c.loc["n_rows", "value"] == 7
    assert c.drop("n_rows")["ok"].all()


def test_checks_flag_bad_rows(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text(FIXTURE.read_text()
                   + "3,1) $0 - $100,50.0,1,0,Urban,0,Web,Kids E-Mail,0,1,10.0\n")
    c = query(connect(bad), "data_checks").set_index("check_name")
    assert c.loc["unknown_arm", "value"] == 1
    assert c.loc["conversion_without_visit", "value"] == 1
