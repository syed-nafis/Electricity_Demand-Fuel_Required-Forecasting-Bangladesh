-- Phase 4 serving-table schema for the PGCB dashboard.
-- Run ONCE in the Supabase SQL editor (Dashboard -> SQL Editor -> New query -> Run).
-- These are small "serving" tables the dashboard reads; full-resolution raw data
-- lives in Parquet (extracted_data/parquet/), not here.

-- First vertical slice: daily per-plant generation + fuel cost.
create table if not exists daily_plant_generation (
    date                 date              not null,
    plant_name           text              not null,
    electricity_gen_kwh  double precision,
    fuel_cost            double precision,
    primary key (date, plant_name)
);

create index if not exists idx_dpg_date  on daily_plant_generation (date);
create index if not exists idx_dpg_plant on daily_plant_generation (plant_name);

-- NOTE on security: the ETL writes with the service_role key (bypasses RLS).
-- Before exposing this to a public dashboard, enable RLS and add a read-only
-- policy for the anon role:
--   alter table daily_plant_generation enable row level security;
--   create policy "public read" on daily_plant_generation for select using (true);
