# KONE Service Dashboard — DAX Measures

## Data Model

### Tables and relationships
- `equipment` — 2,000 units (equipment_id PK)
- `service_calls` — 18,972 calls (equipment_id FK → equipment)
- `contracts` — 5,033 records (equipment_id FK → equipment)
- `monthly_kpis` — 144 rows (region + year + month — no direct FK, use as standalone)
- `monthly_revenue` — 432 rows (business_line + region + year + month)

### Date table (create in Power BI)
Go to Modeling → New Table:
```
DateTable = CALENDAR(DATE(2023,1,1), DATE(2025,12,31))
```
Then add columns:
```
Year = YEAR(DateTable[Date])
Month = MONTH(DateTable[Date])
MonthName = FORMAT(DateTable[Date], "MMM")
Quarter = "Q" & QUARTER(DateTable[Date])
YearMonth = FORMAT(DateTable[Date], "YYYY-MM")
```
Link: `service_calls[call_date]` → `DateTable[Date]`

---

## Page 1 — Executive Overview

### KPI Cards (top row)

```dax
-- Average Uptime % (current year)
Avg Uptime % =
CALCULATE(
    AVERAGE(monthly_kpis[uptime_pct]),
    monthly_kpis[year] = MAX(monthly_kpis[year])
)

-- Contract Renewal Rate
Renewal Rate % =
DIVIDE(
    COUNTROWS(FILTER(contracts, contracts[status] = "Renewed")),
    COUNTROWS(contracts)
) * 100

-- Total Service Calls (selected period)
Total Service Calls =
COUNTROWS(service_calls)

-- Emergency Call Share
Emergency Share % =
DIVIDE(
    COUNTROWS(FILTER(service_calls, service_calls[call_type] <> "Planned Maintenance")),
    COUNTROWS(service_calls)
) * 100

-- Connected Equipment %
Connectivity % =
DIVIDE(
    COUNTROWS(FILTER(equipment, equipment[is_connected_2025] = TRUE())),
    COUNTROWS(equipment)
) * 100
```

### Revenue KPI Cards

```dax
-- Total Revenue (all years)
Total Revenue MEUR =
SUM(monthly_revenue[revenue_meur])

-- YoY Revenue Growth
Revenue YoY % =
VAR CurrentYear = CALCULATE(SUM(monthly_revenue[revenue_meur]), monthly_revenue[year] = 2025)
VAR PriorYear   = CALCULATE(SUM(monthly_revenue[revenue_meur]), monthly_revenue[year] = 2024)
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear) * 100
```

### Visuals on this page
- 5 KPI cards (top row): Uptime %, Renewal Rate, Total Calls, Emergency Share, Connectivity %
- Clustered bar: Revenue by Business Line (3 lines × 3 years)
- Donut: Service calls by region
- Line: Monthly revenue trend 2023–2025

---

## Page 2 — Service Operations

### MTTR and First-Time Fix

```dax
-- Average MTTR
Avg MTTR Hours =
AVERAGE(service_calls[resolution_hours])

-- MTTR for connected equipment only
Avg MTTR Connected =
CALCULATE(
    AVERAGE(service_calls[resolution_hours]),
    RELATED(equipment[is_connected_2025]) = TRUE()
)

-- MTTR improvement 2023 vs 2025
MTTR Improvement % =
VAR MTTR_2023 = CALCULATE(AVERAGE(monthly_kpis[avg_mttr_hours]), monthly_kpis[year] = 2023)
VAR MTTR_2025 = CALCULATE(AVERAGE(monthly_kpis[avg_mttr_hours]), monthly_kpis[year] = 2025)
RETURN DIVIDE(MTTR_2023 - MTTR_2025, MTTR_2023) * 100

-- First-Time Fix Rate
First Time Fix % =
DIVIDE(
    COUNTROWS(FILTER(service_calls, service_calls[first_time_fix] = TRUE())),
    COUNTROWS(service_calls)
) * 100

-- Planned vs Emergency ratio
Planned Calls % =
DIVIDE(
    COUNTROWS(FILTER(service_calls, service_calls[call_type] = "Planned Maintenance")),
    COUNTROWS(service_calls)
) * 100
```

### Call volume breakdown

```dax
-- Breakdown calls count
Breakdown Calls =
CALCULATE(COUNTROWS(service_calls), service_calls[call_type] = "Breakdown")

-- Emergency calls count
Emergency Calls =
CALCULATE(COUNTROWS(service_calls), service_calls[call_type] = "Emergency")

-- Entrapment calls count
Entrapment Calls =
CALCULATE(COUNTROWS(service_calls), service_calls[call_type] = "Entrapment")
```

### Visuals on this page
- KPI cards: Avg MTTR, First-Time Fix %, Planned %, Entrapment count
- Stacked bar: Call types by region (Planned / Breakdown / Emergency / Entrapment)
- Line: MTTR trend by month (2023–2025) — shows downward trend
- Bar: Avg MTTR by equipment type (Elevator / Escalator / Autowalk / Door)
- Matrix: Region × Year with MTTR and FTF%

---

## Page 3 — Contract Health

```dax
-- Active contracts
Active Contracts =
CALCULATE(COUNTROWS(contracts), contracts[status] = "Active")

-- Renewed contracts
Renewed Contracts =
CALCULATE(COUNTROWS(contracts), contracts[status] = "Renewed")

-- Cancelled contracts
Cancelled Contracts =
CALCULATE(COUNTROWS(contracts), contracts[status] = "Cancelled")

-- Renewal rate by contract type
Renewal Rate Full =
CALCULATE(
    DIVIDE(
        COUNTROWS(FILTER(contracts, contracts[status] = "Renewed")),
        COUNTROWS(contracts)
    ),
    contracts[contract_type] = "Full Maintenance"
) * 100

-- Churn risk (Cancelled / Total)
Churn Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(contracts), contracts[status] = "Cancelled"),
    COUNTROWS(contracts)
) * 100
```

### Visuals on this page
- KPI cards: Total Contracts, Renewal Rate %, Churn Rate %, Active count
- Donut: Contract status mix (Active / Renewed / Cancelled)
- Clustered bar: Renewal rate by contract type
- Bar: Renewal rate by region
- Table: Region × Contract Type × Renewal Rate (matrix)

---

## Page 4 — Digital Connectivity

```dax
-- Connectivity by year (from monthly_kpis)
Connectivity 2023 =
CALCULATE(AVERAGE(monthly_kpis[connectivity_pct]), monthly_kpis[year] = 2023)

Connectivity 2024 =
CALCULATE(AVERAGE(monthly_kpis[connectivity_pct]), monthly_kpis[year] = 2024)

Connectivity 2025 =
CALCULATE(AVERAGE(monthly_kpis[connectivity_pct]), monthly_kpis[year] = 2025)

-- Uptime lift: connected vs non-connected (from service_calls + equipment)
Uptime Connected =
CALCULATE(
    AVERAGE(monthly_kpis[uptime_pct]),
    monthly_kpis[connectivity_pct] > 35
)

-- Connectivity growth 2023→2025
Connectivity Growth pp =
[Connectivity 2025] - [Connectivity 2023]
```

### Visuals on this page
- KPI cards: Connectivity 2023 / 2024 / 2025 (shows 28% → 35% → 42%)
- Line: Connectivity % trend by month (2023–2025)
- Scatter: Connectivity % vs Uptime % by region/month — shows correlation
- Bar: MTTR connected vs non-connected by region
- Text box with insight: "Every 10pp increase in connectivity reduces MTTR by ~X%"

---

## Page 5 — Revenue Trends

```dax
-- Revenue by business line
Service Revenue =
CALCULATE(SUM(monthly_revenue[revenue_meur]), monthly_revenue[business_line] = "Service")

NBS Revenue =
CALCULATE(SUM(monthly_revenue[revenue_meur]), monthly_revenue[business_line] = "New Building Solutions")

Modernization Revenue =
CALCULATE(SUM(monthly_revenue[revenue_meur]), monthly_revenue[business_line] = "Modernization")

-- Business line share %
Service Share % =
DIVIDE([Service Revenue], [Total Revenue MEUR]) * 100

-- Revenue per region
Revenue Greater China =
CALCULATE(SUM(monthly_revenue[revenue_meur]), monthly_revenue[region] = "Greater China")

-- MoM growth
Revenue MoM % =
VAR CurrentMonth = SUM(monthly_revenue[revenue_meur])
VAR PriorMonth =
    CALCULATE(
        SUM(monthly_revenue[revenue_meur]),
        DATEADD(DateTable[Date], -1, MONTH)
    )
RETURN DIVIDE(CurrentMonth - PriorMonth, PriorMonth) * 100
```

### Visuals on this page
- KPI cards: Service %, NBS %, Modernization % (with trend arrows)
- Area chart: Revenue by business line over time (stacked)
- Donut: Regional revenue split (Greater China 40% dominance visible)
- Line: Service revenue growth vs NBS decline — strategic narrative
- Bar: Revenue by region × year

---

## Design Settings

### Theme colors
- Primary blue: `#3160E8`
- White background: `#FFFFFF`
- Light grey separator: `#F2F2F2`
- Info box background: `#F5F0EB`
- Text dark: `#1A1A1A`
- Positive trend: `#107C10` (green)
- Negative / alert: `#D83B01` (red)

### Format rules
- No gridlines in charts
- KPI cards: large number, small label below, trend arrow
- Table headers: blue fill `#3160E8`, white text
- Font: Segoe UI throughout
- All % values: 1 decimal place
- MEUR values: 1 decimal place

### Conditional formatting (for matrix/tables)
- Uptime %: green if > 97.5%, yellow if 96–97.5%, red if < 96%
- MTTR: green if < 2.5h, yellow if 2.5–4h, red if > 4h
- Renewal Rate: green if > 88%, red if < 85%
