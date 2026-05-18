with s as(
  SELECT 
    DISTINCT
    -- Correct service date derived from planned date
    DATE(tsv.planned_timestamp) AS service_date,

    tsv.actual_timestamp,
    tsv.planned_timestamp,
    
    dt.toc_name,
    tsv.train_id,
    dts.train_uid,
    rss.route_desc,
    dts.train_signalling_id,
    dts.stp_indicator,
    dts.train_category,

    dl.station_id AS location_id,
    dl.location_name AS location_name,

    nl.station_id AS next_location_id,
    nl.location_name AS next_location_name,

    fsl.location_type_desc,
    tsv.event_type,
    
    -- Raw variation
    tsv.timetable_variation,
      CASE 
          WHEN timetable_variation <= 0 THEN 'on_time'
          WHEN timetable_variation BETWEEN 1 AND 5 THEN 'slight_delay'
          WHEN timetable_variation BETWEEN 6 AND 10 THEN 'delay'
          ELSE 'major_delay'
        END AS delay_category,
    

    tsv.next_report_run_time

  FROM `rail_data.fact_train_scheduled_location` fsl
  LEFT JOIN `rail_data.fact_train_movement` tsv
    ON tsv.schedule_id = fsl.schedule_id
  AND tsv.location_id = fsl.location_id
  LEFT JOIN `rail_data.dim_train_schedule` dts  
    ON tsv.schedule_id = dts.schedule_id
  left join `rail_data.route_start_stop` rss 
    on dts.train_uid = rss.train_uid
  LEFT JOIN `rail_data.dim_location` dl
    ON tsv.location_id = dl.location_id
  LEFT JOIN `rail_data.dim_location` nl
    ON tsv.next_location_id = nl.location_id
  LEFT JOIN `rail_data.dim_toc` dt
    ON tsv.toc_id = dt.toc_id

  WHERE tsv.train_id IS NOT NULL
  AND tsv.actual_timestamp IS NOT NULL

)

select * from s
