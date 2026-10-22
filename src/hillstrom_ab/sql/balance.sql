-- SMD of each covariate, e-mail arm vs control
WITH x AS (
    SELECT
        arm,
        CAST(recency AS DOUBLE) AS recency,
        history,
        CAST(mens AS DOUBLE) AS mens,
        CAST(womens AS DOUBLE) AS womens,
        CAST(newbie AS DOUBLE) AS newbie,
        CAST(lower(zip_code) = 'urban' AS DOUBLE) AS zip_urban,
        CAST(lower(zip_code) LIKE 's%rban' AS DOUBLE) AS zip_suburban,  -- file says "Surburban"
        CAST(lower(zip_code) = 'rural' AS DOUBLE) AS zip_rural,
        CAST(lower(channel) = 'web' AS DOUBLE) AS channel_web,
        CAST(lower(channel) = 'phone' AS DOUBLE) AS channel_phone,
        CAST(lower(channel) = 'multichannel' AS DOUBLE) AS channel_multichannel
    FROM customers
    WHERE arm IS NOT NULL
),
long AS (
    SELECT arm, covariate, val
    FROM x
    UNPIVOT (val FOR covariate IN (
        recency, history, mens, womens, newbie,
        zip_urban, zip_suburban, zip_rural,
        channel_web, channel_phone, channel_multichannel
    ))
),
stats AS (
    SELECT covariate, arm, avg(val) AS mean, var_samp(val) AS var, count(*) AS n
    FROM long
    GROUP BY covariate, arm
)
SELECT
    t.covariate,
    t.arm,
    t.mean,
    c.mean AS control_mean,
    (t.mean - c.mean) / sqrt((t.var + c.var) / 2) AS smd
FROM stats t
JOIN stats c ON t.covariate = c.covariate AND c.arm = 'control'
WHERE t.arm <> 'control'
ORDER BY t.covariate, t.arm;
