# exploratory: T-learner for visit, Qini curves, policy values on the held-out half
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingClassifier

from .effects import COVARIATES

ARMS = ["control", "mens", "womens"]
P_ARM = 1 / 3  # known assignment prob
Z = norm.ppf(0.975)


def split(frame, seed=2008):
    # half of each arm goes to training
    rng = np.random.default_rng(seed)
    arm = frame["arm"].to_numpy()
    train = np.zeros(len(frame), dtype=bool)
    for a in ARMS:
        idx = np.flatnonzero(arm == a)
        train[rng.choice(idx, size=len(idx) // 2, replace=False)] = True
    return train


def fit_t_learner(train, seed=2008):
    models = {}
    for a in ARMS:
        d = train[train["arm"] == a]
        models[a] = HistGradientBoostingClassifier(random_state=seed).fit(d[COVARIATES], d["visit"])
    return models


def predict_uplift(models, frame):
    p = {a: m.predict_proba(frame[COVARIATES])[:, 1] for a, m in models.items()}
    return pd.DataFrame({"uplift_mens": p["mens"] - p["control"],
                         "uplift_womens": p["womens"] - p["control"]}, index=frame.index)


def qini(frame, score, arm, n_points=101):
    keep = frame["arm"].isin([arm, "control"]).to_numpy()
    s = np.asarray(score)[keep]
    order = np.argsort(-s, kind="stable")
    t = (frame["arm"].to_numpy()[keep] == arm)[order]
    y = frame["visit"].to_numpy(float)[keep][order]
    nt, nc = np.cumsum(t), np.cumsum(~t)
    yt, yc = np.cumsum(y * t), np.cumsum(y * ~t)
    # incremental visits Y_t - Y_c * N_t / N_c, per customer in the pair
    ratio = np.divide(nt, nc, out=np.zeros(len(nt)), where=nc > 0)
    q = (yt - yc * ratio) / len(y)
    frac = np.arange(1, len(y) + 1) / len(y)
    grid = np.linspace(0, 1, n_points)
    curve = np.interp(grid, np.r_[0.0, frac], np.r_[0.0, q])
    coef = np.trapezoid(curve - grid * curve[-1], grid)
    return pd.DataFrame({"email": arm, "fraction": grid, "qini": curve}), coef


def targeting_rule(uplift):
    best = np.where(uplift["uplift_mens"] >= uplift["uplift_womens"], "mens", "womens")
    none = np.maximum(uplift["uplift_mens"], uplift["uplift_womens"]) < 0
    return np.where(none, "control", best)


def policy_values(frame, uplift):
    arm = frame["arm"].to_numpy()
    y = frame["visit"].to_numpy(float)
    n = len(y)
    target = targeting_rule(uplift)
    policies = {
        "targeting": target,
        "mens_to_all": np.full(n, "mens"),
        "womens_to_all": np.full(n, "womens"),
        "no_email": np.full(n, "control"),
    }
    terms = {k: (arm == v) * y / P_ARM for k, v in policies.items()}  # IPW
    rows = [{"policy": k, "value": t.mean(), "se": t.std(ddof=1) / np.sqrt(n)} for k, t in terms.items()]
    d = terms["targeting"] - terms["mens_to_all"]
    rows.append({"policy": "targeting minus mens_to_all", "value": d.mean(),
                 "se": d.std(ddof=1) / np.sqrt(n)})
    out = pd.DataFrame(rows)
    out["ci_low"] = out["value"] - Z * out["se"]
    out["ci_high"] = out["value"] + Z * out["se"]
    shares = pd.Series(target).value_counts(normalize=True).rename_axis("sent").reset_index(name="share")
    return out, shares
