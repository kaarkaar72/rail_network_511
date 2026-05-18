WITH merged AS (
  SELECT 
    tsv.train_id,
    tsv.toc_id,
    dts.train_uid,
    dts.train_signalling_id,
    dl.location_name,
    dl.crs_code,
    tsv.event_type,
    tsv.planned_event_type,
    tsv.actual_timestamp,
    tsv.planned_timestamp,
    tsv.timetable_variation,
    tsv.variation_status,
    TIMESTAMP(
      DATETIME(
        IF(tsv.actual_timestamp IS NOT NULL,
           DATE(tsv.actual_timestamp),
           DATE(CURRENT_TIMESTAMP())
        ),
        COALESCE(
          fsl.arrival_public_timetable_time,
          fsl.departure_public_timetable_time,
          fsl.arrival_working_timetable_time,
          fsl.departure_working_timetable_time,
          fsl.passing_working_timetable_time
        )
      )
    ) AS scheduled_event_timestamp,
    fsl.arrival_public_timetable_time,
    fsl.arrival_working_timetable_time,
    fsl.departure_public_timetable_time,
    fsl.departure_working_timetable_time,
    fsl.passing_working_timetable_time,
    fsl.platform,
    fsl.line
  FROM {{ ref('fact_train_scheduled_location') }} fsl
  LEFT JOIN {{ ref("train_status") }} tsv
    ON tsv.schedule_id = fsl.schedule_id
   AND tsv.location_id = fsl.location_id 
  LEFT JOIN {{ ref('dim_train_schedule') }} dts  
    ON tsv.schedule_id = dts.schedule_id
  LEFT JOIN {{ ref('dim_location') }} dl
    ON tsv.location_id = dl.location_id
  WHERE tsv.train_id IS NOT NULL
),

-- Keep only the latest position per train
latest_per_train AS (
  SELECT 
    * EXCEPT(rn)
  FROM (
    SELECT
      m.*,
      ROW_NUMBER() OVER (
        PARTITION BY train_id 
        ORDER BY actual_timestamp DESC, scheduled_event_timestamp DESC
      ) AS rn
    FROM merged m
  )
  WHERE rn = 1
)

SELECT *
FROM latest_per_train
WHERE scheduled_event_timestamp BETWEEN CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
                                  AND CURRENT_TIMESTAMP() + INTERVAL 1 HOUR
ORDER BY scheduled_event_timestamp