-- one row per customer; reference levels: suburban, phone, segment 1
SELECT
    customer_id,
    arm,
    visit,
    conversion,
    spend,
    CAST(recency AS DOUBLE) AS recency,
    history,
    CAST(mens AS DOUBLE) AS mens,
    CAST(womens AS DOUBLE) AS womens,
    CAST(newbie AS DOUBLE) AS newbie,
    CAST(lower(zip_code) = 'urban' AS DOUBLE) AS zip_urban,
    CAST(lower(zip_code) = 'rural' AS DOUBLE) AS zip_rural,
    CAST(lower(channel) = 'web' AS DOUBLE) AS channel_web,
    CAST(lower(channel) = 'multichannel' AS DOUBLE) AS channel_multichannel,
    CAST(history_segment LIKE '2)%' AS DOUBLE) AS hseg_2,
    CAST(history_segment LIKE '3)%' AS DOUBLE) AS hseg_3,
    CAST(history_segment LIKE '4)%' AS DOUBLE) AS hseg_4,
    CAST(history_segment LIKE '5)%' AS DOUBLE) AS hseg_5,
    CAST(history_segment LIKE '6)%' AS DOUBLE) AS hseg_6,
    CAST(history_segment LIKE '7)%' AS DOUBLE) AS hseg_7
FROM customers
WHERE arm IS NOT NULL
ORDER BY customer_id;
