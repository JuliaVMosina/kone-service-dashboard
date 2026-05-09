"""
KONE Service Performance Dashboard — Synthetic Data Generator
Inspired by KONE's operational reporting style · Julia Mosina · 2026

Data proportions based on KONE Annual Reviews 2024–2025:
  - Revenue split: Service 42% · New Building Solutions 36% · Modernization 21%
  - Regional split: Greater China 40% · Europe 25% · Americas 19% · APMEA 15%
  - Service contract renewal rate: ~90%
  - Equipment in service base: ~1.8M units globally (scaled to 2000 for demo)
  - Strategy 'Rise': Accelerate Digital → connectivity improves uptime & MTTR

Output (data/raw/):
    equipment.csv
    service_calls.csv
    contracts.csv
    monthly_kpis.csv
    monthly_revenue.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

N_EQUIPMENT   = 2000
START_DATE    = datetime(2023, 1, 1)
END_DATE      = datetime(2025, 12, 31)

# Regional distribution (from KONE Annual Review 2025 — revenue by area)
REGIONS = {
    'Greater China': {'weight': 0.40, 'countries': ['China']},
    'Europe':        {'weight': 0.25, 'countries': ['Finland', 'Germany', 'France', 'Netherlands', 'Sweden', 'Poland']},
    'Americas':      {'weight': 0.19, 'countries': ['USA', 'Canada', 'Brazil', 'Mexico']},
    'APMEA':         {'weight': 0.16, 'countries': ['India', 'Australia', 'UAE', 'Saudi Arabia', 'South Korea']},
}

EQUIPMENT_TYPES  = ['Elevator', 'Escalator', 'Autowalk', 'Automatic Door']
EQUIP_WEIGHTS    = [0.65, 0.20, 0.10, 0.05]

BUILDING_TYPES   = ['Commercial', 'Residential', 'Industrial', 'Public / Transport', 'Healthcare']
BUILDING_WEIGHTS = [0.30, 0.35, 0.10, 0.15, 0.10]

CONTRACT_TYPES   = ['Full Maintenance', 'Basic Maintenance', 'Repair Only']
CONTRACT_WEIGHTS = [0.55, 0.30, 0.15]

# Digital connectivity — Accelerate Digital strategy (2025 target: >40%)
# Connected units have better uptime and faster response
CONNECTIVITY_BY_YEAR = {2023: 0.28, 2024: 0.35, 2025: 0.42}

# Revenue targets (MEUR, scaled down, proportional to real KONE figures)
# Real 2025: 11,245 MEUR total. We use 1/100 scale for demo.
REVENUE_BASE = {
    'Service':                {'2023': 41.3, '2024': 45.0, '2025': 47.2},
    'New Building Solutions': {'2023': 49.2, '2024': 45.1, '2025': 40.5},
    'Modernization':          {'2023': 19.0, '2024': 20.9, '2025': 23.6},
}

REGION_REVENUE_SPLIT = {
    'Greater China': 0.40,
    'Europe':        0.25,
    'Americas':      0.19,
    'APMEA':         0.16,
}


# ── Equipment ─────────────────────────────────────────────────────────────────

def generate_equipment() -> pd.DataFrame:
    region_list  = list(REGIONS.keys())
    region_w     = [REGIONS[r]['weight'] for r in region_list]
    regions      = np.random.choice(region_list, N_EQUIPMENT, p=region_w)

    countries = [
        np.random.choice(REGIONS[r]['countries']) for r in regions
    ]

    install_years = np.random.choice(
        range(1995, 2025), N_EQUIPMENT,
        p=np.array([1/(2025-1995)] * (2025-1995))
    )

    return pd.DataFrame({
        'equipment_id':    [f'EQ{i:05d}' for i in range(1, N_EQUIPMENT + 1)],
        'region':          regions,
        'country':         countries,
        'equipment_type':  np.random.choice(EQUIPMENT_TYPES, N_EQUIPMENT, p=EQUIP_WEIGHTS),
        'building_type':   np.random.choice(BUILDING_TYPES, N_EQUIPMENT, p=BUILDING_WEIGHTS),
        'installation_year': install_years,
        'equipment_age':   2025 - install_years,
        'contract_type':   np.random.choice(CONTRACT_TYPES, N_EQUIPMENT, p=CONTRACT_WEIGHTS),
        'is_connected_2023': np.random.rand(N_EQUIPMENT) < CONNECTIVITY_BY_YEAR[2023],
        'is_connected_2025': np.random.rand(N_EQUIPMENT) < CONNECTIVITY_BY_YEAR[2025],
    })


# ── Service Calls ──────────────────────────────────────────────────────────────

def generate_service_calls(equipment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    call_id = 1

    call_types = ['Planned Maintenance', 'Breakdown', 'Emergency', 'Entrapment', 'Inspection']

    for _, eq in equipment.iterrows():
        eid         = eq['equipment_id']
        region      = eq['region']
        age         = eq['equipment_age']
        connected   = eq['is_connected_2025']
        contract    = eq['contract_type']

        # Planned maintenance: Full=quarterly, Basic=semi-annual, Repair=annual
        pm_per_year = {'Full Maintenance': 4, 'Basic Maintenance': 2, 'Repair Only': 1}[contract]

        # Emergency call rate increases with age, decreases with connectivity
        emergency_rate = np.clip(0.3 + age * 0.02 - (0.15 if connected else 0), 0.1, 2.5)

        for year in [2023, 2024, 2025]:
            # Planned maintenance calls
            for q in range(pm_per_year):
                month    = int((q * 12 / pm_per_year) + np.random.randint(0, 3)) % 12 + 1
                call_day = datetime(year, month, np.random.randint(1, 28))
                if call_day > END_DATE:
                    continue

                # MTTR: Full maintenance faster, connected faster
                base_mttr = 2.0 if connected else 3.5
                mttr = max(0.5, np.random.exponential(base_mttr))

                rows.append({
                    'call_id':           f'C{call_id:07d}',
                    'equipment_id':      eid,
                    'region':            region,
                    'country':           eq['country'],
                    'call_date':         call_day.strftime('%Y-%m-%d'),
                    'year':              year,
                    'month':             month,
                    'call_type':         'Planned Maintenance',
                    'resolution_hours':  round(mttr, 2),
                    'first_time_fix':    np.random.rand() < (0.93 if connected else 0.82),
                    'technician_id':     f'T{np.random.randint(1, 201):04d}',
                })
                call_id += 1

            # Emergency / breakdown calls
            n_emergency = np.random.poisson(emergency_rate)
            for _ in range(n_emergency):
                call_day = START_DATE + timedelta(
                    days=np.random.randint(0, (END_DATE - START_DATE).days)
                )
                if call_day.year != year:
                    continue

                ctype = np.random.choice(
                    ['Breakdown', 'Emergency', 'Entrapment'],
                    p=[0.55, 0.30, 0.15]
                )
                # Emergency MTTR: connected units respond faster
                base_mttr = (2.5 if connected else 5.0) * (1.5 if ctype == 'Entrapment' else 1.0)
                mttr = max(0.5, np.random.exponential(base_mttr))

                rows.append({
                    'call_id':          f'C{call_id:07d}',
                    'equipment_id':     eid,
                    'region':           region,
                    'country':          eq['country'],
                    'call_date':        call_day.strftime('%Y-%m-%d'),
                    'year':             call_day.year,
                    'month':            call_day.month,
                    'call_type':        ctype,
                    'resolution_hours': round(mttr, 2),
                    'first_time_fix':   np.random.rand() < (0.85 if connected else 0.72),
                    'technician_id':    f'T{np.random.randint(1, 201):04d}',
                })
                call_id += 1

    return pd.DataFrame(rows)


# ── Contracts ──────────────────────────────────────────────────────────────────

def generate_contracts(equipment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    contract_id = 1

    for _, eq in equipment.iterrows():
        if eq['contract_type'] == 'Repair Only':
            continue  # no ongoing contract

        start = datetime(np.random.randint(2020, 2024), np.random.randint(1, 13), 1)

        annual_value = {
            'Full Maintenance': np.random.normal(4800, 800),
            'Basic Maintenance': np.random.normal(2400, 500),
        }.get(eq['contract_type'], 1200)

        # Simulate up to 3 renewal periods
        current_start = start
        for period in range(3):
            period_end = datetime(current_start.year + 1, current_start.month, 1)
            if period_end > END_DATE + timedelta(days=365):
                break

            # ~90% renewal rate (KONE Annual Review: "typically long and stable ~90% retention")
            if period == 0:
                status = 'Active' if period_end > datetime.now() else 'Renewed'
            else:
                if np.random.rand() < 0.90:
                    status = 'Renewed' if period_end < datetime.now() else 'Active'
                else:
                    status = 'Cancelled'

            rows.append({
                'contract_id':      f'CON{contract_id:06d}',
                'equipment_id':     eq['equipment_id'],
                'region':           eq['region'],
                'country':          eq['country'],
                'contract_type':    eq['contract_type'],
                'contract_start':   current_start.strftime('%Y-%m-%d'),
                'contract_end':     period_end.strftime('%Y-%m-%d'),
                'status':           status,
                'annual_value_eur': round(max(500, annual_value), 0),
            })
            contract_id += 1
            current_start = period_end

            if status == 'Cancelled':
                break

    return pd.DataFrame(rows)


# ── Monthly KPIs ───────────────────────────────────────────────────────────────

def generate_monthly_kpis(equipment: pd.DataFrame, calls: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for year in [2023, 2024, 2025]:
        for month in range(1, 13):
            if datetime(year, month, 1) > END_DATE:
                break

            for region in REGIONS.keys():
                eq_region   = equipment[equipment['region'] == region]
                n_eq        = len(eq_region)
                avg_age     = eq_region['equipment_age'].mean()
                conn_rate   = CONNECTIVITY_BY_YEAR.get(year, 0.35)

                # Uptime improves with connectivity and lower age
                base_uptime = 97.5 - avg_age * 0.03 + conn_rate * 1.5
                uptime_pct  = round(np.clip(np.random.normal(base_uptime, 0.3), 94.0, 99.8), 2)

                # Calls this month/region
                month_calls = calls[
                    (calls['region'] == region) &
                    (calls['year'] == year) &
                    (calls['month'] == month)
                ]
                planned   = len(month_calls[month_calls['call_type'] == 'Planned Maintenance'])
                breakdown = len(month_calls[month_calls['call_type'] == 'Breakdown'])
                emergency = len(month_calls[month_calls['call_type'] == 'Emergency'])
                entrap    = len(month_calls[month_calls['call_type'] == 'Entrapment'])
                total     = len(month_calls)

                avg_mttr = round(month_calls['resolution_hours'].mean(), 2) if total > 0 else 0
                ftf_rate = round(
                    month_calls['first_time_fix'].mean() * 100, 1
                ) if total > 0 else 0

                rows.append({
                    'year':                    year,
                    'month':                   month,
                    'month_date':              f'{year}-{month:02d}-01',
                    'region':                  region,
                    'equipment_count':         n_eq,
                    'connectivity_pct':        round(conn_rate * 100, 1),
                    'uptime_pct':              uptime_pct,
                    'avg_mttr_hours':          avg_mttr,
                    'first_time_fix_rate_pct': ftf_rate,
                    'planned_calls':           planned,
                    'breakdown_calls':         breakdown,
                    'emergency_calls':         emergency,
                    'entrapment_calls':        entrap,
                    'total_calls':             total,
                })

    return pd.DataFrame(rows)


# ── Monthly Revenue ────────────────────────────────────────────────────────────

def generate_monthly_revenue() -> pd.DataFrame:
    rows = []

    for year in [2023, 2024, 2025]:
        for month in range(1, 13):
            if datetime(year, month, 1) > END_DATE:
                break

            for business_line, yearly in REVENUE_BASE.items():
                annual = yearly[str(year)]

                # Seasonality: Q4 stronger for NBS/Modernization, Service more stable
                season = {
                    'Service': [0.08, 0.08, 0.08, 0.08, 0.085, 0.085,
                                0.085, 0.085, 0.085, 0.09, 0.09, 0.09],
                    'New Building Solutions': [0.06, 0.07, 0.08, 0.08, 0.09, 0.09,
                                               0.09, 0.09, 0.09, 0.095, 0.095, 0.08],
                    'Modernization': [0.07, 0.07, 0.08, 0.08, 0.085, 0.09,
                                      0.09, 0.09, 0.09, 0.095, 0.095, 0.085],
                }[business_line]

                monthly_total = annual * season[month - 1]

                for region, rsplit in REGION_REVENUE_SPLIT.items():
                    # Greater China: NBS declining 2024-2025 (from annual report)
                    if region == 'Greater China' and business_line == 'New Building Solutions':
                        rsplit = rsplit * (0.85 if year == 2024 else 0.72)
                    # Americas: NBS growing (from annual report)
                    elif region == 'Americas' and business_line == 'New Building Solutions':
                        rsplit = rsplit * (1.05 if year == 2024 else 1.12)

                    rev = monthly_total * rsplit * np.random.uniform(0.95, 1.05)

                    rows.append({
                        'year':          year,
                        'month':         month,
                        'month_date':    f'{year}-{month:02d}-01',
                        'region':        region,
                        'business_line': business_line,
                        'revenue_meur':  round(rev, 3),
                    })

    return pd.DataFrame(rows)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=== KONE Service Performance Dashboard — Data Generation ===\n")

    out = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    os.makedirs(out, exist_ok=True)

    print("Generating equipment...")
    equipment = generate_equipment()
    equipment.to_csv(f'{out}/equipment.csv', index=False)
    print(f"  equipment.csv          — {len(equipment):,} units")
    for r in REGIONS:
        n = (equipment['region'] == r).sum()
        print(f"    {r}: {n} units")

    print("\nGenerating service calls...")
    calls = generate_service_calls(equipment)
    calls.to_csv(f'{out}/service_calls.csv', index=False)
    print(f"  service_calls.csv      — {len(calls):,} calls")
    print(f"    Planned maintenance: {(calls.call_type == 'Planned Maintenance').sum():,}")
    print(f"    Breakdowns:          {(calls.call_type == 'Breakdown').sum():,}")
    print(f"    Emergencies:         {(calls.call_type == 'Emergency').sum():,}")
    print(f"    Entrapments:         {(calls.call_type == 'Entrapment').sum():,}")

    print("\nGenerating contracts...")
    contracts = generate_contracts(equipment)
    contracts.to_csv(f'{out}/contracts.csv', index=False)
    renewed = (contracts.status == 'Renewed').sum()
    total_c = len(contracts)
    print(f"  contracts.csv          — {total_c:,} records")
    print(f"    Renewal rate:        {renewed / total_c * 100:.1f}%")

    print("\nGenerating monthly KPIs...")
    kpis = generate_monthly_kpis(equipment, calls)
    kpis.to_csv(f'{out}/monthly_kpis.csv', index=False)
    print(f"  monthly_kpis.csv       — {len(kpis):,} rows")
    print(f"    Avg uptime 2023: {kpis[kpis.year==2023].uptime_pct.mean():.2f}%")
    print(f"    Avg uptime 2025: {kpis[kpis.year==2025].uptime_pct.mean():.2f}%")
    print(f"    Avg MTTR 2023:   {kpis[kpis.year==2023].avg_mttr_hours.mean():.2f}h")
    print(f"    Avg MTTR 2025:   {kpis[kpis.year==2025].avg_mttr_hours.mean():.2f}h")

    print("\nGenerating monthly revenue...")
    revenue = generate_monthly_revenue()
    revenue.to_csv(f'{out}/monthly_revenue.csv', index=False)
    total_rev = revenue.groupby('year')['revenue_meur'].sum()
    print(f"  monthly_revenue.csv    — {len(revenue):,} rows")
    for yr, rev in total_rev.items():
        print(f"    {yr} total: {rev:.1f} MEUR")

    print("\nDone. All files saved to data/raw/")


if __name__ == "__main__":
    main()
