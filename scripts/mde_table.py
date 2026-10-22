# MDE table for docs/design.md
# python scripts/mde_table.py results/design_mde.csv
import csv
import sys

from scipy.stats import norm

N_TOTAL = 64000
N_ARM = N_TOTAL // 3
POWER = 0.80
ALPHAS = {"0.05": 0.05, "0.05/3 (Holm, first step)": 0.05 / 3}

# a grid, not estimates (plan was fixed before outcomes)
BASELINES = {
    "visit": [0.05, 0.10, 0.15, 0.20],
    "conversion": [0.005, 0.01, 0.02],
}


def mde_proportion(p, n, alpha, power):
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    return z * (2 * p * (1 - p) / n) ** 0.5


def mde_sd_units(n, alpha, power):
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    return z * (2 / n) ** 0.5


def main(out_path):
    rows = []
    for alpha_label, alpha in ALPHAS.items():
        for metric, grid in BASELINES.items():
            for p in grid:
                d = mde_proportion(p, N_ARM, alpha, POWER)
                rows.append([metric, alpha_label, p, round(d, 5), round(d / p, 4)])
        rows.append(["continuous (SD units)", alpha_label, "",
                     round(mde_sd_units(N_ARM, alpha, POWER), 5), ""])
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "alpha", "baseline", "mde_absolute", "mde_relative"])
        w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1])
