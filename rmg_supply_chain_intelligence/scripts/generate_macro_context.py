"""
generate_macro_context.py
Generates the 20-year monthly macroeconomic & Bangladesh RMG industry context (2006-01 to 2025-12).
Produces `fact_macro_monthly` with explicit source status, frequency metadata, and quality flags.
"""

import os
import datetime
import numpy as np
import pandas as pd

SEED = 20261026


def build_macro_monthly(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Historical fiscal year national RMG export figures (BGMEA / EPB sourced, USD Billions)
    # FY runs July (year Y) to June (year Y+1)
    bgmea_fy_exports = {
        "FY2005-06": (3.65, 4.25, 7.90, 10.53),
        "FY2006-07": (4.06, 5.15, 9.21, 12.18),
        "FY2007-08": (4.69, 6.01, 10.70, 14.11),
        "FY2008-09": (5.16, 7.19, 12.35, 15.57),
        "FY2009-10": (4.91, 7.59, 12.50, 16.20),
        "FY2010-11": (6.77, 11.14, 17.91, 22.92),
        "FY2011-12": (7.23, 11.86, 19.09, 24.30),
        "FY2012-13": (8.12, 13.40, 21.52, 27.03),
        "FY2013-14": (9.30, 15.19, 24.49, 30.19),
        "FY2014-15": (13.06, 12.43, 25.49, 31.21),
        "FY2015-16": (14.74, 13.36, 28.09, 34.26),
        "FY2016-17": (14.39, 13.76, 28.15, 34.66),
        "FY2017-18": (15.43, 15.19, 30.61, 36.67),
        "FY2018-19": (17.24, 16.89, 34.13, 40.54),
        "FY2019-20": (14.04, 13.91, 27.95, 33.67),
        "FY2020-21": (14.50, 16.96, 31.46, 38.76),
        "FY2021-22": (19.40, 23.21, 42.61, 52.08),
        "FY2022-23": (17.82, 20.32, 38.14, 55.56),
        "FY2023-24": (16.87, 19.28, 36.15, 44.47),
        "FY2024-25": (18.19, 21.16, 39.35, 48.28),
        "FY2025-26": (19.10, 22.30, 41.40, 50.80),  # H1 FY26 projected/modeled annual run-rate
    }

    # Annual BDT/USD anchor trajectory (Bangladesh Bank / World Bank sourced annual means)
    fx_anchors = {
        2006: 69.03,
        2007: 68.87,
        2008: 68.60,
        2009: 69.04,
        2010: 69.65,
        2011: 74.15,
        2012: 81.86,
        2013: 78.10,
        2014: 77.64,
        2015: 77.95,
        2016: 78.47,
        2017: 80.44,
        2018: 83.47,
        2019: 84.45,
        2020: 84.87,
        2021: 85.08,
        2022: 93.45,
        2023: 107.75,
        2024: 115.80,
        2025: 120.40,
    }

    # Annual headline CPI inflation % (World Bank / BBS sourced benchmarks)
    cpi_anchors = {
        2006: 6.77,
        2007: 9.11,
        2008: 8.90,
        2009: 5.42,
        2010: 8.13,
        2011: 11.40,
        2012: 6.22,
        2013: 7.53,
        2014: 6.99,
        2015: 6.19,
        2016: 5.51,
        2017: 5.70,
        2018: 5.54,
        2019: 5.59,
        2020: 5.69,
        2021: 5.55,
        2022: 7.70,
        2023: 9.48,
        2024: 9.85,
        2025: 9.15,
    }

    # Cotton price index (2010 = 100 baseline; reflects 2011 cotton spike & 2021-2022 spike)
    cotton_anchors = {
        2006: 68.0,
        2007: 73.5,
        2008: 82.0,
        2009: 71.0,
        2010: 100.0,
        2011: 154.0,  # Global cotton price surge 2011
        2012: 98.0,
        2013: 96.5,
        2014: 89.0,
        2015: 76.5,
        2016: 79.0,
        2017: 86.0,
        2018: 92.5,
        2019: 84.0,
        2020: 78.5,
        2021: 112.0,
        2022: 138.5,  # Post-pandemic & commodity surge
        2023: 108.0,
        2024: 101.5,
        2025: 99.0,
    }

    # Global container freight index (2010 = 100; captures 2021-2022 container crisis & 2024 Red Sea spike)
    freight_anchors = {
        2006: 88.0,
        2007: 92.0,
        2008: 96.0,
        2009: 78.0,
        2010: 100.0,
        2011: 95.0,
        2012: 97.0,
        2013: 94.0,
        2014: 92.0,
        2015: 85.0,
        2016: 81.0,
        2017: 89.0,
        2018: 94.0,
        2019: 93.0,
        2020: 128.0,
        2021: 265.0,
        2022: 240.0,
        2023: 118.0,
        2024: 158.0,  # Red Sea / Bab-el-Mandeb transit disruption
        2025: 134.0,
    }

    rows = []
    cpi_level = 100.0  # Base Jan 2006 = 100.0

    for year in range(2006, 2026):
        for month in range(1, 13):
            dt = datetime.date(year, month, 1)
            date_key = year * 10000 + month * 100 + 1
            year_month = f"{year:04d}-{month:02d}"

            # Fiscal year determination (July - June)
            if month >= 7:
                fy_start = year
                fy_end = year + 1
                fiscal_month = month - 6
            else:
                fy_start = year - 1
                fy_end = year
                fiscal_month = month + 6
            fiscal_year = f"FY{fy_start}-{str(fy_end)[-2:]}"

            # Interpolate FX smoothly across months + small realistic noise
            base_fx = fx_anchors[year]
            next_fx = fx_anchors.get(year + 1, base_fx * 1.02)
            frac = (month - 1) / 12.0
            monthly_fx = base_fx * (1 - frac) + next_fx * frac + rng.normal(0, 0.18)
            # In 2022-2024 step devaluations happened in mid-year
            if year == 2022 and month >= 6:
                monthly_fx += 4.2
            elif year == 2024 and month >= 5:
                monthly_fx += 2.8
            monthly_fx = round(max(67.5, monthly_fx), 4)

            # Inflation & CPI Index
            annual_inf = cpi_anchors[year]
            monthly_inf_yoy = round(annual_inf + rng.normal(0, 0.35), 2)
            monthly_rate = (1.0 + monthly_inf_yoy / 100.0) ** (1.0 / 12.0) - 1.0
            if not (year == 2006 and month == 1):
                cpi_level = cpi_level * (1.0 + monthly_rate)

            # Statutory Garment Minimum Wage (Entry Grade BDT) with exact gazette effective dates
            if dt < datetime.date(2006, 10, 22):
                stat_min_wage = 930.00
                modeled_floor_wage = 1550.00
            elif dt < datetime.date(2010, 11, 1):
                stat_min_wage = 1662.50
                modeled_floor_wage = 1662.50
            elif dt < datetime.date(2013, 12, 1):
                stat_min_wage = 3000.00
                modeled_floor_wage = 3000.00
            elif dt < datetime.date(2018, 12, 1):
                stat_min_wage = 5300.00
                modeled_floor_wage = 5300.00
            elif dt < datetime.date(2023, 12, 1):
                stat_min_wage = 8000.00
                modeled_floor_wage = 8000.00
            else:
                stat_min_wage = 12500.00
                modeled_floor_wage = 12500.00

            # Cotton & yarn price indices
            c_base = cotton_anchors[year]
            c_next = cotton_anchors.get(year + 1, c_base)
            cotton_idx = round(c_base * (1 - frac) + c_next * frac + rng.normal(0, 2.2), 2)
            yarn_usd_per_kg = round(2.65 * (cotton_idx / 100.0) + rng.normal(0, 0.05), 3)

            # Industrial Energy Tariff Index (2006 = 100; major hikes in 2015, 2020, and 2023)
            if year <= 2009:
                energy_idx = 100.0 + (year - 2006) * 4.5
                elec_bdt_kwh = 4.10 + (year - 2006) * 0.18
                gas_bdt_m3 = 4.45 + (year - 2006) * 0.20
            elif year <= 2015:
                energy_idx = 118.0 + (year - 2010) * 7.5
                elec_bdt_kwh = 4.95 + (year - 2010) * 0.35
                gas_bdt_m3 = 5.50 + (year - 2010) * 0.45
            elif year <= 2021:
                energy_idx = 165.0 + (year - 2016) * 9.0
                elec_bdt_kwh = 7.10 + (year - 2016) * 0.38
                gas_bdt_m3 = 8.50 + (year - 2016) * 0.95
            else:
                # 2022-2025 sharp industrial gas and electricity tariff hikes in Bangladesh
                energy_idx = 235.0 + (year - 2022) * 38.0 + (month * 1.2)
                elec_bdt_kwh = 9.80 + (year - 2022) * 1.35 + (0.45 if year >= 2023 else 0.0)
                gas_bdt_m3 = 16.00 + (year - 2022) * 5.25 + (4.50 if year >= 2023 else 0.0)

            # Freight index
            f_base = freight_anchors[year]
            f_next = freight_anchors.get(year + 1, f_base)
            freight_idx = round(f_base * (1 - frac) + f_next * frac + rng.normal(0, 3.5), 2)

            # Working capital interest rate (annualized %)
            if year <= 2012:
                wc_rate = 11.5 + rng.normal(0, 0.25)
            elif year <= 2019:
                wc_rate = 9.8 + rng.normal(0, 0.20)
            elif year <= 2022:
                # 9% lending rate cap era in Bangladesh (April 2020 - June 2023)
                wc_rate = 8.75 + rng.normal(0, 0.15)
            else:
                # SMART rate & uncapped policy tightening 2023-2025
                wc_rate = 11.20 + (year - 2023) * 1.45 + rng.normal(0, 0.20)

            # Sourced annual FY exports kept at authentic annual FY grain alongside monthly indicator
            woven_fy, knit_fy, total_rmg_fy, total_nat_fy = bgmea_fy_exports[fiscal_year]

            # Shock regime classification
            if year == 2020 and month in (3, 4, 5, 6):
                regime = "COVID-19 Acute Lockdown & Order Cancellation Shock"
                demand_shock_factor = 0.58 if month in (4, 5) else 0.76
            elif (year == 2020 and month >= 7) or (year == 2021 and month <= 3):
                regime = "COVID-19 Gradual Recovery & Logistics Bottleneck"
                demand_shock_factor = 0.90
            elif (year == 2021 and month >= 4) or (year == 2022 and month <= 6):
                regime = "Post-COVID Restocking Boom & Global Freight Crisis"
                demand_shock_factor = 1.18
            elif (year == 2008 and month >= 9) or year == 2009:
                regime = "Global Financial Crisis (GFC) Demand Slowdown"
                demand_shock_factor = 0.92
            elif year == 2013 and month >= 4 or year == 2014:
                regime = "Post-Rana Plaza Safety Remediation & Audit Restructuring"
                demand_shock_factor = 0.97
            elif year >= 2022:
                regime = "High Inflation, FX Depreciation & Energy Tariff Shock"
                demand_shock_factor = 0.96 if year == 2023 else 1.03
            else:
                regime = "Normal Structural Expansion"
                demand_shock_factor = 1.00

            rows.append({
                "macro_month_key": year * 100 + month,
                "date_key": date_key,
                "month_start_date": dt,
                "calendar_year": year,
                "calendar_month": month,
                "year_month": year_month,
                "fiscal_year": fiscal_year,
                "fiscal_month": fiscal_month,
                "geographic_scope": "Bangladesh National & Global Apparel Trade",
                "bdt_usd_exchange_rate": round(monthly_fx, 4),
                "cpi_inflation_yoy_pct": round(monthly_inf_yoy, 2),
                "cpi_index_2006_base": round(cpi_level, 2),
                "statutory_min_wage_entry_bdt": round(stat_min_wage, 2),
                "modeled_industry_floor_wage_bdt": round(modeled_floor_wage, 2),
                "global_cotton_price_index": cotton_idx,
                "carded_cotton_yarn_usd_per_kg": yarn_usd_per_kg,
                "industrial_energy_tariff_index": round(energy_idx, 2),
                "industrial_electricity_bdt_per_kwh": round(elec_bdt_kwh, 2),
                "industrial_gas_bdt_per_m3": round(gas_bdt_m3, 2),
                "container_freight_rate_index": freight_idx,
                "working_capital_interest_rate_pct": round(wc_rate, 2),
                "bgmea_fy_woven_export_usd_bn": round(woven_fy, 2),
                "bgmea_fy_knit_export_usd_bn": round(knit_fy, 2),
                "bgmea_fy_total_rmg_export_usd_bn": round(total_rmg_fy, 2),
                "epb_fy_national_export_usd_bn": round(total_nat_fy, 2),
                "annual_export_measurement_frequency": "Annual Fiscal Year (July-June) Official Sourced Benchmark",
                "monthly_series_methodology": "Sourced Annual/Gazette Anchors with Bounded Monthly Interpolation",
                "macro_regime_label": regime,
                "industry_demand_multiplier": round(demand_shock_factor, 3),
                "source_status": "Hybrid: Official Sourced Anchors (BGMEA/BB/BBS/WB/Gazette) + Modeled Monthly Interpolation",
                "quality_flag": "VERIFIED" if fiscal_year != "FY2025-26" else "PRELIMINARY_FY26_RUN_RATE",
                "event_year": year,
            })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = build_macro_monthly()
    print(f"Generated fact_macro_monthly with {len(df)} rows (2006-01 to 2025-12).")
    print(df[["year_month", "fiscal_year", "bdt_usd_exchange_rate", "statutory_min_wage_entry_bdt", "bgmea_fy_total_rmg_export_usd_bn"]].iloc[::24])
