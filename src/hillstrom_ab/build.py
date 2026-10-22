# python -m hillstrom_ab.build data/hillstrom.csv results/checks --checks-only
# python -m hillstrom_ab.build data/hillstrom.csv results/metrics
import argparse
from pathlib import Path

from .metrics import arm_metrics, connect, query, srm


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("out_dir")
    p.add_argument("--checks-only", action="store_true")  # no outcomes
    args = p.parse_args(argv)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    con = connect(args.csv)

    checks = query(con, "data_checks")
    checks.to_csv(out / "data_checks.csv", index=False)
    tab, stat, pval = srm(con)
    tab.assign(chisq=stat, p_value=pval).to_csv(out / "srm.csv", index=False)
    query(con, "balance").to_csv(out / "balance.csv", index=False)
    print(checks.to_string(index=False))
    print(f"SRM chi-square {stat:.3f}, p = {pval:.4g}")

    if not args.checks_only:
        arm_metrics(con).to_csv(out / "arm_metrics.csv", index=False)


if __name__ == "__main__":
    main()
