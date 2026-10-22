import numpy as np
import pandas as pd
import pytest

from hillstrom_ab.effects import COVARIATES, ols_hc2
from hillstrom_ab.subgroups import interaction_tests, subgroup_effects
from hillstrom_ab.uplift import policy_values, qini, split, targeting_rule


def simulated_frame(n=9000, interaction=0.0, seed=3):
    rng = np.random.default_rng(seed)
    f = pd.DataFrame({c: 0.0 for c in COVARIATES}, index=range(n))
    f["arm"] = rng.choice(["control", "mens", "womens"], size=n)
    f["newbie"] = (rng.random(n) < 0.5).astype(float)
    f["mens"] = (rng.random(n) < 0.6).astype(float)
    f["womens"] = np.where(f["mens"] == 1, (rng.random(n) < 0.2).astype(float), 1.0)
    u = rng.random(n)
    f["channel_web"] = (u < 0.45).astype(float)
    f["channel_multichannel"] = (u > 0.88).astype(float)
    lift = np.select([f["arm"] == "mens", f["arm"] == "womens"], [0.08, 0.04], 0.0)
    lift = lift + interaction * f["newbie"] * (f["arm"] != "control")
    f["visit"] = (rng.random(n) < 0.10 + lift).astype(int)
    return f


def test_hc2_cov_matches_se():
    rng = np.random.default_rng(4)
    X = np.column_stack([np.ones(300), rng.normal(size=300)])
    y = X @ [1.0, 2.0] + rng.normal(size=300)
    _, se = ols_hc2(X, y)
    _, V = ols_hc2(X, y, cov=True)
    assert np.sqrt(np.diag(V)) == pytest.approx(se)


def test_interaction_tests_df_and_power():
    t = interaction_tests(simulated_frame(interaction=0.15)).set_index("subgroup")
    assert list(t["df"]) == [4, 2, 4]
    assert t.loc["newbie", "p_value"] < 1e-6
    null = interaction_tests(simulated_frame(interaction=0.0)).set_index("subgroup")
    assert null.loc["newbie", "p_value"] > 0.001


def test_subgroup_effects_are_differences_in_means():
    f = simulated_frame()
    e = subgroup_effects(f).set_index(["subgroup", "level", "comparison"])
    d = f[f["newbie"] == 1]
    expected = d.loc[d["arm"] == "mens", "visit"].mean() - d.loc[d["arm"] == "control", "visit"].mean()
    assert e.loc[("newbie", "yes", "mens vs control"), "estimate"] == pytest.approx(expected)


def test_split_takes_half_of_each_arm():
    f = simulated_frame()
    train = split(f)
    share = pd.Series(train).groupby(f["arm"].to_numpy()).mean()
    assert share.between(0.49, 0.51).all()


def test_qini_ranks_an_informative_score_above_a_random_one():
    f = simulated_frame(interaction=0.15)
    rng = np.random.default_rng(5)
    _, good = qini(f, f["newbie"] + 0.01 * rng.random(len(f)), "mens")
    _, noise = qini(f, rng.random(len(f)), "mens")
    assert good > noise


def test_policy_values():
    f = simulated_frame()
    up = pd.DataFrame({"uplift_mens": np.ones(len(f)), "uplift_womens": np.zeros(len(f))})
    assert (targeting_rule(up) == "mens").all()
    values, _ = policy_values(f, up)
    v = values.set_index("policy")["value"]
    assert v["targeting minus mens_to_all"] == pytest.approx(0.0)
    n = len(f)
    mens = f["arm"] == "mens"
    assert v["mens_to_all"] == pytest.approx(f.loc[mens, "visit"].sum() / (n / 3))
