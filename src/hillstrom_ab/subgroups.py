# pre-specified subgroups (visit only): interaction tests + effect per level
import numpy as np
import pandas as pd
from scipy.stats import chi2, norm

from .effects import holm, ols_hc2

EMAILS = ["mens", "womens"]
Z = norm.ppf(0.975)


def subgroup_levels(frame):
    buyer = np.select([(frame["mens"] == 1) & (frame["womens"] == 1), frame["mens"] == 1],
                      ["both", "mens_only"], "womens_only")
    channel = np.select([frame["channel_web"] == 1, frame["channel_multichannel"] == 1],
                        ["web", "multichannel"], "phone")
    return {
        "buyer_type": pd.Series(buyer, index=frame.index),
        "newbie": frame["newbie"].map({0.0: "no", 1.0: "yes"}),
        "channel": pd.Series(channel, index=frame.index),
    }


def interaction_tests(frame):
    y = frame["visit"].to_numpy(float)
    arm = frame["arm"].to_numpy()
    A = np.column_stack([(arm == a).astype(float) for a in EMAILS])
    rows = []
    for name, lev in subgroup_levels(frame).items():
        cats = sorted(lev.unique())
        L = np.column_stack([(lev == c).to_numpy(float) for c in cats[1:]])
        inter = np.column_stack([A[:, i] * L[:, j] for i in range(A.shape[1]) for j in range(L.shape[1])])
        X = np.column_stack([np.ones(len(y)), A, L, inter])
        beta, V = ols_hc2(X, y, cov=True)
        # joint Wald test on the arm x level terms (last k columns)
        k = inter.shape[1]
        b, Vk = beta[-k:], V[-k:, -k:]
        stat = float(b @ np.linalg.solve(Vk, b))
        rows.append({"subgroup": name, "reference": cats[0], "df": k, "wald": stat,
                     "p_value": chi2.sf(stat, k)})
    out = pd.DataFrame(rows)
    out["p_holm"] = holm(out["p_value"])
    return out


def subgroup_effects(frame):
    rows = []
    for name, lev in subgroup_levels(frame).items():
        for level in sorted(lev.unique()):
            d = frame[lev == level]
            yc = d.loc[d["arm"] == "control", "visit"]
            for a in EMAILS:
                yt = d.loc[d["arm"] == a, "visit"]
                se = np.sqrt(yt.var(ddof=1) / len(yt) + yc.var(ddof=1) / len(yc))
                est = yt.mean() - yc.mean()
                rows.append({"subgroup": name, "level": level, "comparison": f"{a} vs control",
                             "n": len(yt) + len(yc), "control_rate": yc.mean(), "estimate": est,
                             "se": se, "ci_low": est - Z * se, "ci_high": est + Z * se})
    return pd.DataFrame(rows)
