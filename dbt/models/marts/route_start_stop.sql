With s as (
    SELECT *,
    ROW_NUMBER() OVER (PARTITION BY schedule_id ORDER BY loc_offset) as rn_asc,
    ROW_NUMBER() OVER (PARTITION BY schedule_id ORDER BY loc_offset DESC) as rn_desc,
    FROM `rail_data.fact_train_scheduled_location`
),
st as (
  SELECT *
  FROM s
  WHERE rn_asc = 1 or rn_desc = 1
), str as (
    SELECT s.schedule_id,s.location_id as origin_loc_id,s1.location_id as terminating_loc_id,s.rn_asc,s1.rn_asc 
    FROM st as s
    JOIN st as s1 ON s.schedule_id = s1.schedule_id AND s.location_id != s1.location_id
),
strp as (select dts.schedule_id,dts.train_uid,dl.location_name as origin, nl.location_name as terminating, CONCAT(dl.location_name,'-',nl.location_name) as route_desc, row_number() over (partition by train_uid) as rn
from str
left join `rail_data.dim_train_schedule` dts on str.schedule_id = dts.schedule_id
left join `rail_data.dim_location` dl on str.origin_loc_id = dl.location_id
left join `rail_data.dim_location` nl on str.terminating_loc_id = nl.location_id )


select * from strp where rn = 1