from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hillstrom_ab import arm_metrics, connect
from hillstrom_ab.effects import (cuped, decision, holm, lin_adjust, ols_hc2,
                                  ratio_bootstrap, unadjusted)

FIXTURE = Path(__file__).parent / "fixtures" / "mini.csv"


def simulated_frame(n=3000, seed=1):
    rng = np.random.default_rng(seed)
    arm = rng.choice(["control", "mens", "womens"], size=n)
    x = rng.normal(size=n)
    effect = np.select([arm == "mens", arm == "womens"], [0.5, 0.2], 0.0)
    y = 2 * x + effect + rng.normal(size=n)
    visit = (rng.random(n) < 0.3 + 0.1 * (arm != "control")).astype(int)
    spend = visit * rng.gamma(2.0, 50.0, size=n)
    return pd.DataFrame({"arm": arm, "y": y, "history": x, "visit": visit, "spend": spend})


def test_holm_known_values():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])


def test_hc2_matches_unpooled_se_without_covariates():
    rng = np.random.default_rng(2)
    t = rng.random(500) < 0.4
    y = rng.normal(size=500) + 3 * t * rng.normal(size=500)
    X = np.column_stack([np.ones(500), t.astype(float)])
    beta, se = ols_hc2(X, y)
    neyman = np.sqrt(y[t].var(ddof=1) / t.sum() + y[~t].var(ddof=1) / (~t).sum())
    assert beta[1] == pytest.approx(y[t].mean() - y[~t].mean())
    assert se[1] == pytest.approx(neyman)


def test_adjustment_recovers_effect_and_cuts_variance():
    frame = simulated_frame()
    for res in (cuped(frame, "y"), lin_adjust(frame, "y", ["history"])):
        r = res.set_index("comparison")
        assert abs(r.loc["mens vs control", "estimate"] - 0.5) < 4 * r.loc["mens vs control", "se"]
        assert (1 - (r["se"] / r["se_unadjusted"]) ** 2).min() > 0.6


@pytest.mark.filterwarnings("ignore::RuntimeWarning")  # fixture control has no converters
def test_unadjusted_on_fixture():
    u = unadjusted(arm_metrics(connect(FIXTURE))).set_index(["metric", "comparison"])
    assert u.loc[("visit_rate", "womens vs control"), "estimate"] == pytest.approx(2 / 3 - 1 / 2)
    assert u.loc[("visit_rate", "womens vs control"), "lift"] == pytest.approx((2 / 3) / (1 / 2) - 1)


def test_ratio_bootstrap_agrees_with_delta():
    frame = simulated_frame(n=6000)
    g = frame.groupby("arm")
    n = g.size()
    mu_s, mu_v = g["spend"].mean(), g["visit"].mean()
    cov = g[["spend", "visit"]].cov().unstack()
    var = (cov[("spend", "spend")] / mu_v**2
           - 2 * mu_s * cov[("spend", "visit")] / mu_v**3
           + mu_s**2 * cov[("visit", "visit")] / mu_v**4) / n
    m = pd.DataFrame({"arm": n.index, "spend_per_visitor": (mu_s / mu_v).values,
                      "se_spend_per_visitor": np.sqrt(var).values})
    b = ratio_bootstrap(frame, m, n_boot=400)
    assert b["se_ratio"].between(0.85, 1.15).all()


def test_decision_rule():
    rows = []
    for metric, vals in {"visit_rate": (0.07, 0.04, 0.03), "spend_per_customer": (0.8, 0.4, 0.3)}.items():
        for comp, est in zip(["mens vs control", "womens vs control", "mens vs womens"], vals):
            rows.append({"metric": metric, "comparison": comp, "estimate": est, "p_holm": 0.001})
    rule = decision(pd.DataFrame(rows)).set_index("step")["result"]
    assert rule["send"] == "mens"
