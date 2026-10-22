CREATE OR REPLACE VIEW customers AS
SELECT
    row_number() OVER () AS customer_id,
    CAST(recency AS INTEGER) AS recency,
    history_segment,
    CAST(history AS DOUBLE) AS history,
    CAST(mens AS INTEGER) AS mens,
    CAST(womens AS INTEGER) AS womens,
    zip_code,
    CAST(newbie AS INTEGER) AS newbie,
    channel,
    segment AS segment_raw,
    CASE segment
        WHEN 'Mens E-Mail' THEN 'mens'
        WHEN 'Womens E-Mail' THEN 'womens'
        WHEN 'No E-Mail' THEN 'control'
    END AS arm,
    CAST(visit AS INTEGER) AS visit,
    CAST(conversion AS INTEGER) AS conversion,
    CAST(spend AS DOUBLE) AS spend
FROM read_csv('{csv_path}', header = true);
