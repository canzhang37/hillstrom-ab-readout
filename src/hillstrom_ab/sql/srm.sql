-- arm counts vs a 1/3 split; p-value in metrics.srm()
WITH counts AS (
    SELECT arm, count(*) AS n
    FROM customers
    WHERE arm IS NOT NULL
    GROUP BY arm
),
total AS (
    SELECT sum(n) AS n_total FROM counts
)
SELECT
    c.arm,
    c.n,
    c.n / t.n_total AS share,
    t.n_total / 3.0 AS expected,
    power(c.n - t.n_total / 3.0, 2) / (t.n_total / 3.0) AS chisq_part
FROM counts c, total t
ORDER BY c.arm;
