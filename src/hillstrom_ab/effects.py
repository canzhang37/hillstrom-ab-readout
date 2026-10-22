# between-arm effects: unadjusted, CUPED, Lin; bootstrap check; decision rule
# python -m hillstrom_ab.effects data/hillstrom.csv results/effects
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from .metrics import arm_metrics, connect, query

COMPARISONS = [("mens", "control"), ("womens", "control"), ("mens", "womens")]
METRICS = {
    "visit_rate": "se_visit_rate",
    "conversion_rate": "se_conversion_rate",
    "spend_per_customer": "se_spend_per_customer",
    "spend_per_visitor": "se_spend_per_visitor",
}
OUTCOMES = {"visit_rate": "visit", "conversion_rate": "conversion", "spend_per_customer": "spend"}
COVARIATES = [
    "recency", "history", "mens", "womens", "newbie",
    "zip_urban", "zip_rural", "channel_web", "channel_multichannel",
    "hseg_2", "hseg_3", "hseg_4", "hseg_5", "hseg_6", "hseg_7",
]
Z = norm.ppf(0.975)


def holm(p):
    p = np.asarray(p, dtype=float)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(np.argsort(p)):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = running
    return adj


def _inference(df):
    df["ci_low"] = df["estimate"] - Z * df["se"]
    df["ci_high"] = df["estimate"] + Z * df["se"]
    df["p_value"] = 2 * norm.sf(np.abs(df["estimate"] / df["se"]))
    return df


def unadjusted(m):
    m = m.set_index("arm")
    rows = []
    for metric, se_col in METRICS.items():
        for a, b in COMPARISONS:
            ma, mb = m.loc[a, metric], m.loc[b, metric]
            sa, sb = m.loc[a, se_col], m.loc[b, se_col]
            se_lift = np.sqrt(sa**2 / mb**2 + ma**2 * sb**2 / mb**4)  # delta method
            rows.append({
                "metric": metric, "comparison": f"{a} vs {b}",
                "estimate": ma - mb, "se": np.hypot(sa, sb),
                "lift": ma / mb - 1, "lift_low": ma / mb - 1 - Z * se_lift,
                "lift_high": ma / mb - 1 + Z * se_lift,
            })
    out = _inference(pd.DataFrame(rows))
    out["family"] = np.where(out["metric"] == "visit_rate", "primary", "secondary")
    out["p_holm"] = out.groupby("metric")["p_value"].transform(holm)
    return out


def _pair(frame, a, b):
    d = frame[frame["arm"].isin([a, b])]
    return d, (d["arm"] == a).to_numpy()


def _neyman_se(y, t):
    return np.sqrt(y[t].var(ddof=1) / t.sum() + y[~t].var(ddof=1) / (~t).sum())


def ols_hc2(X, y, cov=False):
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    e = y - X @ beta
    h = np.einsum("ij,jk,ik->i", X, xtx_inv, X)  # leverages
    meat = (X * (e**2 / (1 - h))[:, None]).T @ X
    V = xtx_inv @ meat @ xtx_inv
    return (beta, V) if cov else (beta, np.sqrt(np.diag(V)))


def cuped(frame, outcome, covariate="history"):
    rows = []
    for a, b in COMPARISONS:
        d, t = _pair(frame, a, b)
        y = d[outcome].to_numpy(float)
        x = d[covariate].to_numpy(float)
        x = x - x.mean()
        theta = np.cov(y, x)[0, 1] / x.var(ddof=1)
        yc = y - theta * x
        se = _neyman_se(yc, t)
        rows.append({"comparison": f"{a} vs {b}", "estimate": yc[t].mean() - yc[~t].mean(),
                     "se": se, "se_unadjusted": _neyman_se(y, t), "theta": theta})
    return pd.DataFrame(rows)


def lin_adjust(frame, outcome, covariates=COVARIATES):
    rows = []
    for a, b in COMPARISONS:
        d, t = _pair(frame, a, b)
        y = d[outcome].to_numpy(float)
        xc = d[covariates].to_numpy(float)
        xc = xc - xc.mean(axis=0)
        tf = t.astype(float)
        X = np.column_stack([np.ones(len(y)), tf, xc, tf[:, None] * xc])
        beta, se = ols_hc2(X, y)
        rows.append({"comparison": f"{a} vs {b}", "estimate": beta[1], "se": se[1],
                     "se_unadjusted": _neyman_se(y, t)})
    return pd.DataFrame(rows)


def adjusted(frame):
    parts = []
    for metric, outcome in OUTCOMES.items():
        for method, fn in [("cuped", cuped), ("lin", lin_adjust)]:
            parts.append(fn(frame, outcome).assign(metric=metric, method=method))
    out = _inference(pd.concat(parts, ignore_index=True))
    out["variance_reduction"] = 1 - (out["se"] / out["se_unadjusted"]) ** 2
    cols = ["metric", "method", "comparison", "estimate", "se", "ci_low", "ci_high",
            "p_value", "se_unadjusted", "variance_reduction", "theta"]
    return out[cols]


# spend per visitor: resample within each arm, compare with the delta SEs
def ratio_bootstrap(frame, m, n_boot=2000, seed=2008, chunk=100):
    rng = np.random.default_rng(seed)
    m = m.set_index("arm")
    draws = {}
    for arm in ["control", "mens", "womens"]:
        d = frame[frame["arm"] == arm]
        s, v = d["spend"].to_numpy(float), d["visit"].to_numpy(float)
        r = np.empty(n_boot)
        for start in range(0, n_boot, chunk):
            idx = rng.integers(0, len(s), size=(min(chunk, n_boot - start), len(s)))
            r[start:start + len(idx)] = s[idx].sum(axis=1) / v[idx].sum(axis=1)
        draws[arm] = r
    rows = []
    for arm, r in draws.items():
        rows.append({"target": arm, "estimate": m.loc[arm, "spend_per_visitor"],
                     "se_delta": m.loc[arm, "se_spend_per_visitor"], "se_boot": r.std(ddof=1),
                     "pct_low": np.quantile(r, 0.025), "pct_high": np.quantile(r, 0.975)})
    for a, b in COMPARISONS:
        r = draws[a] - draws[b]
        rows.append({"target": f"{a} vs {b}",
                     "estimate": m.loc[a, "spend_per_visitor"] - m.loc[b, "spend_per_visitor"],
                     "se_delta": np.hypot(m.loc[a, "se_spend_per_visitor"],
                                          m.loc[b, "se_spend_per_visitor"]),
                     "se_boot": r.std(ddof=1),
                     "pct_low": np.quantile(r, 0.025), "pct_high": np.quantile(r, 0.975)})
    out = pd.DataFrame(rows)
    out["se_ratio"] = out["se_boot"] / out["se_delta"]
    return out


# decision rule from docs/design.md, on the unadjusted estimates
def decision(unadj):
    u = unadj.set_index(["metric", "comparison"])
    rows = []
    qualified = []
    for arm in ["mens", "womens"]:
        v = u.loc[("visit_rate", f"{arm} vs control")]
        s = u.loc[("spend_per_customer", f"{arm} vs control")]
        ok = bool(v["estimate"] > 0 and v["p_holm"] < 0.05 and s["estimate"] >= 0)
        rows.append({"step": f"{arm} qualifies", "result": ok})
        if ok:
            qualified.append(arm)
    mw = u.loc[("visit_rate", "mens vs womens")]
    separated = bool(mw["p_holm"] < 0.05)
    rows.append({"step": "visit test separates mens and womens", "result": separated})
    if len(qualified) == 2:
        if separated:
            choice = "mens" if mw["estimate"] > 0 else "womens"
        else:
            sp = u.loc[("spend_per_customer", "mens vs womens"), "estimate"]
            choice = "mens" if sp > 0 else "womens"
    else:
        choice = qualified[0] if qualified else "none"
    rows.append({"step": "send", "result": choice})
    return pd.DataFrame(rows)


def main(csv, out_dir, n_boot=2000):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    con = connect(csv)
    m = arm_metrics(con)
    frame = query(con, "analysis_frame")

    unadj = unadjusted(m)
    rule = decision(unadj)
    unadj.to_csv(out / "effects_unadjusted.csv", index=False)
    adjusted(frame).to_csv(out / "effects_adjusted.csv", index=False)
    ratio_bootstrap(frame, m, n_boot=n_boot).to_csv(out / "ratio_bootstrap.csv", index=False)
    rule.to_csv(out / "decision.csv", index=False)
    print(rule.to_string(index=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
