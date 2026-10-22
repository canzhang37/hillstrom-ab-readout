-- per-arm metrics, plus moments for the SEs
SELECT
    arm,
    count(*) AS n,
    sum(visit) AS visitors,
    sum(conversion) AS converters,
    sum(spend) AS total_spend,
    avg(visit) AS visit_rate,
    avg(conversion) AS conversion_rate,
    avg(spend) AS spend_per_customer,
    sum(spend) / nullif(sum(visit), 0) AS spend_per_visitor,
    sum(spend) / nullif(sum(conversion), 0) AS spend_per_converter,
    var_samp(visit) AS var_visit,
    var_samp(conversion) AS var_conversion,
    var_samp(spend) AS var_spend,
    covar_samp(spend, visit) AS cov_spend_visit
FROM customers
WHERE arm IS NOT NULL
GROUP BY arm
ORDER BY arm;
