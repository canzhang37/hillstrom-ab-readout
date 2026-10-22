from importlib import resources

import duckdb
import numpy as np
from scipy.stats import chi2


def _sql(name):
    return resources.files("hillstrom_ab").joinpath("sql", f"{name}.sql").read_text()


def connect(csv_path, database=":memory:"):
    con = duckdb.connect(database)
    path = str(csv_path).replace("\\", "/").replace("'", "''")
    con.execute(_sql("customers").replace("{csv_path}", path))
    return con


def query(con, name):
    return con.execute(_sql(name)).df()


def srm(con):
    tab = query(con, "srm")
    stat = float(tab["chisq_part"].sum())
    return tab, stat, float(chi2.sf(stat, df=len(tab) - 1))


def arm_metrics(con):
    m = query(con, "arm_metrics")
    n = m["n"]
    m["se_visit_rate"] = np.sqrt(m["var_visit"] / n)
    m["se_conversion_rate"] = np.sqrt(m["var_conversion"] / n)
    m["se_spend_per_customer"] = np.sqrt(m["var_spend"] / n)
    # spend per visitor is a ratio of means -> delta method
    mu_s, mu_v = m["spend_per_customer"], m["visit_rate"]
    var_ratio = (m["var_spend"] / mu_v**2
                 - 2 * mu_s * m["cov_spend_visit"] / mu_v**3
                 + mu_s**2 * m["var_visit"] / mu_v**4) / n
    m["se_spend_per_visitor"] = np.sqrt(var_ratio)
    return m
