-- counts of bad rows (ok = what the design expects)
WITH c AS (
    SELECT
        count(*) AS n_rows,
        count(*) FILTER (WHERE arm IS NULL) AS unknown_arm,
        count(*) FILTER (
            WHERE recency IS NULL OR history IS NULL OR mens IS NULL OR womens IS NULL
               OR zip_code IS NULL OR newbie IS NULL OR channel IS NULL
               OR visit IS NULL OR conversion IS NULL OR spend IS NULL
        ) AS missing_values,
        count(*) FILTER (
            WHERE visit NOT IN (0, 1) OR conversion NOT IN (0, 1)
               OR mens NOT IN (0, 1) OR womens NOT IN (0, 1) OR newbie NOT IN (0, 1)
        ) AS non_binary_flags,
        count(*) FILTER (WHERE spend < 0) AS negative_spend,
        count(*) FILTER (WHERE spend > 0 AND conversion = 0) AS spend_without_conversion,
        count(*) FILTER (WHERE conversion = 1 AND visit = 0) AS conversion_without_visit,
        count(*) FILTER (
            WHERE lower(zip_code) NOT IN ('urban', 'rural') AND lower(zip_code) NOT LIKE 's%rban'
        ) AS unknown_zip_code,
        count(*) FILTER (WHERE lower(channel) NOT IN ('web', 'phone', 'multichannel')) AS unknown_channel
    FROM customers
)
SELECT
    check_name,
    value,
    CASE WHEN check_name = 'n_rows' THEN value = 64000 ELSE value = 0 END AS ok
FROM c
UNPIVOT (value FOR check_name IN (
    n_rows, unknown_arm, missing_values, non_binary_flags, negative_spend,
    spend_without_conversion, conversion_without_visit, unknown_zip_code, unknown_channel
));
