# README figure: visit lift by buyer group
# python scripts/key_figure.py results figures
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "base": "#c3c2b7", "mens": "#2a78d6", "womens": "#eb6834"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781",
             "grid": "#2c2c2a", "base": "#383835", "mens": "#3987e5", "womens": "#d95926"},
}
ROWS = [("overall", "All customers"), ("womens_only", "Bought womens items only"),
        ("mens_only", "Bought mens items only"), ("both", "Bought both")]
PX = 72 / 100  # pt per px at dpi 100


def load(results):
    u = pd.read_csv(results / "effects" / "effects_unadjusted.csv")
    u = u[u["metric"] == "visit_rate"].assign(level="overall")
    s = pd.read_csv(results / "targeting" / "subgroup_effects.csv")
    s = s[s["subgroup"] == "buyer_type"]
    d = pd.concat([u, s])[["level", "comparison", "estimate", "ci_low", "ci_high"]]
    d = d[d["comparison"].str.endswith("vs control")].copy()
    d["email"] = d["comparison"].str.split(" ").str[0]
    for c in ["estimate", "ci_low", "ci_high"]:
        d[c] = 100 * d[c]
    return d


def draw(d, theme, path):
    t = THEMES[theme]
    plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]
    fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=100)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])

    ypos = {level: i for i, (level, _) in enumerate(ROWS)}
    for email, offset in [("mens", -0.14), ("womens", 0.14)]:
        e = d[d["email"] == email]
        y = e["level"].map(ypos) + offset
        ax.hlines(y, e["ci_low"], e["ci_high"], color=t[email], lw=2 * PX)
        ax.plot(e["estimate"], y, "o", ms=9 * PX, color=t[email], mec=t["surface"], mew=2 * PX,
                label=f"{email.capitalize()} e-mail", zorder=3)
        for level in ["overall"] + (["mens_only"] if email == "womens" else []):
            r = e[e["level"] == level].iloc[0]
            ax.text(r["ci_high"] + 0.35, ypos[level] + offset, f"+{r['estimate']:.1f}",
                    va="center", fontsize=9, color=t["ink2"])

    ax.axvline(0, color=t["base"], lw=1 * PX, zorder=1)
    ax.axhline(0.5, color=t["grid"], lw=1 * PX)
    ax.set_yticks(range(len(ROWS)), [label for _, label in ROWS])
    ax.set_ylim(len(ROWS) - 0.5, -0.5)
    ax.set_xlim(-1, 17)
    ax.set_xticks(range(0, 17, 4))
    ax.grid(axis="x", color=t["grid"], lw=1 * PX)
    ax.set_axisbelow(True)
    ax.tick_params(colors=t["muted"], length=0, labelsize=9)
    for lab in ax.get_yticklabels():
        lab.set_color(t["ink"])
        lab.set_fontsize(10)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_xlabel("Difference in two-week visit rate vs no e-mail (percentage points, 95% interval)",
                  color=t["ink2"], fontsize=9, labelpad=8)

    fig.text(0.02, 0.95, "The Mens e-mail lifts visits in every buyer group",
             fontsize=13, fontweight="semibold", color=t["ink"])
    fig.text(0.02, 0.895, "The Womens e-mail matches it only among customers who bought womens items alone",
             fontsize=9.5, color=t["ink2"])
    leg = ax.legend(loc="upper right", frameon=False, fontsize=9, handletextpad=0.3)
    for txt in leg.get_texts():
        txt.set_color(t["ink2"])
    fig.text(0.02, 0.02, "Hillstrom (2008) e-mail test, 64,000 customers. Buyer group from past-year purchases.",
             fontsize=8, color=t["muted"])
    fig.subplots_adjust(left=0.27, right=0.97, top=0.84, bottom=0.2)
    fig.savefig(path, dpi=200, facecolor=t["surface"])
    plt.close(fig)


def main(results, out_dir):
    results, out_dir = Path(results), Path(out_dir)
    out_dir.mkdir(exist_ok=True)
    d = load(results)
    for theme in THEMES:
        draw(d, theme, out_dir / f"visit_lift_{theme}.png")


if __name__ == "__main__":
    main(*sys.argv[1:3])
