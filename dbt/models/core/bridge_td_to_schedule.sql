
with td as (
    select distinct train_signalling_id
    from {{ ref('stg_rail_describer')}}
    where train_signalling_id is not null
    and msg_type != "CT"
),
sched as (
    select distinct
        schedule_id,
        train_uid,
        train_signalling_id,
        schedule_start_date,
        schedule_end_date
    from {{ ref('dim_train_schedule')}}
    where train_signalling_id is not null
)

SELECT * FROM
(
select
    {{ dbt_utils.generate_surrogate_key([
        'td.train_signalling_id', 'schedule_id', 'schedule_start_date', 'schedule_end_date'
    ]) }} AS bridge_id,
    td.train_signalling_id,
    sched.train_uid,
    sched.schedule_id,
    sched.schedule_start_date,
    sched.schedule_end_date
from td
left join sched
  on td.train_signalling_id = sched.train_signalling_id
UNION ALL
    SELECT
    {{ dbt_utils.generate_surrogate_key([
        "'Unknown'"
    ]) }} AS bridge_id,
    null as train_signalling_id,
    null as train_uid,
    null as schedule_id,
    null as schedule_start_date,
    null as schedule_end_date
)