{{ config(
    unique_key='location_id',
    alias='dim_geo'
) }}

with naptan_raw as (
    select *
    from {{ ref('stops')}}

),

location_base as (
    select
        l.location_id,
        l.station_id,
        l.crs_code,
        l.tiploc_code,
        l.location_name,
        l.source_system,
        l.dbt_updated_at,
        row_number() over (partition by l.station_id order by l.tiploc_code DESC) as rn
    from {{ ref('dim_location') }} l
),

geo as (
    select
        l.location_id,
        l.tiploc_code,
        l.crs_code,
        l.location_name,
        l.station_id,
        -- Create ATCOCode as 9100 + TIPLOC
        concat('9100', l.tiploc_code) as atco_code,
        n.Latitude as latitude,
        n.Longitude as longitude,
        CONCAT(Latitude,',',Longitude) as coordinates,
        n.Easting,
        n.Northing,
        n.StopType,
        l.source_system,
        current_timestamp() as dbt_updated_at
    from location_base l
    left join naptan_raw n
        on  l.tiploc_code = SUBSTRING(n.ATCOCode,5,1000)
    where rn =1
)

select * from geo


