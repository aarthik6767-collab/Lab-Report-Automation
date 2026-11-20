-- Run in Supabase SQL Editor. Create PRIVATE Storage bucket `lab-reports` separately.
create extension if not exists pgcrypto;
create table if not exists public.reports (
 id uuid primary key default gen_random_uuid(),
 patient_name text not null,
 patient_phone text not null,
 report_type text not null,
 storage_path text not null,
 secure_token text not null unique,
 expires_at timestamptz not null,
 is_critical boolean not null default false,
 doctor_notes text not null default '',
 friendly_note text not null default '',
 created_at timestamptz not null default now()
);
create index if not exists reports_created_at_idx on public.reports(created_at desc);
create index if not exists reports_token_idx on public.reports(secure_token);
create index if not exists reports_phone_idx on public.reports(patient_phone);
alter table public.reports enable row level security;
-- No anonymous/public SELECT policy. API accesses this table server-side.
-- Never expose SUPABASE_SERVICE_ROLE_KEY in React or commit it to GitHub.
