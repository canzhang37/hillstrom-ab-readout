# subgroup tests, uplift model, held-out policy values
# python -m hillstrom_ab.targeting data/hillstrom.csv results/targeting
import sys
from pathlib import Path

import pandas as pd

from .metrics import connect, query
from .subgroups import interaction_tests, subgroup_effects
from .uplift import fit_t_learner, policy_values, predict_uplift, qini, split


def main(csv, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    frame = query(connect(csv), "analysis_frame")

    tests = interaction_tests(frame)
    tests.to_csv(out / "subgroup_tests.csv", index=False)
    subgroup_effects(frame).to_csv(out / "subgroup_effects.csv", index=False)

    train = split(frame)
    held = frame[~train]
    uplift = predict_uplift(fit_t_learner(frame[train]), held)
    curves, coefs = [], []
    for email in ["mens", "womens"]:
        c, coef = qini(held, uplift[f"uplift_{email}"], email)
        curves.append(c)
        coefs.append({"email": email, "qini_coefficient": coef})
    pd.concat(curves).to_csv(out / "qini_curves.csv", index=False)
    pd.DataFrame(coefs).to_csv(out / "qini_coefficients.csv", index=False)

    values, shares = policy_values(held, uplift)
    values.to_csv(out / "policy_values.csv", index=False)
    shares.to_csv(out / "targeting_shares.csv", index=False)
    gain = values.set_index("policy").loc["targeting minus mens_to_all"]
    print(tests.to_string(index=False))
    print(values.to_string(index=False))
    print("targeting replaces Mens to all:", bool(gain["ci_low"] > 0))


if __name__ == "__main__":
    main(*sys.argv[1:3])
