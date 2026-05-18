WITH latest AS (
  SELECT
    train_id,
    MAX(actual_timestamp) AS last_event_ts
  FROM {{ref('fact_train_movement')}}
  GROUP BY train_id
),
latest_event AS (
  SELECT
    fm.train_id,
    fm.schedule_id,
    fm.location_id,
    fm.next_location_id,
    fm.toc_id,

    fm.planned_timestamp,
    fm.actual_timestamp,

    fm.event_type,
    fm.planned_event_type,

    fm.timetable_variation,
    fm.variation_status,

  FROM latest l
  JOIN {{ ref('fact_train_movement' )}} fm
    ON l.train_id = fm.train_id
   AND l.last_event_ts = fm.actual_timestamp
)

SELECT *
FROM latest_event
ORDER BY actual_timestamp DESC