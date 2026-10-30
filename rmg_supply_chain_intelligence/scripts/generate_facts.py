"""
generate_facts.py
Generates all transactional and periodic snapshot fact tables (plus dim_order_line) for the
20-year Bangladesh RMG Supply Chain Intelligence dataset (2006-01-01 to 2025-12-31).

Vectorized NumPy/Pandas implementation with strict supply-chain reconciliation:
1. fact_sales_order_line & dim_order_line (~240,000 rows)
2. fact_purchase_order_line (~250,000 rows)
3. fact_supplier_delivery (~285,000 rows)
4. fact_production_batch (~290,000 rows)
5. fact_material_consumption (~580,000 rows)
6. fact_quality_inspection (~290,000 rows)
7. fact_shipment_line (~255,000 rows)
8. fact_inventory_snapshot_monthly (~265,000 rows)
7. fact_workforce_monthly (~45,000 rows)
10. fact_sustainability_monthly (~5,200 rows)
11. fact_cost_transaction (~260,000 rows)
12. fact_macro_monthly (240 rows)
"""

import time
import datetime
import numpy as np
import pandas as pd

from generate_macro_context import build_macro_monthly
from generate_dimensions import generate_all_dimensions

SEED = 20261026
MIN_DATE = datetime.date(2006, 1, 1)
MAX_DATE = datetime.date(2025, 12, 31)
MIN_ORD = MIN_DATE.toordinal()
MAX_ORD = MAX_DATE.toordinal()


def ordinals_to_dates_and_keys(ordinals: np.ndarray) -> tuple[pd.Series, np.ndarray]:
    """Convert integer proleptic Gregorian ordinals (clamped to 2006-01-01..2025-12-31) to Python dates and YYYYMMDD keys."""
    clipped = np.clip(ordinals, MIN_ORD, MAX_ORD)
    # Build lookup array for the 7,305 days once
    base_dates = [MIN_DATE + datetime.timedelta(days=i) for i in range(MAX_ORD - MIN_ORD + 1)]
    base_keys = np.array([d.year * 10000 + d.month * 100 + d.day for d in base_dates], dtype=np.int64)
    idx = clipped - MIN_ORD
    date_arr = np.array(base_dates, dtype=object)[idx]
    key_arr = base_keys[idx]
    return pd.Series(date_arr), key_arr


def generate_sales_and_order_lines(
    dims: dict[str, pd.DataFrame],
    df_macro: pd.DataFrame,
    target_rows: int = 240000,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed + 100)
    df_comp = dims["dim_company"]
    df_fac = dims["dim_factory"]
    df_buyer = dims["dim_buyer"]
    df_prod = dims["dim_product"]
    df_date = dims["dim_date"]

    # Map macro monthly growth & FX
    macro_map = df_macro.set_index(["calendar_year", "calendar_month"])

    # Determine monthly order line counts across the 240 months (2006-01 to 2025-12)
    # Reflects Bangladesh RMG export trajectory: rising from ~650 order lines/month in 2006 to ~1,350/month in 2022-2025
    month_weights = []
    ym_list = []
    for yr in range(2006, 2026):
        # Secular industry expansion curve
        yr_progress = (yr - 2006) / 19.0
        base_yr_w = 0.58 + 0.84 * (yr_progress ** 0.85)
        for mo in range(1, 13):
            m_row = macro_map.loc[(yr, mo)]
            shk = float(m_row["industry_demand_multiplier"])
            # Seasonal order booking peaks in Jan-Mar and Jul-Oct
            seas = 1.12 if mo in (1, 2, 3, 7, 8, 9, 10) else (0.88 if mo in (4, 5, 12) else 0.96)
            w = base_yr_w * shk * seas
            month_weights.append(w)
            ym_list.append((yr, mo))

    month_weights = np.array(month_weights, dtype=np.float64)
    month_weights /= month_weights.sum()
    month_counts = np.round(month_weights * target_rows).astype(int)
    diff = target_rows - int(month_counts.sum())
    month_counts[-1] += diff

    # Pre-group factories and products by company archetype compatibility
    # Map each company to compatible product categories
    comp_prod_map = {
        1: df_prod[df_prod["knit_woven_classification"] == "Knit"]["product_key"].to_numpy(),
        2: df_prod[df_prod["product_category"].isin(["Woven Shirts", "Woven Bottoms"])]["product_key"].to_numpy(),
        3: df_prod[df_prod["product_category"].isin(["Denim Apparel", "Woven Bottoms"])]["product_key"].to_numpy(),
        4: df_prod[df_prod["product_category"].isin(["Knit Tops", "Knit Fleece & Hoodies"])]["product_key"].to_numpy(),
        5: df_prod[df_prod["product_category"].isin(["Denim Apparel", "Woven Bottoms"])]["product_key"].to_numpy(),
        6: df_prod[df_prod["product_category"] == "Sweaters & Flat-Knit"]["product_key"].to_numpy(),
        7: df_prod[df_prod["product_category"].isin(["MMF Activewear & Outerwear", "Knit Tops"])]["product_key"].to_numpy(),
        8: df_prod[df_prod["value_tier"] == "Basic Volume"]["product_key"].to_numpy(),
    }

    # Build lookup arrays from df_prod
    prod_indexed = df_prod.set_index("product_key")
    prod_base_price = prod_indexed["base_fob_unit_price_usd"].to_dict()
    prod_smv = prod_indexed["standard_minute_value_smv"].to_dict()
    prod_cat = prod_indexed["product_category"].to_dict()
    prod_kw = prod_indexed["knit_woven_classification"].to_dict()
    prod_code_map = prod_indexed["product_code"].to_dict()
    prod_intro_yr = {k: v.year for k, v in prod_indexed["introduction_date"].to_dict().items()}
    prod_disc_yr = {k: v.year for k, v in prod_indexed["discontinuation_date"].to_dict().items()}

    # Buyer lookup
    buyer_indexed = df_buyer.set_index("buyer_key")
    buyer_start_yr = {k: v.year for k, v in buyer_indexed["relationship_start_date"].to_dict().items()}
    buyer_weights_base = buyer_indexed["demand_share_weight"].to_numpy()
    buyer_keys_all = df_buyer["buyer_key"].to_numpy()
    buyer_country_map = buyer_indexed["destination_country"].to_dict()
    buyer_terms_map = buyer_indexed["payment_terms"].to_dict()

    # Factory lookup
    fac_open_ord = {r["factory_key"]: r["opening_date"].toordinal() for _, r in df_fac.iterrows()}
    fac_close_ord = {r["factory_key"]: r["closure_date"].toordinal() for _, r in df_fac.iterrows()}
    fac_comp_map = {r["factory_key"]: r["company_key"] for _, r in df_fac.iterrows()}
    fac_cap_map = {r["factory_key"]: r["base_monthly_capacity_pcs"] for _, r in df_fac.iterrows()}

    all_chunks = []
    order_line_counter = 1
    order_header_counter = 100001

    for (yr, mo), n_lines in zip(ym_list, month_counts):
        if n_lines <= 0:
            continue

        m_row = macro_map.loc[(yr, mo)]
        fx_rate = float(m_row["bdt_usd_exchange_rate"])
        cpi_idx = float(m_row["cpi_index_2006_base"])
        fy_str = str(m_row["fiscal_year"])
        fy_mo = int(m_row["fiscal_month"])

        # Days in this month
        m_start = datetime.date(yr, mo, 1)
        if mo == 12:
            m_end = datetime.date(yr, 12, 31)
        else:
            m_end = datetime.date(yr, mo + 1, 1) - datetime.timedelta(days=1)
        m_start_ord = m_start.toordinal()
        m_end_ord = m_end.toordinal()

        # Random order dates within month
        ord_ordinals = rng.integers(m_start_ord, m_end_ord + 1, size=n_lines)

        # Active factories in this month
        active_facs = [
            fk for fk in fac_open_ord
            if fac_open_ord[fk] <= m_start_ord and fac_close_ord[fk] >= m_end_ord
        ]
        fac_weights = np.array([fac_cap_map[fk] for fk in active_facs], dtype=np.float64)
        # Adjust seasonal factory weight for Sweater company (comp 6 peaks in Mar-Aug order booking for AW delivery)
        for idx_f, fk in enumerate(active_facs):
            if fac_comp_map[fk] == 6:
                fac_weights[idx_f] *= (1.55 if mo in (3, 4, 5, 6, 7, 8) else 0.55)
        fac_weights /= fac_weights.sum()

        chosen_facs = rng.choice(active_facs, size=n_lines, p=fac_weights)
        chosen_comps = np.array([fac_comp_map[fk] for fk in chosen_facs], dtype=np.int64)

        # Active buyers in this year
        valid_b_mask = np.array([buyer_start_yr[bk] <= yr for bk in buyer_keys_all])
        valid_b_keys = buyer_keys_all[valid_b_mask]
        valid_b_w = buyer_weights_base[valid_b_mask].copy()
        valid_b_w /= valid_b_w.sum()
        chosen_buyers = rng.choice(valid_b_keys, size=n_lines, p=valid_b_w)

        # Choose product for each line based on company specialization & active product dates
        chosen_prods = np.zeros(n_lines, dtype=np.int64)
        for comp_id in np.unique(chosen_comps):
            c_mask = chosen_comps == comp_id
            cand_prods = [
                pk for pk in comp_prod_map[comp_id]
                if prod_intro_yr[pk] <= yr and prod_disc_yr[pk] >= yr
            ]
            if not cand_prods:
                cand_prods = list(comp_prod_map[comp_id])
            chosen_prods[c_mask] = rng.choice(cand_prods, size=int(c_mask.sum()))

        # Lead time requested by buyer (45 to 105 days; capped so delivery falls inside 2006..2025)
        req_lead_days = rng.integers(42, 98, size=n_lines)
        req_deliv_ordinals = np.minimum(ord_ordinals + req_lead_days, MAX_ORD - 5)
        # Ensure requested delivery is at least 18 days after order date
        ord_ordinals = np.minimum(ord_ordinals, req_deliv_ordinals - 18)

        # Order quantities (pieces): log-normal distribution realistic for RMG order lines (1,200 to 45,000 pcs)
        base_qty = rng.lognormal(mean=8.55, sigma=0.62, size=n_lines)
        # Round to nearest 50 pieces
        ordered_qty = np.clip((np.round(base_qty / 50.0) * 50).astype(np.int64), 600, 65000)

        # Unit price USD: base style price * historical price evolution (slight deflation 2014-2019, inflation 2021-2025)
        price_evo = 0.86 + 0.14 * ((yr - 2006) / 19.0) + (0.06 if yr >= 2022 else 0.0)
        base_p_arr = np.array([prod_base_price[pk] for pk in chosen_prods], dtype=np.float64)
        unit_price_usd = np.round(base_p_arr * price_evo * rng.uniform(0.93, 1.08, size=n_lines), 2)

        # Discounts (higher during 2008-09 GFC and 2020 COVID shock)
        disc_prob = 0.35 if (yr in (2008, 2009, 2020)) else 0.18
        has_disc = rng.random(n_lines) < disc_prob
        disc_pct = np.where(has_disc, np.round(rng.uniform(0.015, 0.065, size=n_lines), 4), 0.0)

        gross_usd = np.round(ordered_qty * unit_price_usd, 2)
        disc_usd = np.round(gross_usd * disc_pct, 2)
        net_usd = np.round(gross_usd - disc_usd, 2)
        net_bdt = np.round(net_usd * fx_rate, 2)

        # Order status: Completed / Shipped in Full, Partially Shipped, Amended (+5%..10%), or Cancelled
        cancel_prob = 0.024
        if yr == 2020 and mo in (3, 4, 5):
            cancel_prob = 0.165  # COVID-19 order cancellation wave
        elif yr in (2008, 2009):
            cancel_prob = 0.048
        elif yr in (2022, 2023):
            cancel_prob = 0.036

        u_stat = rng.random(n_lines)
        is_cancelled = u_stat < cancel_prob
        is_amended = (~is_cancelled) & (u_stat < (cancel_prob + 0.055))
        is_partial = (~is_cancelled) & (~is_amended) & (u_stat < (cancel_prob + 0.135))

        amend_mult = np.where(is_amended, rng.choice([0.90, 1.05, 1.10], size=n_lines), 1.0)
        eligible_qty = np.where(
            is_cancelled,
            0,
            np.round(ordered_qty * amend_mult).astype(np.int64)
        )

        status_arr = np.where(
            is_cancelled,
            "Cancelled",
            np.where(
                is_amended,
                "Amended & Fulfilled",
                np.where(is_partial, "Partially Shipped", "Fulfilled")
            )
        )

        # Group every ~2.2 lines into a Sales Order Header ID
        n_headers = max(1, int(round(n_lines / 2.2)))
        header_ids = [f"SO-{yr}-{order_header_counter + h:06d}" for h in range(n_headers)]
        order_header_counter += n_headers
        assigned_headers = [header_ids[i % n_headers] for i in range(n_lines)]

        line_keys = np.arange(order_line_counter, order_line_counter + n_lines, dtype=np.int64)
        order_line_counter += n_lines

        chunk_df = pd.DataFrame({
            "order_line_key": line_keys,
            "sales_order_id": assigned_headers,
            "order_line_number": [(i % 5) + 1 for i in range(n_lines)],
            "order_date_ordinal": ord_ordinals,
            "req_deliv_ordinal": req_deliv_ordinals,
            "calendar_year": yr,
            "calendar_month": mo,
            "calendar_quarter": ((mo - 1) // 3) + 1,
            "fiscal_year": fy_str,
            "fiscal_month": fy_mo,
            "company_key": chosen_comps,
            "factory_key": chosen_facs,
            "buyer_key": chosen_buyers,
            "product_key": chosen_prods,
            "ordered_qty_pcs": ordered_qty,
            "amended_order_qty_pcs": eligible_qty,
            "unit_price_usd": unit_price_usd,
            "currency_code": "USD",
            "bdt_usd_exchange_rate": round(fx_rate, 4),
            "gross_order_value_usd": gross_usd,
            "discount_rate": disc_pct,
            "discount_amount_usd": disc_usd,
            "net_order_value_usd": net_usd,
            "net_order_value_bdt": net_bdt,
            "order_status": status_arr,
            "is_cancelled": is_cancelled,
            "is_amended": is_amended,
            "is_partial_fulfilment": is_partial,
            "event_year": yr,
        })
        all_chunks.append(chunk_df)

    df_so = pd.concat(all_chunks, ignore_index=True)
    df_so["order_date"], df_so["order_date_key"] = ordinals_to_dates_and_keys(df_so["order_date_ordinal"].to_numpy())
    df_so["requested_delivery_date"], df_so["requested_delivery_date_key"] = ordinals_to_dates_and_keys(df_so["req_deliv_ordinal"].to_numpy())

    # Delivery terms & incoterms
    incoterms_pool = np.array(["FOB Chattogram", "FOB Chattogram", "FOB Chattogram", "FCA Dhaka Airport", "CIF Destination Port"])
    df_so["incoterm"] = incoterms_pool[df_so["order_line_key"].to_numpy() % len(incoterms_pool)]

    # Build dim_order_line (conformed bridge dimension connecting sales order lines, production batches, and shipment lines)
    dim_order_line = pd.DataFrame({
        "order_line_key": df_so["order_line_key"],
        "sales_order_id": df_so["sales_order_id"],
        "order_line_code": [f"OL-{k:06d}" for k in df_so["order_line_key"]],
        "company_key": df_so["company_key"],
        "factory_key": df_so["factory_key"],
        "buyer_key": df_so["buyer_key"],
        "product_key": df_so["product_key"],
        "order_date": df_so["order_date"],
        "requested_delivery_date": df_so["requested_delivery_date"],
        "order_status": df_so["order_status"],
        "incoterm": df_so["incoterm"],
        "destination_country": [buyer_country_map[bk] for bk in df_so["buyer_key"]],
        "payment_terms": [buyer_terms_map[bk] for bk in df_so["buyer_key"]],
        "knit_woven_classification": [prod_kw[pk] for pk in df_so["product_key"]],
        "product_category": [prod_cat[pk] for pk in df_so["product_key"]],
    })

    return df_so, dim_order_line


def generate_production_and_quality_and_shipments(
    df_so: pd.DataFrame,
    dims: dict[str, pd.DataFrame],
    df_macro: pd.DataFrame,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generates synchronized:
    - fact_production_batch
    - fact_material_consumption
    - fact_quality_inspection
    - fact_shipment_line
    And updates df_so with reconciled shipped_qty_pcs and backlog_qty_pcs.
    """
    rng = np.random.default_rng(seed + 200)
    df_prod = dims["dim_product"].set_index("product_key")
    df_fac = dims["dim_factory"].set_index("factory_key")
    df_line = dims["dim_factory_line"]
    df_mat = dims["dim_material"].set_index("material_key")
    df_buyer = dims["dim_buyer"].set_index("buyer_key")
    macro_map = df_macro.set_index(["calendar_year", "calendar_month"])

    # Filter non-cancelled order lines for production
    active_so = df_so[~df_so["is_cancelled"]].copy().reset_index(drop=True)
    n_active = len(active_so)

    # Decide which orders split across 2 batches (~26% of active orders) so total batches ~ 285,000
    split_mask = (active_so["amended_order_qty_pcs"].to_numpy() >= 9000) & (rng.random(n_active) < 0.48)

    so_part1 = active_so.copy()
    so_part1["batch_seq"] = 1
    so_part1["batch_share"] = np.where(split_mask, 0.55, 1.0)

    so_part2 = active_so[split_mask].copy()
    so_part2["batch_seq"] = 2
    so_part2["batch_share"] = 0.45

    batches_raw = pd.concat([so_part1, so_part2], ignore_index=True)
    batches_raw.sort_values(["order_line_key", "batch_seq"], inplace=True)
    batches_raw.reset_index(drop=True, inplace=True)
    n_batches = len(batches_raw)

    batch_keys = np.arange(1, n_batches + 1, dtype=np.int64)
    batches_raw["production_batch_key"] = batch_keys
    batches_raw["batch_id"] = [f"BAT-{yr}-{bk:06d}" for yr, bk in zip(batches_raw["calendar_year"], batch_keys)]

    # Assign production_line_key belonging to each factory_key
    fac_lines_map = df_line.groupby("factory_key")["production_line_key"].apply(np.array).to_dict()
    fac_arr = batches_raw["factory_key"].to_numpy()
    line_keys_assigned = np.zeros(n_batches, dtype=np.int64)
    for fk, l_arr in fac_lines_map.items():
        m = fac_arr == fk
        if m.any():
            line_keys_assigned[m] = rng.choice(l_arr, size=int(m.sum()))
    batches_raw["production_line_key"] = line_keys_assigned

    # Planned vs Actual Production Dates (respecting order_date <= planned_start <= actual_start <= actual_completion <= requested_delivery)
    ord_ord = batches_raw["order_date_ordinal"].to_numpy()
    req_ord = batches_raw["req_deliv_ordinal"].to_numpy()
    span = np.maximum(18, req_ord - ord_ord)

    # Batch 1 starts ~35% into lead window; Batch 2 starts ~48% into lead window
    start_offset = np.where(
        batches_raw["batch_seq"].to_numpy() == 1,
        (span * rng.uniform(0.28, 0.45, size=n_batches)).astype(int),
        (span * rng.uniform(0.42, 0.58, size=n_batches)).astype(int),
    )
    planned_start_ord = np.minimum(ord_ord + np.maximum(5, start_offset), MAX_ORD - 12)
    prod_duration_planned = rng.integers(5, 16, size=n_batches)
    planned_comp_ord = np.minimum(planned_start_ord + prod_duration_planned, MAX_ORD - 4)

    # Actual start delay (material shortage, power outage, COVID disruption, line changeover)
    yr_arr = batches_raw["calendar_year"].to_numpy()
    mo_arr = batches_raw["calendar_month"].to_numpy()
    fac_eff_arr = df_fac["base_efficiency_factor"].reindex(fac_arr).to_numpy()

    delay_prob = 0.22 + (0.88 - fac_eff_arr) * 0.8
    delay_prob = np.where((yr_arr == 2020) & np.isin(mo_arr, [3, 4, 5, 6]), delay_prob + 0.35, delay_prob)
    delay_prob = np.where(yr_arr >= 2022, delay_prob + 0.06, delay_prob)  # Gas/load-shedding delays 2022-24
    has_start_delay = rng.random(n_batches) < np.clip(delay_prob, 0.08, 0.75)
    start_delay_days = np.where(has_start_delay, rng.integers(1, 12, size=n_batches), 0)

    actual_start_ord = np.minimum(planned_start_ord + start_delay_days, MAX_ORD - 8)
    actual_duration = np.maximum(3, prod_duration_planned + rng.integers(-1, 5, size=n_batches))
    actual_comp_ord = np.minimum(actual_start_ord + actual_duration, MAX_ORD - 2)
    # Guarantee actual_start_ord <= actual_comp_ord
    actual_start_ord = np.minimum(actual_start_ord, actual_comp_ord - 2)

    # Quantities: Planned vs Actual Good Output vs Rework vs Scrap/Reject
    target_order_qty = batches_raw["amended_order_qty_pcs"].to_numpy()
    is_part_order = batches_raw["is_partial_fulfilment"].to_numpy()
    share_arr = batches_raw["batch_share"].to_numpy()

    planned_batch_qty = np.maximum(100, np.round(target_order_qty * share_arr).astype(np.int64))
    # Ensure for split batches that Batch 1 + Batch 2 planned_batch_qty equals target_order_qty exactly
    is_b2 = batches_raw["batch_seq"].to_numpy() == 2
    if is_b2.any():
        b2_idx = np.where(is_b2)[0]
        b1_idx = b2_idx - 1
        planned_batch_qty[b1_idx] = np.round(target_order_qty[b1_idx] * 0.55).astype(np.int64)
        planned_batch_qty[b2_idx] = target_order_qty[b2_idx] - planned_batch_qty[b1_idx]

    # For partial fulfilment orders, actual good output is 75%..92% of planned; for full orders, 100% of planned_batch_qty
    fulfil_ratio = np.where(is_part_order, rng.uniform(0.75, 0.92, size=n_batches), 1.00)
    actual_good_output = np.minimum(planned_batch_qty, np.maximum(50, np.round(planned_batch_qty * fulfil_ratio).astype(np.int64)))

    # Complexity & historical quality trajectory
    prod_keys_b = batches_raw["product_key"].to_numpy()
    smv_arr = df_prod["standard_minute_value_smv"].reindex(prod_keys_b).to_numpy()
    comp_tier_arr = df_prod["manufacturing_complexity"].reindex(prod_keys_b).to_numpy()

    base_defect_rate = np.where(
        comp_tier_arr == "Very High", 0.052,
        np.where(comp_tier_arr == "High", 0.041,
                 np.where(comp_tier_arr == "Medium-High", 0.035,
                          np.where(comp_tier_arr == "Medium", 0.029, 0.023)))
    )
    # Historical improvement from lean/automation, offset when overtime/delay pressure is high
    yr_improvement = np.clip(1.08 - 0.014 * (yr_arr - 2006), 0.76, 1.10)
    fac_quality_mod = np.clip(1.0 + (0.85 - fac_eff_arr) * 2.2, 0.72, 1.45)
    pressure_bump = np.where(has_start_delay, 1.18, 1.00)

    batch_defect_rate = np.clip(
        base_defect_rate * yr_improvement * fac_quality_mod * pressure_bump * rng.uniform(0.75, 1.30, size=n_batches),
        0.006, 0.145
    )

    # Inspected quantity is 100% of finished garment output (end-line 100% check + AQL final audit)
    gross_produced_pcs = np.round(actual_good_output / (1.0 - batch_defect_rate * 0.22)).astype(np.int64)
    defective_pcs = np.maximum(1, np.round(gross_produced_pcs * batch_defect_rate).astype(np.int64))
    # Roughly 78% of defective garments are successfully reworked; 22% are rejected/seconds
    rework_pcs = np.round(defective_pcs * rng.uniform(0.72, 0.85, size=n_batches)).astype(np.int64)
    rejected_pcs = np.maximum(0, defective_pcs - rework_pcs)

    # Standard minutes & actual labour hours
    earned_standard_minutes = np.round(actual_good_output * smv_arr, 1)
    earned_standard_hours = earned_standard_minutes / 60.0
    # Line efficiency = fac_eff_arr + secular improvement + noise
    realized_line_eff = np.clip(
        fac_eff_arr + 0.0035 * (yr_arr - 2006) + rng.normal(0, 0.035, size=n_batches),
        0.48, 0.96
    )
    actual_labour_hours = np.round(earned_standard_hours / realized_line_eff, 1)
    actual_line_hours = np.round(actual_labour_hours / 48.0, 1)  # ~48 operators/helpers per line
    downtime_hours = np.round(np.where(has_start_delay, rng.uniform(2.5, 14.0, size=n_batches), rng.uniform(0.2, 3.0, size=n_batches)), 1)

    p_start_dt, p_start_key = ordinals_to_dates_and_keys(planned_start_ord)
    a_start_dt, a_start_key = ordinals_to_dates_and_keys(actual_start_ord)
    p_comp_dt, p_comp_key = ordinals_to_dates_and_keys(planned_comp_ord)
    a_comp_dt, a_comp_key = ordinals_to_dates_and_keys(actual_comp_ord)

    fact_production_batch = pd.DataFrame({
        "production_batch_key": batch_keys,
        "batch_id": batches_raw["batch_id"],
        "order_line_key": batches_raw["order_line_key"],
        "company_key": batches_raw["company_key"],
        "factory_key": fac_arr,
        "production_line_key": line_keys_assigned,
        "product_key": prod_keys_b,
        "planned_start_date_key": p_start_key,
        "planned_start_date": p_start_dt,
        "actual_start_date_key": a_start_key,
        "actual_start_date": a_start_dt,
        "planned_completion_date_key": p_comp_key,
        "planned_completion_date": p_comp_dt,
        "actual_completion_date_key": a_comp_key,
        "actual_completion_date": a_comp_dt,
        "planned_qty_pcs": planned_batch_qty,
        "gross_produced_qty_pcs": gross_produced_pcs,
        "actual_good_output_pcs": actual_good_output,
        "rework_qty_pcs": rework_pcs,
        "rejected_scrap_qty_pcs": rejected_pcs,
        "standard_minute_value_smv": smv_arr,
        "earned_standard_minutes": earned_standard_minutes,
        "actual_production_line_hours": actual_line_hours,
        "actual_labour_hours": actual_labour_hours,
        "machine_downtime_hours": downtime_hours,
        "line_efficiency_pct": np.round(realized_line_eff * 100.0, 2),
        "schedule_delay_days": np.maximum(0, actual_comp_ord - planned_comp_ord),
        "production_status": np.where(is_part_order, "Completed (Short-Shipped)", "Completed in Full"),
        "event_year": pd.to_datetime(a_comp_dt).dt.year.to_numpy(),
    })

    # ---------------------------------------------------------
    # Generate fact_material_consumption (2 rows per batch: Primary Fabric/Yarn + Trims/Packaging Kit)
    # ---------------------------------------------------------
    prim_mat_keys = df_prod["primary_material_key"].reindex(prod_keys_b).to_numpy(dtype=np.int64)
    prim_cons_unit = df_prod["primary_material_consumption_per_unit"].reindex(prod_keys_b).to_numpy(dtype=np.float64)
    prim_base_cost = df_mat["base_unit_cost_usd_2015"].reindex(prim_mat_keys).to_numpy(dtype=np.float64)

    # Wastage rate (fabric cutting/knitting wastage 4.5%..11%, improving slightly over 20 years)
    wastage_pct_1 = np.clip(
        0.078 - 0.0012 * (yr_arr - 2006) + (0.86 - fac_eff_arr) * 0.15 + rng.normal(0, 0.008, size=n_batches),
        0.028, 0.145
    )
    planned_mat_qty_1 = np.round(gross_produced_pcs * prim_cons_unit, 2)
    wastage_qty_1 = np.round(planned_mat_qty_1 * wastage_pct_1, 2)
    actual_mat_qty_1 = np.round(planned_mat_qty_1 + wastage_qty_1, 2)

    fx_b_arr = batches_raw["bdt_usd_exchange_rate"].to_numpy()
    # Material unit cost in USD and BDT
    mat_price_mod = 0.82 + 0.18 * ((yr_arr - 2006) / 19.0) + np.where(yr_arr == 2011, 0.28, 0.0) + np.where(yr_arr == 2022, 0.22, 0.0)
    unit_cost_usd_1 = np.round(prim_base_cost * mat_price_mod * rng.uniform(0.95, 1.06, size=n_batches), 3)
    mat_cost_usd_1 = np.round(actual_mat_qty_1 * unit_cost_usd_1, 2)
    mat_cost_bdt_1 = np.round(mat_cost_usd_1 * fx_b_arr, 2)
    wastage_cost_usd_1 = np.round(wastage_qty_1 * unit_cost_usd_1, 2)
    wastage_cost_bdt_1 = np.round(wastage_cost_usd_1 * fx_b_arr, 2)

    # Secondary material row: Trims & Packaging Kit (material keys 45..64)
    sec_mat_keys = rng.integers(45, 65, size=n_batches, dtype=np.int64)
    sec_base_cost = df_mat["base_unit_cost_usd_2015"].reindex(sec_mat_keys).to_numpy(dtype=np.float64)
    planned_mat_qty_2 = gross_produced_pcs.astype(np.float64)
    wastage_pct_2 = np.clip(rng.normal(0.025, 0.006, size=n_batches), 0.008, 0.055)
    wastage_qty_2 = np.round(planned_mat_qty_2 * wastage_pct_2, 2)
    actual_mat_qty_2 = np.round(planned_mat_qty_2 + wastage_qty_2, 2)
    unit_cost_usd_2 = np.round(sec_base_cost * mat_price_mod, 3)
    mat_cost_usd_2 = np.round(actual_mat_qty_2 * unit_cost_usd_2, 2)
    mat_cost_bdt_2 = np.round(mat_cost_usd_2 * fx_b_arr, 2)
    wastage_cost_usd_2 = np.round(wastage_qty_2 * unit_cost_usd_2, 2)
    wastage_cost_bdt_2 = np.round(wastage_cost_usd_2 * fx_b_arr, 2)

    mc_part1 = pd.DataFrame({
        "production_batch_key": batch_keys,
        "batch_id": batches_raw["batch_id"],
        "company_key": batches_raw["company_key"],
        "factory_key": fac_arr,
        "product_key": prod_keys_b,
        "material_key": prim_mat_keys,
        "consumption_date_key": a_start_key,
        "consumption_date": a_start_dt,
        "planned_material_qty": planned_mat_qty_1,
        "actual_material_qty": actual_mat_qty_1,
        "wastage_qty": wastage_qty_1,
        "wastage_rate_pct": np.round(wastage_pct_1 * 100.0, 2),
        "currency_code": "USD",
        "bdt_usd_exchange_rate": fx_b_arr,
        "unit_cost_usd": unit_cost_usd_1,
        "total_material_cost_usd": mat_cost_usd_1,
        "total_material_cost_bdt": mat_cost_bdt_1,
        "wastage_cost_usd": wastage_cost_usd_1,
        "wastage_cost_bdt": wastage_cost_bdt_1,
        "event_year": pd.to_datetime(a_start_dt).dt.year.to_numpy(),
    })

    mc_part2 = pd.DataFrame({
        "production_batch_key": batch_keys,
        "batch_id": batches_raw["batch_id"],
        "company_key": batches_raw["company_key"],
        "factory_key": fac_arr,
        "product_key": prod_keys_b,
        "material_key": sec_mat_keys,
        "consumption_date_key": a_comp_key,
        "consumption_date": a_comp_dt,
        "planned_material_qty": planned_mat_qty_2,
        "actual_material_qty": actual_mat_qty_2,
        "wastage_qty": wastage_qty_2,
        "wastage_rate_pct": np.round(wastage_pct_2 * 100.0, 2),
        "currency_code": "USD",
        "bdt_usd_exchange_rate": fx_b_arr,
        "unit_cost_usd": unit_cost_usd_2,
        "total_material_cost_usd": mat_cost_usd_2,
        "total_material_cost_bdt": mat_cost_bdt_2,
        "wastage_cost_usd": wastage_cost_usd_2,
        "wastage_cost_bdt": wastage_cost_bdt_2,
        "event_year": pd.to_datetime(a_comp_dt).dt.year.to_numpy(),
    })

    fact_material_consumption = pd.concat([mc_part1, mc_part2], ignore_index=True)
    fact_material_consumption.insert(0, "consumption_key", np.arange(1, len(fact_material_consumption) + 1, dtype=np.int64))

    # ---------------------------------------------------------
    # Generate fact_quality_inspection (1 row per production batch)
    # ---------------------------------------------------------
    defect_categories = np.array([
        "Stitching / Broken or Skipped Stitch",
        "Measurement / Spec Out-of-Tolerance",
        "Fabric Shade Variation / Dye Streak",
        "Oil Stain / Washing & Finishing Spot",
        "Puckering / Seam Twisted or Uneven",
        "Trim / Button / Zipper Attachment Defect",
        "Needle Hole / Fabric Yarn Pull",
    ])
    defect_cat_assigned = defect_categories[rng.integers(0, len(defect_categories), size=n_batches)]
    aql_tol = df_buyer["quality_tolerance_aql"].reindex(batches_raw["buyer_key"].to_numpy()).to_numpy()
    # Pass on first inspection if defect rate <= AQL threshold * 1.6, else Re-inspected after rework
    fpy_pct = np.round((1.0 - batch_defect_rate) * 100.0, 2)
    pass_first_time = (batch_defect_rate * 100.0) <= (aql_tol * 1.85)
    insp_status = np.where(pass_first_time, "Passed First-Time Final AQL", "Passed After Rework & Re-Audit")

    # Quality cost = rework labour + scrap write-off
    rework_cost_usd = np.round(rework_pcs * rng.uniform(0.35, 0.75, size=n_batches) + rejected_pcs * rng.uniform(2.10, 4.80, size=n_batches), 2)
    rework_cost_bdt = np.round(rework_cost_usd * fx_b_arr, 2)

    fact_quality_inspection = pd.DataFrame({
        "inspection_key": batch_keys,
        "inspection_id": [f"INS-{yr}-{bk:06d}" for yr, bk in zip(batches_raw["calendar_year"], batch_keys)],
        "production_batch_key": batch_keys,
        "batch_id": batches_raw["batch_id"],
        "order_line_key": batches_raw["order_line_key"],
        "company_key": batches_raw["company_key"],
        "factory_key": fac_arr,
        "production_line_key": line_keys_assigned,
        "product_key": prod_keys_b,
        "inspection_date_key": a_comp_key,
        "inspection_date": a_comp_dt,
        "inspection_stage": "Final Pre-Shipment AQL & End-Line Summary",
        "inspected_qty_pcs": gross_produced_pcs,
        "defective_qty_pcs": defective_pcs,
        "rework_qty_pcs": rework_pcs,
        "rejected_qty_pcs": rejected_pcs,
        "accepted_qty_pcs": actual_good_output,
        "defect_rate_pct": np.round(batch_defect_rate * 100.0, 2),
        "first_pass_yield_pct": fpy_pct,
        "primary_defect_category": defect_cat_assigned,
        "aql_standard_threshold": aql_tol,
        "passed_first_inspection": pass_first_time,
        "inspection_status": insp_status,
        "currency_code": "USD",
        "bdt_usd_exchange_rate": fx_b_arr,
        "estimated_quality_cost_usd": rework_cost_usd,
        "estimated_quality_cost_bdt": rework_cost_bdt,
        "event_year": pd.to_datetime(a_comp_dt).dt.year.to_numpy(),
    })

    # ---------------------------------------------------------
    # Generate fact_shipment_line (reconciled to actual_good_output and sales order lines)
    # ---------------------------------------------------------
    # Aggregate actual_good_output and max completion date per order_line_key
    batch_agg = batches_raw.assign(
        actual_good_output_pcs=actual_good_output,
        actual_comp_ord=actual_comp_ord,
        had_delay=has_start_delay,
    ).groupby("order_line_key", as_index=False).agg(
        total_produced_good_pcs=("actual_good_output_pcs", "sum"),
        first_batch_comp_ord=("actual_comp_ord", "min"),
        last_batch_comp_ord=("actual_comp_ord", "max"),
        batch_count=("production_batch_key", "count"),
        any_prod_delay=("had_delay", "max"),
    )

    so_ship_base = active_so.merge(batch_agg, on="order_line_key", how="left")
    # Split ~10% of multi-batch orders into 2 partial shipment lines so fact_shipment_line has ~255,000 rows
    ship_split_mask = (so_ship_base["batch_count"].to_numpy() == 2) & (rng.random(len(so_ship_base)) < 0.38)

    sh_p1 = so_ship_base.copy()
    sh_p1["ship_seq"] = 1
    sh_p1["shipped_qty_pcs"] = np.where(
        ship_split_mask,
        np.round(sh_p1["total_produced_good_pcs"] * 0.55).astype(np.int64),
        sh_p1["total_produced_good_pcs"].astype(np.int64),
    )
    sh_p1["prod_ready_ord"] = np.where(ship_split_mask, sh_p1["first_batch_comp_ord"], sh_p1["last_batch_comp_ord"])

    sh_p2 = so_ship_base[ship_split_mask].copy()
    sh_p2["ship_seq"] = 2
    sh_p2["shipped_qty_pcs"] = (
        sh_p2["total_produced_good_pcs"].astype(np.int64)
        - np.round(sh_p2["total_produced_good_pcs"] * 0.55).astype(np.int64)
    )
    sh_p2["prod_ready_ord"] = sh_p2["last_batch_comp_ord"]

    df_sh = pd.concat([sh_p1, sh_p2], ignore_index=True)
    df_sh.sort_values(["order_line_key", "ship_seq"], inplace=True)
    df_sh.reset_index(drop=True, inplace=True)
    n_ship = len(df_sh)
    ship_line_keys = np.arange(1, n_ship + 1, dtype=np.int64)

    # Dates: factory dispatch_date >= prod_ready_ord + 1..3 days
    # Chattogram factories (company 3) have 1-day port transfer; Dhaka/Gazipur/Mymensingh have 2-4 days inland haulage
    sh_comp = df_sh["company_key"].to_numpy()
    sh_yr = df_sh["calendar_year"].to_numpy()
    sh_mo = df_sh["calendar_month"].to_numpy()
    prod_ready = df_sh["prod_ready_ord"].to_numpy()
    req_deliv = df_sh["req_deliv_ordinal"].to_numpy()

    dispatch_ord = np.minimum(prod_ready + rng.integers(1, 4, size=n_ship), MAX_ORD - 6)
    port_wait_days = np.where(sh_comp == 3, rng.integers(1, 4, size=n_ship), rng.integers(2, 6, size=n_ship))
    # Port congestion bumps during 2020-2022 COVID/container shortage & monsoon months
    port_wait_days = np.where(np.isin(sh_yr, [2020, 2021, 2022]), port_wait_days + rng.integers(2, 7, size=n_ship), port_wait_days)
    actual_ship_ord = np.minimum(dispatch_ord + port_wait_days, MAX_ORD - 3)
    expected_ship_ord = np.minimum(np.maximum(df_sh["order_date_ordinal"].to_numpy() + 14, req_deliv - 21), MAX_ORD - 5)

    # Shipping mode: Sea Freight (Chattogram/Mongla) ~91%, Air Freight (HSIA Dhaka) ~9% (higher when production is late)
    is_late_to_port = actual_ship_ord > expected_ship_ord
    air_prob = np.where(is_late_to_port, 0.22, 0.045)
    is_air = rng.random(n_ship) < air_prob
    shipping_mode = np.where(is_air, "Air Freight (HSIA Dhaka)", "Sea Freight FCL/LCL (Chattogram Port)")

    # Transit time to destination country
    dest_countries = df_buyer["destination_country"].reindex(df_sh["buyer_key"].to_numpy()).to_numpy()
    sea_transit_base = np.where(
        dest_countries == "United States", 28,
        np.where(dest_countries == "Canada", 27,
                 np.where(np.isin(dest_countries, ["Japan", "Australia", "South Korea"]), 16,
                          np.where(np.isin(dest_countries, ["India", "United Arab Emirates"]), 9, 22)))  # EU/UK ~22 days
    )
    # 2024-2025 Red Sea / Suez diversion adds ~8 days to EU/UK/US East Coast sea transit
    red_sea_bump = np.where((sh_yr >= 2024) & (~np.isin(dest_countries, ["Japan", "Australia", "South Korea", "India"])), 7, 0)
    transit_days = np.where(is_air, rng.integers(3, 7, size=n_ship), sea_transit_base + red_sea_bump + rng.integers(-2, 6, size=n_ship))

    est_arrival_ord = np.minimum(expected_ship_ord + sea_transit_base, MAX_ORD)
    actual_arrival_ord = np.minimum(actual_ship_ord + transit_days, MAX_ORD)
    confirmed_deliv_ord = np.minimum(actual_arrival_ord + rng.integers(1, 5, size=n_ship), MAX_ORD)
    # Guarantee chronological sequence: dispatch <= actual_ship <= actual_arrival <= confirmed_deliv
    actual_ship_ord = np.maximum(dispatch_ord, actual_ship_ord)
    actual_arrival_ord = np.maximum(actual_ship_ord + 1, actual_arrival_ord)
    confirmed_deliv_ord = np.maximum(actual_arrival_ord, confirmed_deliv_ord)

    ship_delay_days = np.maximum(0, actual_ship_ord - expected_ship_ord)
    deliv_delay_days = np.maximum(0, confirmed_deliv_ord - req_deliv)
    is_on_time_ship = ship_delay_days <= 2
    is_on_time_deliv = deliv_delay_days <= 3

    delay_reasons = np.where(
        ~is_on_time_deliv,
        np.where(
            (sh_yr == 2020) & np.isin(sh_mo, [3, 4, 5, 6, 7]),
            "COVID-19 Lockdown & Vessel Blank Sailing",
            np.where(
                np.isin(sh_yr, [2021, 2022]),
                "Global Container Shortage & Port Congestion",
                np.where(
                    (sh_yr >= 2024) & (red_sea_bump > 0),
                    "Red Sea Maritime Rerouting & Transit Delay",
                    np.where(
                        df_sh["any_prod_delay"].to_numpy(),
                        "Raw Material Lead-Time & Production Bottleneck",
                        "Customs Clearance & Inland Corridor Congestion"
                    )
                )
            )
        ),
        "On-Time Delivery (No Delay)"
    )

    # Financial calculations on shipment line
    shipped_qty = df_sh["shipped_qty_pcs"].to_numpy()
    eff_unit_price = df_sh["unit_price_usd"].to_numpy() * (1.0 - df_sh["discount_rate"].to_numpy())
    fob_rev_usd = np.round(shipped_qty * eff_unit_price, 2)
    fx_sh = df_sh["bdt_usd_exchange_rate"].to_numpy()
    fob_rev_bdt = np.round(fob_rev_usd * fx_sh, 2)

    # Freight & inland logistics costs
    freight_mult = np.where(np.isin(sh_yr, [2021, 2022]), 2.25, np.where(sh_yr >= 2024, 1.45, 1.0))
    unit_freight_usd = np.where(is_air, rng.uniform(0.95, 1.85, size=n_ship), rng.uniform(0.14, 0.32, size=n_ship) * freight_mult)
    freight_cost_usd = np.round(shipped_qty * unit_freight_usd, 2)
    freight_cost_bdt = np.round(freight_cost_usd * fx_sh, 2)
    inland_log_usd = np.round(shipped_qty * np.where(sh_comp == 3, 0.035, 0.075), 2)
    inland_log_bdt = np.round(inland_log_usd * fx_sh, 2)

    disp_dt, disp_key = ordinals_to_dates_and_keys(dispatch_ord)
    exp_sh_dt, exp_sh_key = ordinals_to_dates_and_keys(expected_ship_ord)
    act_sh_dt, act_sh_key = ordinals_to_dates_and_keys(actual_ship_ord)
    est_arr_dt, est_arr_key = ordinals_to_dates_and_keys(est_arrival_ord)
    act_arr_dt, act_arr_key = ordinals_to_dates_and_keys(actual_arrival_ord)
    conf_del_dt, conf_del_key = ordinals_to_dates_and_keys(confirmed_deliv_ord)

    fact_shipment_line = pd.DataFrame({
        "shipment_line_key": ship_line_keys,
        "shipment_id": [f"SHP-{yr}-{(k // 2) + 1:06d}" for yr, k in zip(sh_yr, ship_line_keys)],
        "order_line_key": df_sh["order_line_key"],
        "sales_order_id": df_sh["sales_order_id"],
        "company_key": sh_comp,
        "factory_key": df_sh["factory_key"],
        "buyer_key": df_sh["buyer_key"],
        "product_key": df_sh["product_key"],
        "dispatch_date_key": disp_key,
        "dispatch_date": disp_dt,
        "expected_ship_date_key": exp_sh_key,
        "expected_ship_date": exp_sh_dt,
        "actual_ship_date_key": act_sh_key,
        "actual_ship_date": act_sh_dt,
        "estimated_arrival_date_key": est_arr_key,
        "estimated_arrival_date": est_arr_dt,
        "actual_arrival_date_key": act_arr_key,
        "actual_arrival_date": act_arr_dt,
        "confirmed_delivery_date_key": conf_del_key,
        "confirmed_delivery_date": conf_del_dt,
        "shipped_qty_pcs": shipped_qty,
        "delivered_qty_pcs": shipped_qty,
        "currency_code": "USD",
        "bdt_usd_exchange_rate": fx_sh,
        "fob_revenue_usd": fob_rev_usd,
        "fob_revenue_bdt": fob_rev_bdt,
        "delivered_revenue_usd": fob_rev_usd,
        "delivered_revenue_bdt": fob_rev_bdt,
        "freight_cost_usd": freight_cost_usd,
        "freight_cost_bdt": freight_cost_bdt,
        "inland_logistics_cost_usd": inland_log_usd,
        "inland_logistics_cost_bdt": inland_log_bdt,
        "shipping_mode": shipping_mode,
        "port_of_loading": np.where(is_air, "Hazrat Shahjalal Int. Airport (DAC)", "Chattogram Sea Port (CGP)"),
        "export_destination_country": dest_countries,
        "shipment_delay_days": ship_delay_days,
        "delivery_delay_days": deliv_delay_days,
        "is_on_time_shipment": is_on_time_ship,
        "is_on_time_delivery": is_on_time_deliv,
        "is_partial_shipment": df_sh["ship_seq"].to_numpy() > 1,
        "delivery_status": np.where(is_on_time_deliv, "Delivered On-Time", "Delivered Late"),
        "delay_reason": delay_reasons,
        "event_year": pd.to_datetime(act_sh_dt).dt.year.to_numpy(),
    })

    # Reconcile total shipped_qty_pcs back onto df_so
    ship_totals = fact_shipment_line.groupby("order_line_key", as_index=False)["shipped_qty_pcs"].sum()
    df_so = df_so.merge(ship_totals, on="order_line_key", how="left")
    df_so["shipped_qty_pcs"] = df_so["shipped_qty_pcs"].fillna(0).astype(np.int64)
    df_so["unfulfilled_backlog_qty_pcs"] = np.maximum(0, df_so["amended_order_qty_pcs"] - df_so["shipped_qty_pcs"])

    # Drop helper ordinal columns from df_so
    df_so.drop(columns=["order_date_ordinal", "req_deliv_ordinal"], inplace=True)

    return df_so, fact_production_batch, fact_material_consumption, fact_quality_inspection, fact_shipment_line


def generate_procurement_and_supplier_deliveries(
    fact_material_consumption: pd.DataFrame,
    dims: dict[str, pd.DataFrame],
    df_macro: pd.DataFrame,
    target_po_lines: int = 245000,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates `fact_purchase_order_line` (~245,000 rows) and `fact_supplier_delivery` (~280,000 rows)
    driven by factory/material demand in `fact_material_consumption`, respecting supplier lead times
    and domestic vs. imported sourcing profiles.
    """
    rng = np.random.default_rng(seed + 300)
    df_sup = dims["dim_supplier"]
    df_mat = dims["dim_material"].set_index("material_key")
    macro_map = df_macro.set_index(["calendar_year", "calendar_month"])

    # Sample/group consumption events to create realistic consolidated PO lines (~245,000 lines)
    mc = fact_material_consumption.copy()
    mc["cons_dt_ord"] = [d.toordinal() for d in mc["consumption_date"]]
    # Sort chronologically and take every ~2.37th consumption cluster or aggregate by (factory, material, bi-weekly window)
    mc["biweek_bucket"] = (mc["cons_dt_ord"] - MIN_ORD) // 10
    po_agg = mc.groupby(
        ["company_key", "factory_key", "material_key", "biweek_bucket"],
        as_index=False
    ).agg(
        req_qty=("actual_material_qty", "sum"),
        earliest_cons_ord=("cons_dt_ord", "min"),
        avg_unit_cost_usd=("unit_cost_usd", "mean"),
        avg_fx=("bdt_usd_exchange_rate", "mean"),
    )

    # If po_agg has fewer or more rows than target_po_lines, supplement with split replenishment POs
    n_base = len(po_agg)
    if n_base < target_po_lines:
        extra_needed = target_po_lines - n_base
        top_idx = rng.choice(n_base, size=extra_needed, replace=True)
        po_extra = po_agg.iloc[top_idx].copy()
        po_agg["req_qty"] = np.round(po_agg["req_qty"] * 0.65, 2)
        po_extra["req_qty"] = np.round(po_extra["req_qty"] * 0.45, 2)
        po_extra["earliest_cons_ord"] = np.maximum(MIN_ORD + 10, po_extra["earliest_cons_ord"] - rng.integers(3, 12, size=extra_needed))
        po_df = pd.concat([po_agg, po_extra], ignore_index=True)
    else:
        po_df = po_agg.iloc[:target_po_lines].copy()

    po_df.sort_values("earliest_cons_ord", inplace=True)
    po_df.reset_index(drop=True, inplace=True)
    n_po = len(po_df)
    po_line_keys = np.arange(1, n_po + 1, dtype=np.int64)

    # Match each material_key to compatible suppliers
    mat_keys = po_df["material_key"].to_numpy()
    mat_group_arr = df_mat["material_group"].reindex(mat_keys).to_numpy()
    mat_std_lt = df_mat["standard_lead_time_days"].reindex(mat_keys).to_numpy()

    sup_keys_assigned = np.zeros(n_po, dtype=np.int64)
    for m_grp in np.unique(mat_group_arr):
        m_mask = mat_group_arr == m_grp
        cand_sups = df_sup[df_sup["major_materials_supplied"].str.contains(m_grp.split()[0], case=False, na=False)]
        if cand_sups.empty:
            cand_sups = df_sup
        s_keys = cand_sups["supplier_key"].to_numpy()
        s_weights = cand_sups["spend_share_weight"].to_numpy().copy()
        s_weights /= s_weights.sum()
        sup_keys_assigned[m_mask] = rng.choice(s_keys, size=int(m_mask.sum()), p=s_weights)

    sup_indexed = df_sup.set_index("supplier_key")
    sup_lt_arr = sup_indexed["average_lead_time_days"].reindex(sup_keys_assigned).to_numpy()
    sup_rel_arr = sup_indexed["baseline_reliability_score"].reindex(sup_keys_assigned).to_numpy()

    # PO Order Date is placed prior to earliest_cons_ord by supplier lead time + buffer
    cons_ord = po_df["earliest_cons_ord"].to_numpy()
    po_ord_ordinals = np.maximum(MIN_ORD, cons_ord - sup_lt_arr - rng.integers(3, 14, size=n_po))
    exp_deliv_ordinals = np.minimum(MAX_ORD - 4, po_ord_ordinals + np.maximum(5, (sup_lt_arr + mat_std_lt) // 2))
    po_ord_ordinals = np.minimum(po_ord_ordinals, exp_deliv_ordinals - 5)

    po_dt, po_dt_key = ordinals_to_dates_and_keys(po_ord_ordinals)
    exp_dt, exp_dt_key = ordinals_to_dates_and_keys(exp_deliv_ordinals)
    po_years = pd.to_datetime(po_dt).dt.year.to_numpy()

    # Ordered quantity includes a 3%..8% safety buffer above batch consumption requirement
    ordered_qty = np.maximum(10.0, np.round(po_df["req_qty"].to_numpy() * rng.uniform(1.03, 1.09, size=n_po), 2))
    unit_cost_usd = np.round(po_df["avg_unit_cost_usd"].to_numpy() * rng.uniform(0.97, 1.04, size=n_po), 3)
    fx_arr = np.round(po_df["avg_fx"].to_numpy(), 4)
    po_val_usd = np.round(ordered_qty * unit_cost_usd, 2)
    po_val_bdt = np.round(po_val_usd * fx_arr, 2)

    # Split ~15% of PO lines into 2 supplier deliveries so fact_supplier_delivery has ~282,000 rows
    split_deliv = rng.random(n_po) < 0.15
    short_deliv = (~split_deliv) & (rng.random(n_po) < 0.045)
    po_status = np.where(short_deliv, "Closed Short (Partial Receipt)", np.where(split_deliv, "Received in Split Lots", "Received in Full"))

    fact_purchase_order_line = pd.DataFrame({
        "purchase_order_line_key": po_line_keys,
        "purchase_order_id": [f"PO-{yr}-{(k // 3) + 10001:06d}" for yr, k in zip(po_years, po_line_keys)],
        "po_line_number": [(k % 3) + 1 for k in range(n_po)],
        "supplier_key": sup_keys_assigned,
        "company_key": po_df["company_key"].to_numpy(),
        "receiving_factory_key": po_df["factory_key"].to_numpy(),
        "material_key": mat_keys,
        "po_order_date_key": po_dt_key,
        "po_order_date": po_dt,
        "expected_delivery_date_key": exp_dt_key,
        "expected_delivery_date": exp_dt,
        "ordered_qty": ordered_qty,
        "currency_code": "USD",
        "bdt_usd_exchange_rate": fx_arr,
        "unit_cost_usd": unit_cost_usd,
        "order_value_usd": po_val_usd,
        "order_value_bdt": po_val_bdt,
        "purchase_status": po_status,
        "event_year": po_years,
    })

    # Build fact_supplier_delivery
    deliv_p1 = fact_purchase_order_line.copy()
    deliv_p1["deliv_seq"] = 1
    deliv_p1["lot_share"] = np.where(split_deliv, 0.60, np.where(short_deliv, rng.uniform(0.84, 0.94, size=n_po), 1.00))
    deliv_p1["sup_rel"] = sup_rel_arr
    deliv_p1["po_ord_ordinal"] = po_ord_ordinals
    deliv_p1["exp_deliv_ordinal"] = exp_deliv_ordinals

    deliv_p2 = deliv_p1[split_deliv].copy()
    deliv_p2["deliv_seq"] = 2
    deliv_p2["lot_share"] = 0.40

    df_del = pd.concat([deliv_p1, deliv_p2], ignore_index=True)
    df_del.sort_values(["purchase_order_line_key", "deliv_seq"], inplace=True)
    df_del.reset_index(drop=True, inplace=True)
    n_del = len(df_del)
    deliv_keys = np.arange(1, n_del + 1, dtype=np.int64)

    # Supplier dispatch & receipt dates
    d_po_ord = df_del["po_ord_ordinal"].to_numpy()
    d_exp_ord = df_del["exp_deliv_ordinal"].to_numpy()
    d_rel = df_del["sup_rel"].to_numpy()
    d_yr = df_del["event_year"].to_numpy()

    # Delay probability inversely proportional to supplier reliability, higher in 2020-2022
    late_prob = np.clip((1.0 - d_rel) * 1.9 + np.where(np.isin(d_yr, [2020, 2021, 2022]), 0.18, 0.0), 0.05, 0.68)
    is_late = (rng.random(n_del) < late_prob) | (df_del["deliv_seq"].to_numpy() == 2)
    delay_days = np.where(
        is_late,
        rng.integers(2, 16, size=n_del) + np.where(df_del["deliv_seq"].to_numpy() == 2, 5, 0),
        rng.integers(-3, 1, size=n_del)
    )
    receipt_ord = np.clip(d_exp_ord + delay_days, d_po_ord + 2, MAX_ORD)
    dispatch_ord = np.maximum(d_po_ord, receipt_ord - rng.integers(2, 14, size=n_del))

    disp_d, disp_k = ordinals_to_dates_and_keys(dispatch_ord)
    rec_d, rec_k = ordinals_to_dates_and_keys(receipt_ord)

    received_qty = np.round(df_del["ordered_qty"].to_numpy() * df_del["lot_share"].to_numpy(), 2)
    # Material incoming inspection rejection rate (0% to 4.5% depending on supplier reliability)
    rej_rate = np.where(rng.random(n_del) < (1.0 - d_rel) * 1.5, rng.uniform(0.01, 0.048, size=n_del), 0.0)
    rejected_qty = np.round(received_qty * rej_rate, 2)
    accepted_qty = np.round(received_qty - rejected_qty, 2)

    u_cost = df_del["unit_cost_usd"].to_numpy()
    d_fx = df_del["bdt_usd_exchange_rate"].to_numpy()
    doc_cost_usd = np.round(accepted_qty * u_cost, 2)
    doc_cost_bdt = np.round(doc_cost_usd * d_fx, 2)

    fact_supplier_delivery = pd.DataFrame({
        "delivery_key": deliv_keys,
        "delivery_id": [f"GRN-{yr}-{dk:06d}" for yr, dk in zip(pd.to_datetime(rec_d).dt.year, deliv_keys)],
        "purchase_order_line_key": df_del["purchase_order_line_key"].to_numpy(),
        "purchase_order_id": df_del["purchase_order_id"].to_numpy(),
        "supplier_key": df_del["supplier_key"].to_numpy(),
        "company_key": df_del["company_key"].to_numpy(),
        "receiving_factory_key": df_del["receiving_factory_key"].to_numpy(),
        "material_key": df_del["material_key"].to_numpy(),
        "dispatch_date_key": disp_k,
        "dispatch_date": disp_d,
        "receipt_date_key": rec_k,
        "receipt_date": rec_d,
        "received_qty": received_qty,
        "accepted_qty": accepted_qty,
        "rejected_qty": rejected_qty,
        "delivery_delay_days": np.maximum(0, receipt_ord - d_exp_ord),
        "is_on_time_delivery": (receipt_ord - d_exp_ord) <= 2,
        "currency_code": "USD",
        "bdt_usd_exchange_rate": d_fx,
        "unit_cost_usd": u_cost,
        "documented_material_cost_usd": doc_cost_usd,
        "documented_material_cost_bdt": doc_cost_bdt,
        "event_year": pd.to_datetime(rec_d).dt.year.to_numpy(),
    })

    return fact_purchase_order_line, fact_supplier_delivery


def generate_monthly_snapshots_and_costs(
    dims: dict[str, pd.DataFrame],
    df_macro: pd.DataFrame,
    fact_production_batch: pd.DataFrame,
    fact_material_consumption: pd.DataFrame,
    fact_quality_inspection: pd.DataFrame,
    fact_shipment_line: pd.DataFrame,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generates the 4 periodic/financial fact tables:
    1. fact_workforce_monthly (~45,000 rows: month x active factory x department x worker grade)
    2. fact_sustainability_monthly (~5,500 rows: month x active factory)
    3. fact_inventory_snapshot_monthly (~265,000 rows: month x active factory x item x stock type with exact opening + additions - issues = closing reconciliation)
    4. fact_cost_transaction (~260,000 rows: traceable cost postings across all 12 cost categories)
    """
    rng = np.random.default_rng(seed + 400)
    df_fac = dims["dim_factory"]
    df_mat = dims["dim_material"]
    df_prod = dims["dim_product"]
    macro_map = df_macro.set_index(["calendar_year", "calendar_month"])

    # Pre-aggregate monthly factory production output & hours for realistic scaling
    pb_dt = pd.to_datetime(fact_production_batch["actual_completion_date"])
    pb_monthly = fact_production_batch.assign(
        yr=pb_dt.dt.year,
        mo=pb_dt.dt.month
    ).groupby(["factory_key", "yr", "mo"], as_index=False).agg(
        monthly_output_pcs=("actual_good_output_pcs", "sum"),
        monthly_labour_hrs=("actual_labour_hours", "sum"),
    )
    pb_map = pb_monthly.set_index(["factory_key", "yr", "mo"])

    # ---------------------------------------------------------
    # 1. fact_workforce_monthly & 2. fact_sustainability_monthly
    # ---------------------------------------------------------
    # 9 workforce segments per active factory per month (~5,500 factory-months * 9 = ~49,500 rows)
    wf_segments = [
        ("Cutting & Spreading", "Grade-3 Senior Cutter & CAD Marker", 1.52, 0.08),
        ("Cutting & Spreading", "Grade-5 Helper & Layer", 1.04, 0.07),
        ("Sewing Floor", "Grade-3 Senior Multi-Machine Operator", 1.44, 0.22),
        ("Sewing Floor", "Grade-4 Regular Sewing Operator", 1.24, 0.28),
        ("Sewing Floor", "Grade-5 Junior Operator & Helper", 1.02, 0.14),
        ("Quality Assurance", "Grade-3 End-Line & Final QC Inspector", 1.38, 0.07),
        ("Finishing & Packing", "Grade-4 Ironer, Folder & Packer", 1.16, 0.08),
        ("Washing, Dyeing & Utility", "Grade-3 Wet-Process & Boiler Technician", 1.56, 0.03),
        ("Maintenance & Store", "Grade-2 इलेक्ट्रो-Mechanical Technician & Supervisor", 1.88, 0.03),
    ]
    # Clean ASCII label for Grade-2
    wf_segments[-1] = ("Maintenance & Store", "Grade-2 Electro-Mechanical Technician & Supervisor", 1.88, 0.03)

    wf_rows = []
    sust_rows = []
    wf_key = 1
    sust_key = 1

    for yr in range(2006, 2026):
        for mo in range(1, 13):
            m_start = datetime.date(yr, mo, 1)
            date_key = yr * 10000 + mo * 100 + 1
            m_row = macro_map.loc[(yr, mo)]
            fx_rate = float(m_row["bdt_usd_exchange_rate"])
            stat_min_bdt = float(m_row["statutory_min_wage_entry_bdt"])
            floor_bdt = float(m_row["modeled_industry_floor_wage_bdt"])
            elec_rate_bdt = float(m_row["industrial_electricity_bdt_per_kwh"])
            gas_rate_bdt = float(m_row["industrial_gas_bdt_per_m3"])
            fy_str = str(m_row["fiscal_year"])

            for _, fac in df_fac.iterrows():
                if not (fac["opening_date"] <= m_start <= fac["closure_date"]):
                    continue
                fk = int(fac["factory_key"])
                ck = int(fac["company_key"])
                n_lines = int(fac["design_line_count"])
                cap_pcs = int(fac["base_monthly_capacity_pcs"])

                if (fk, yr, mo) in pb_map.index:
                    out_pcs = int(pb_map.loc[(fk, yr, mo), "monthly_output_pcs"])
                else:
                    out_pcs = int(cap_pcs * 0.72)

                util_ratio = np.clip(out_pcs / max(1, cap_pcs), 0.35, 1.25)
                total_fac_headcount = int(round(n_lines * 68 * (0.88 + 0.14 * util_ratio)))

                # Sustainability metrics for this factory-month
                is_eco_fac = "Eco-Design" in str(fac["compliance_profile"]) or ck == 4
                is_wet_heavy = ck in (1, 3, 5)  # Composite knit dyeing or denim washing/weaving
                eff_progress = max(0.72, 1.0 - 0.011 * (yr - 2006)) * (0.80 if is_eco_fac else 1.0)

                kwh_per_pc = (0.48 if is_wet_heavy else 0.29) * eff_progress * rng.uniform(0.94, 1.06)
                elec_kwh = round(out_pcs * kwh_per_pc, 1)

                # Solar renewable share grows after 2014, especially in eco factories
                if yr < 2013:
                    ren_share = 0.01 if is_eco_fac else 0.0
                else:
                    ren_share = min(0.32, (0.04 if is_eco_fac else 0.012) * (yr - 2012) * rng.uniform(0.9, 1.1))
                ren_kwh = round(elec_kwh * ren_share, 1)

                gas_m3_per_pc = (0.19 if is_wet_heavy else 0.07) * eff_progress * rng.uniform(0.93, 1.07)
                gas_m3 = round(out_pcs * gas_m3_per_pc, 1)

                water_l_per_pc = (42.0 if is_wet_heavy else 11.5) * eff_progress * rng.uniform(0.94, 1.06)
                water_m3 = round((out_pcs * water_l_per_pc) / 1000.0, 1)
                wastewater_treated_m3 = round(water_m3 * (0.94 if (yr >= 2014 or is_eco_fac) else 0.78), 1)

                solid_waste_kg = round(out_pcs * 0.042 * rng.uniform(0.92, 1.08), 1)
                recycle_rate = min(0.78, (0.38 if is_eco_fac else 0.18) + 0.018 * (yr - 2006))
                recycled_waste_kg = round(solid_waste_kg * recycle_rate, 1)

                # Grid + natural gas Scope 1 & 2 CO2e estimation (kg CO2e)
                grid_kwh = elec_kwh - ren_kwh
                co2_kg = round(grid_kwh * 0.62 + gas_m3 * 1.92, 1)
                elec_cost_bdt = round(grid_kwh * elec_rate_bdt, 2)
                gas_cost_bdt = round(gas_m3 * gas_rate_bdt, 2)

                sust_rows.append({
                    "sustainability_month_key": sust_key,
                    "date_key": date_key,
                    "month_start_date": m_start,
                    "calendar_year": yr,
                    "calendar_month": mo,
                    "fiscal_year": fy_str,
                    "company_key": ck,
                    "factory_key": fk,
                    "monthly_output_pcs": out_pcs,
                    "electricity_consumption_kwh": elec_kwh,
                    "renewable_solar_kwh": ren_kwh,
                    "renewable_energy_share_pct": round(ren_share * 100.0, 2),
                    "natural_gas_consumption_m3": gas_m3,
                    "water_withdrawal_m3": water_m3,
                    "wastewater_treated_m3": wastewater_treated_m3,
                    "solid_fabric_waste_kg": solid_waste_kg,
                    "recycled_material_kg": recycled_waste_kg,
                    "waste_recycling_rate_pct": round(recycle_rate * 100.0, 2),
                    "estimated_carbon_emissions_kg_co2e": co2_kg,
                    "emissions_per_garment_kg_co2e": round(co2_kg / max(1, out_pcs), 4),
                    "utility_cost_bdt": round(elec_cost_bdt + gas_cost_bdt, 2),
                    "utility_cost_usd": round((elec_cost_bdt + gas_cost_bdt) / fx_rate, 2),
                    "estimation_methodology": "Activity-Based Meter & Emission Factor Model (Synthetic Entity - Non-Certified)",
                    "event_year": yr,
                })
                sust_key += 1

                # Workforce segments for this factory-month
                for dept, grade_role, wage_mult, hc_share in wf_segments:
                    hc = max(4, int(round(total_fac_headcount * hc_share * rng.uniform(0.96, 1.04))))
                    turnover_rate = rng.uniform(0.018, 0.048) + (0.025 if mo in (4, 5, 11) else 0.0)
                    separations = int(round(hc * turnover_rate))
                    hires = max(0, separations + int(rng.integers(-2, 4)))

                    # Average monthly base + allowance wage in BDT (distinct from entry statutory minimum)
                    seniority_drift = 1.0 + 0.008 * (yr - 2006)
                    avg_base_wage_bdt = round(floor_bdt * wage_mult * seniority_drift * rng.uniform(0.97, 1.04), 2)
                    base_payroll_bdt = round(hc * avg_base_wage_bdt * 0.65, 2)
                    allowances_bdt = round(hc * avg_base_wage_bdt * 0.35, 2)

                    # Overtime hours per worker per month (22 to 52 hours depending on utilization)
                    ot_hrs_per_worker = round(max(6.0, 28.0 * util_ratio * rng.uniform(0.85, 1.18)), 1)
                    total_ot_hours = round(hc * ot_hrs_per_worker, 1)
                    # Statutory overtime rate in Bangladesh is 2x basic hourly wage
                    hourly_basic_bdt = (avg_base_wage_bdt * 0.65) / 208.0
                    ot_expense_bdt = round(total_ot_hours * (hourly_basic_bdt * 2.0), 2)
                    # Festival bonus in Eid months
                    festival_bonus_bdt = round(base_payroll_bdt * 0.50, 2) if mo in (4, 6, 8, 9, 10) and (yr + mo) % 5 == 0 else 0.0
                    total_payroll_bdt = round(base_payroll_bdt + allowances_bdt + ot_expense_bdt + festival_bonus_bdt, 2)

                    wf_rows.append({
                        "workforce_month_key": wf_key,
                        "date_key": date_key,
                        "month_start_date": m_start,
                        "calendar_year": yr,
                        "calendar_month": mo,
                        "fiscal_year": fy_str,
                        "company_key": ck,
                        "factory_key": fk,
                        "department_name": dept,
                        "worker_grade_role": grade_role,
                        "active_headcount": hc,
                        "monthly_hires": hires,
                        "monthly_separations": separations,
                        "statutory_entry_min_wage_bdt": stat_min_bdt,
                        "average_monthly_wage_bdt": avg_base_wage_bdt,
                        "overtime_hours": total_ot_hours,
                        "base_payroll_bdt": base_payroll_bdt,
                        "allowances_and_bonus_bdt": round(allowances_bdt + festival_bonus_bdt, 2),
                        "overtime_expense_bdt": ot_expense_bdt,
                        "total_payroll_bdt": total_payroll_bdt,
                        "total_payroll_usd": round(total_payroll_bdt / fx_rate, 2),
                        "absenteeism_rate_pct": round(float(rng.uniform(2.1, 5.8)), 2),
                        "training_hours": round(hc * float(rng.uniform(0.5, 2.2)), 1),
                        "event_year": yr,
                    })
                    wf_key += 1

    fact_workforce_monthly = pd.DataFrame(wf_rows)
    fact_sustainability_monthly = pd.DataFrame(sust_rows)

    # ---------------------------------------------------------
    # 3. fact_inventory_snapshot_monthly (~265,000 rows)
    # Every active factory tracks 48 stocked items across Raw Material, Work-in-Progress (WIP), and Finished Goods (FG)
    # With exact period-over-period continuity: closing_qty(t-1) == opening_qty(t) and
    # closing_qty(t) == opening_qty(t) + receipts + prod_additions - consumption - shipments + adjustments
    # ---------------------------------------------------------
    inv_items = []
    # 30 key raw materials + 9 WIP product lines + 9 Finished Goods styles per factory (48 items * ~5,500 fac-months = ~264,000 rows)
    for mk in range(1, 31):
        m_row = df_mat.loc[df_mat["material_key"] == mk].iloc[0]
        inv_items.append((
            f"RM-{mk:03d}", int(mk), 0, "Raw Material",
            str(m_row["base_uom"]), float(m_row["base_unit_cost_usd_2015"])
        ))
    for pk_idx, pk in enumerate(range(1, 90, 10), start=1):
        p_row = df_prod.loc[df_prod["product_key"] == pk].iloc[0]
        inv_items.append((
            f"WIP-{pk:03d}", int(p_row["primary_material_key"]), int(pk), "Work in Progress (WIP)",
            "PCS", round(float(p_row["base_fob_unit_price_usd"]) * 0.55, 2)
        ))
        inv_items.append((
            f"FG-{pk:03d}", int(p_row["primary_material_key"]), int(pk), "Finished Goods (FG)",
            "PCS", round(float(p_row["base_fob_unit_price_usd"]) * 0.82, 2)
        ))

    # Build vector arrays of active (factory_key, yr, mo) in chronological order per factory
    active_fm = fact_sustainability_monthly[["factory_key", "company_key", "calendar_year", "calendar_month", "date_key", "month_start_date", "fiscal_year", "monthly_output_pcs"]].copy()
    active_fm.sort_values(["factory_key", "calendar_year", "calendar_month"], inplace=True)
    active_fm.reset_index(drop=True, inplace=True)

    # Expand active_fm x inv_items (48 items)
    n_fm = len(active_fm)
    n_items = len(inv_items)
    total_inv_rows = n_fm * n_items

    fm_rep = active_fm.loc[np.repeat(active_fm.index.values, n_items)].reset_index(drop=True)
    item_codes = np.tile([x[0] for x in inv_items], n_fm)
    item_mat_keys = np.tile([x[1] for x in inv_items], n_fm)
    item_prod_keys = np.tile([x[2] for x in inv_items], n_fm)
    item_stock_types = np.tile([x[3] for x in inv_items], n_fm)
    item_uoms = np.tile([x[4] for x in inv_items], n_fm)
    item_base_usd = np.tile([x[5] for x in inv_items], n_fm)

    # Compute sequential inventory balance along each (factory_key, item_code) time series
    # Sort by (factory_key, item_code, calendar_year, calendar_month) so each series is a contiguous block!
    fm_rep["item_code"] = item_codes
    fm_rep["material_key"] = item_mat_keys
    fm_rep["product_key"] = item_prod_keys
    fm_rep["stock_type"] = item_stock_types
    fm_rep["uom"] = item_uoms
    fm_rep["base_unit_usd"] = item_base_usd

    fm_rep.sort_values(["factory_key", "item_code", "calendar_year", "calendar_month"], inplace=True)
    fm_rep.reset_index(drop=True, inplace=True)

    # Identify start of each (factory_key, item_code) series
    fac_col = fm_rep["factory_key"].to_numpy()
    ic_col = fm_rep["item_code"].to_numpy()
    is_series_start = np.ones(total_inv_rows, dtype=bool)
    is_series_start[1:] = (fac_col[1:] != fac_col[:-1]) | (ic_col[1:] != ic_col[:-1])

    st_col = fm_rep["stock_type"].to_numpy()
    yr_col = fm_rep["calendar_year"].to_numpy()
    mo_col = fm_rep["calendar_month"].to_numpy()
    out_col = fm_rep["monthly_output_pcs"].to_numpy()

    # Scale monthly flow quantities realistically
    base_flow = np.where(
        st_col == "Raw Material",
        (out_col / 28.0) * rng.uniform(0.75, 1.30, size=total_inv_rows),
        (out_col / 14.0) * rng.uniform(0.70, 1.25, size=total_inv_rows)
    )
    base_flow = np.round(np.maximum(25.0, base_flow), 2)

    # Net monthly change (builds up during 2020 COVID shock & peak season buffers, draws down afterwards)
    drift_factor = np.where(
        (yr_col == 2020) & np.isin(mo_col, [3, 4, 5, 6]),
        rng.uniform(0.04, 0.16, size=total_inv_rows),
        rng.uniform(-0.06, 0.065, size=total_inv_rows)
    )
    inflow_qty = np.round(base_flow * (1.0 + np.maximum(0.0, drift_factor)), 2)
    outflow_qty = np.round(base_flow * (1.0 + np.maximum(0.0, -drift_factor)), 2)
    adj_qty = np.where(rng.random(total_inv_rows) < 0.08, np.round(base_flow * rng.uniform(-0.015, 0.012, size=total_inv_rows), 2), 0.0)

    # Propagate opening and closing balances strictly along each time series
    opening_qty = np.zeros(total_inv_rows, dtype=np.float64)
    closing_qty = np.zeros(total_inv_rows, dtype=np.float64)
    initial_stock = np.round(base_flow * rng.uniform(0.55, 1.15, size=total_inv_rows), 2)

    # Fast loop over max 240 steps using vectorized group offsets or simple C-speed numba-like step
    # Since each series has <= 240 months, let's compute step index within each series (0..239)
    series_id = np.cumsum(is_series_start) - 1
    _, series_start_idx = np.unique(series_id, return_index=True)
    step_in_series = np.arange(total_inv_rows) - series_start_idx[series_id]

    opening_qty[step_in_series == 0] = initial_stock[step_in_series == 0]
    for s in range(240):
        m_s = step_in_series == s
        if not m_s.any():
            break
        if s > 0:
            opening_qty[m_s] = closing_qty[np.where(m_s)[0] - 1]
        # Ensure outflow doesn't drive closing stock negative
        avail = opening_qty[m_s] + inflow_qty[m_s] + adj_qty[m_s]
        outflow_qty[m_s] = np.minimum(outflow_qty[m_s], np.round(avail * 0.92, 2))
        closing_qty[m_s] = np.round(opening_qty[m_s] + inflow_qty[m_s] - outflow_qty[m_s] + adj_qty[m_s], 2)

    receipts_qty = np.where(st_col == "Raw Material", inflow_qty, 0.0)
    prod_add_qty = np.where(st_col != "Raw Material", inflow_qty, 0.0)
    cons_issue_qty = np.where(st_col != "Finished Goods (FG)", outflow_qty, 0.0)
    ship_issue_qty = np.where(st_col == "Finished Goods (FG)", outflow_qty, 0.0)

    safety_stock_qty = np.round(base_flow * 0.35, 2)
    reserved_qty = np.round(closing_qty * rng.uniform(0.35, 0.72, size=total_inv_rows), 2)
    is_stockout = closing_qty < (safety_stock_qty * 0.45)
    ageing_days = np.round(np.clip(30.0 * (closing_qty / np.maximum(1.0, outflow_qty)), 5.0, 180.0), 1)
    ageing_bucket = np.where(
        ageing_days <= 30, "0-30 Days (Fresh)",
        np.where(ageing_days <= 60, "31-60 Days (Normal)",
                 np.where(ageing_days <= 90, "61-90 Days (Slow-Moving)", "90+ Days (Aged / Excess Risk)"))
    )

    # Map FX rate by (yr, mo)
    fx_lookup = df_macro.set_index(["calendar_year", "calendar_month"])["bdt_usd_exchange_rate"].to_dict()
    inv_fx = np.array([fx_lookup[(y, m)] for y, m in zip(yr_col, mo_col)], dtype=np.float64)
    unit_val_usd = np.round(fm_rep["base_unit_usd"].to_numpy() * (0.85 + 0.15 * ((yr_col - 2006) / 19.0)), 3)
    inv_val_usd = np.round(closing_qty * unit_val_usd, 2)
    inv_val_bdt = np.round(inv_val_usd * inv_fx, 2)

    fact_inventory_snapshot_monthly = pd.DataFrame({
        "inventory_snapshot_key": np.arange(1, total_inv_rows + 1, dtype=np.int64),
        "date_key": fm_rep["date_key"].to_numpy(),
        "snapshot_month_date": fm_rep["month_start_date"].to_numpy(),
        "calendar_year": yr_col,
        "calendar_month": mo_col,
        "fiscal_year": fm_rep["fiscal_year"].to_numpy(),
        "company_key": fm_rep["company_key"].to_numpy(),
        "factory_key": fac_col,
        "item_code": ic_col,
        "material_key": fm_rep["material_key"].to_numpy(),
        "product_key": fm_rep["product_key"].to_numpy(),
        "stock_type": st_col,
        "uom": fm_rep["uom"].to_numpy(),
        "opening_qty": opening_qty,
        "receipts_qty": receipts_qty,
        "production_additions_qty": prod_add_qty,
        "consumption_issues_qty": cons_issue_qty,
        "shipment_issues_qty": ship_issue_qty,
        "adjustment_qty": adj_qty,
        "closing_qty": closing_qty,
        "reserved_qty": reserved_qty,
        "safety_stock_qty": safety_stock_qty,
        "is_below_safety_stock": closing_qty < safety_stock_qty,
        "is_stockout_incident": is_stockout,
        "average_ageing_days": ageing_days,
        "ageing_bucket": ageing_bucket,
        "currency_code": "USD",
        "bdt_usd_exchange_rate": inv_fx,
        "unit_valuation_usd": unit_val_usd,
        "inventory_value_usd": inv_val_usd,
        "inventory_value_bdt": inv_val_bdt,
        "event_year": yr_col,
    })

    # ---------------------------------------------------------
    # 4. fact_cost_transaction (~265,000 rows)
    # Combines batch-allocated direct costs (sampled/consolidated per order-line/batch) and
    # factory/company monthly overhead, utilities, labour, quality, freight, admin, and financing postings
    # without double-counting.
    # ---------------------------------------------------------
    # A. Direct Material & Trims Cost Postings (1 per production batch for categories 1 & 2 combined or split)
    mc_by_batch = fact_material_consumption.groupby("production_batch_key", as_index=False).agg(
        company_key=("company_key", "first"),
        factory_key=("factory_key", "first"),
        consumption_date_key=("consumption_date_key", "max"),
        consumption_date=("consumption_date", "max"),
        qty=("actual_material_qty", "sum"),
        fx=("bdt_usd_exchange_rate", "first"),
        cost_usd=("total_material_cost_usd", "sum"),
        cost_bdt=("total_material_cost_bdt", "sum"),
        event_year=("event_year", "max"),
    )
    # Map order_line_key from fact_production_batch
    batch_to_ol = fact_production_batch.set_index("production_batch_key")["order_line_key"].to_dict()
    mc_by_batch["order_line_key"] = [batch_to_ol[bk] for bk in mc_by_batch["production_batch_key"]]
    mc_by_batch["cost_usd"] = np.round(mc_by_batch["cost_usd"], 2)
    mc_by_batch["cost_bdt"] = np.round(mc_by_batch["cost_usd"] * mc_by_batch["fx"], 2)

    # Assign Category 1 (Direct Materials) to 70% and Category 2 (Trims & Packaging) to 30% or keep exact batch link
    cat_dm = np.where(mc_by_batch["production_batch_key"].to_numpy() % 4 == 0, 2, 1)
    cost_part_dm = pd.DataFrame({
        "transaction_date_key": mc_by_batch["consumption_date_key"],
        "transaction_date": mc_by_batch["consumption_date"],
        "company_key": mc_by_batch["company_key"],
        "factory_key": mc_by_batch["factory_key"],
        "cost_category_key": cat_dm,
        "production_batch_key": mc_by_batch["production_batch_key"],
        "order_line_key": mc_by_batch["order_line_key"],
        "reference_quantity": mc_by_batch["qty"],
        "currency_code": "USD",
        "bdt_usd_exchange_rate": mc_by_batch["fx"],
        "amount_usd": mc_by_batch["cost_usd"],
        "amount_bdt": mc_by_batch["cost_bdt"],
        "allocation_method": "Direct Batch BOM Consumption Posting",
        "event_year": mc_by_batch["event_year"],
    })

    # B. Monthly Factory & Company Cost Postings across Categories 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
    # Aggregate workforce payroll per factory-month (Category 3: Direct Labour)
    wf_fm = fact_workforce_monthly.groupby(["company_key", "factory_key", "date_key", "month_start_date", "calendar_year"], as_index=False).agg(
        hc=("active_headcount", "sum"),
        payroll_bdt=("total_payroll_bdt", "sum"),
        payroll_usd=("total_payroll_usd", "sum"),
        fx=("bdt_usd_exchange_rate", "first") if "bdt_usd_exchange_rate" in fact_workforce_monthly.columns else ("statutory_entry_min_wage_bdt", "first"),
    )
    # Lookup exact monthly FX from macro_map
    wf_months = pd.to_datetime(wf_fm["month_start_date"]).dt.month.to_numpy()
    wf_years = wf_fm["calendar_year"].to_numpy()
    wf_fx = np.array([macro_map.loc[(y, m), "bdt_usd_exchange_rate"] for y, m in zip(wf_years, wf_months)], dtype=np.float64)
    wf_fm["fx"] = wf_fx
    wf_fm["payroll_usd"] = np.round(wf_fm["payroll_bdt"].to_numpy() / wf_fx, 2)

    cost_part_dl = pd.DataFrame({
        "transaction_date_key": wf_fm["date_key"],
        "transaction_date": wf_fm["month_start_date"],
        "company_key": wf_fm["company_key"],
        "factory_key": wf_fm["factory_key"],
        "cost_category_key": 3,
        "production_batch_key": 0,
        "order_line_key": 0,
        "reference_quantity": wf_fm["hc"].astype(np.float64),
        "currency_code": "BDT",
        "bdt_usd_exchange_rate": wf_fm["fx"],
        "amount_usd": wf_fm["payroll_usd"],
        "amount_bdt": wf_fm["payroll_bdt"],
        "allocation_method": "Monthly Factory Workforce Payroll Register",
        "event_year": wf_fm["calendar_year"],
    })

    # Category 5: Industrial Utilities from fact_sustainability_monthly
    sm = fact_sustainability_monthly
    sm_fx = np.array([macro_map.loc[(y, m), "bdt_usd_exchange_rate"] for y, m in zip(sm["calendar_year"], sm["calendar_month"])], dtype=np.float64)
    cost_part_utl = pd.DataFrame({
        "transaction_date_key": sm["date_key"],
        "transaction_date": sm["month_start_date"],
        "company_key": sm["company_key"],
        "factory_key": sm["factory_key"],
        "cost_category_key": 5,
        "production_batch_key": 0,
        "order_line_key": 0,
        "reference_quantity": sm["electricity_consumption_kwh"],
        "currency_code": "BDT",
        "bdt_usd_exchange_rate": sm_fx,
        "amount_usd": sm["utility_cost_usd"],
        "amount_bdt": sm["utility_cost_bdt"],
        "allocation_method": "Monthly Factory Metered Utility Ledger",
        "event_year": sm["calendar_year"],
    })

    # Categories 4 (Factory Overhead), 6 (Maintenance & Depreciation), 7 (Compliance & Quality), 10 (Admin), 11 (Financing), 12 (Subcontract)
    # Generate for each active factory-month (6 categories * ~5,500 factory-months = ~33,000 rows)
    extra_cat_rows = []
    for cat_k, mult_bdt, alloc_label in [
        (4, 1450000.0, "Factory Floor Supervision & Overhead Allocation"),
        (6, 980000.0, "Machinery Maintenance & Depreciation Schedule"),
        (7, 520000.0, "Quality Assurance Lab &RSC/Accord Audit Ledger"),
        (10, 880000.0, "Corporate Merchandising & G&A Apportionment"),
        (11, 760000.0, "Working Capital & Back-to-Back L/C Finance Charge"),
        (12, 410000.0, "Peak Season External Wash/Embroidery Subcontract"),
    ]:
        yr_scale = 0.65 + 0.85 * ((sm["calendar_year"].to_numpy() - 2006) / 19.0)
        # Post-2013 Rana Plaza compliance jump for category 7
        if cat_k == 7:
            yr_scale = np.where(sm["calendar_year"].to_numpy() >= 2013, yr_scale * 1.65, yr_scale)
        # Post-2022 interest rate jump for category 11
        if cat_k == 11:
            yr_scale = np.where(sm["calendar_year"].to_numpy() >= 2022, yr_scale * 1.55, yr_scale)

        amt_bdt = np.round(mult_bdt * yr_scale * rng.uniform(0.82, 1.22, size=len(sm)), 2)
        amt_usd = np.round(amt_bdt / sm_fx, 2)
        extra_cat_rows.append(pd.DataFrame({
            "transaction_date_key": sm["date_key"],
            "transaction_date": sm["month_start_date"],
            "company_key": sm["company_key"],
            "factory_key": sm["factory_key"],
            "cost_category_key": cat_k,
            "production_batch_key": 0,
            "order_line_key": 0,
            "reference_quantity": sm["monthly_output_pcs"].astype(np.float64),
            "currency_code": "BDT",
            "bdt_usd_exchange_rate": sm_fx,
            "amount_usd": amt_usd,
            "amount_bdt": amt_bdt,
            "allocation_method": alloc_label,
            "event_year": sm["calendar_year"],
        }))

    # Categories 8 (Inland Logistics) & 9 (International Freight) aggregated by factory-month from fact_shipment_line (~9,500 rows)
    sh_dt = pd.to_datetime(fact_shipment_line["actual_ship_date"])
    sh_grp = fact_shipment_line.assign(
        ym_key=(sh_dt.dt.year * 10000 + sh_dt.dt.month * 100 + 1),
        m_dt=[datetime.date(y, m, 1) for y, m in zip(sh_dt.dt.year, sh_dt.dt.month)],
        sh_yr=sh_dt.dt.year,
        sh_mo=sh_dt.dt.month,
    ).groupby(["company_key", "factory_key", "ym_key", "m_dt", "sh_yr", "sh_mo", "event_year"], as_index=False).agg(
        ship_qty=("shipped_qty_pcs", "sum"),
        frt_usd=("freight_cost_usd", "sum"),
        inl_usd=("inland_logistics_cost_usd", "sum"),
    )
    sh_grp["fx"] = np.array([macro_map.loc[(y, m), "bdt_usd_exchange_rate"] for y, m in zip(sh_grp["sh_yr"], sh_grp["sh_mo"])], dtype=np.float64)
    sh_grp["frt_usd"] = np.round(sh_grp["frt_usd"], 2)
    sh_grp["frt_bdt"] = np.round(sh_grp["frt_usd"] * sh_grp["fx"], 2)
    sh_grp["inl_usd"] = np.round(sh_grp["inl_usd"], 2)
    sh_grp["inl_bdt"] = np.round(sh_grp["inl_usd"] * sh_grp["fx"], 2)

    cost_part_inl = pd.DataFrame({
        "transaction_date_key": sh_grp["ym_key"],
        "transaction_date": sh_grp["m_dt"],
        "company_key": sh_grp["company_key"],
        "factory_key": sh_grp["factory_key"],
        "cost_category_key": 8,
        "production_batch_key": 0,
        "order_line_key": 0,
        "reference_quantity": sh_grp["ship_qty"].astype(np.float64),
        "currency_code": "USD",
        "bdt_usd_exchange_rate": np.round(sh_grp["fx"], 4),
        "amount_usd": np.round(sh_grp["inl_usd"], 2),
        "amount_bdt": np.round(sh_grp["inl_bdt"], 2),
        "allocation_method": "Shipment Dispatch Inland Haulage & C&F Voucher",
        "event_year": sh_grp["event_year"],
    })

    cost_part_frt = pd.DataFrame({
        "transaction_date_key": sh_grp["ym_key"],
        "transaction_date": sh_grp["m_dt"],
        "company_key": sh_grp["company_key"],
        "factory_key": sh_grp["factory_key"],
        "cost_category_key": 9,
        "production_batch_key": 0,
        "order_line_key": 0,
        "reference_quantity": sh_grp["ship_qty"].astype(np.float64),
        "currency_code": "USD",
        "bdt_usd_exchange_rate": np.round(sh_grp["fx"], 4),
        "amount_usd": np.round(sh_grp["frt_usd"], 2),
        "amount_bdt": np.round(sh_grp["frt_bdt"], 2),
        "allocation_method": "Export Forwarder Ocean/Air Freight Settlement",
        "event_year": sh_grp["event_year"],
    })

    fact_cost_transaction = pd.concat(
        [cost_part_dm, cost_part_dl, cost_part_utl, cost_part_inl, cost_part_frt] + extra_cat_rows,
        ignore_index=True
    )
    cost_keys = np.arange(1, len(fact_cost_transaction) + 1, dtype=np.int64)
    cost_ids = [
        f"CST-{yr}-{k:07d}" for yr, k in zip(fact_cost_transaction["event_year"], cost_keys)
    ]
    fact_cost_transaction.insert(0, "cost_transaction_key", cost_keys)
    fact_cost_transaction.insert(1, "cost_transaction_id", cost_ids)

    return (
        fact_workforce_monthly,
        fact_sustainability_monthly,
        fact_inventory_snapshot_monthly,
        fact_cost_transaction,
    )


def generate_all_datasets(seed: int = SEED) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    t0 = time.time()
    print("1/5 Building macroeconomic context (2006-2025)...")
    df_macro = build_macro_monthly(seed)

    print("2/5 Building dimension tables...")
    dims = generate_all_dimensions(seed)

    print("3/5 Generating sales orders & order line bridge...")
    df_so, dim_order_line = generate_sales_and_order_lines(dims, df_macro, target_rows=240000, seed=seed)
    dims["dim_order_line"] = dim_order_line

    print("4/5 Generating production batches, material consumption, quality inspections & shipments...")
    (
        df_so,
        fact_production_batch,
        fact_material_consumption,
        fact_quality_inspection,
        fact_shipment_line,
    ) = generate_production_and_quality_and_shipments(df_so, dims, df_macro, seed=seed)

    print("5/5 Generating procurement POs, supplier deliveries, inventory snapshots, workforce, sustainability & cost transactions...")
    fact_purchase_order_line, fact_supplier_delivery = generate_procurement_and_supplier_deliveries(
        fact_material_consumption, dims, df_macro, target_po_lines=245000, seed=seed
    )
    (
        fact_workforce_monthly,
        fact_sustainability_monthly,
        fact_inventory_snapshot_monthly,
        fact_cost_transaction,
    ) = generate_monthly_snapshots_and_costs(
        dims,
        df_macro,
        fact_production_batch,
        fact_material_consumption,
        fact_quality_inspection,
        fact_shipment_line,
        seed=seed,
    )

    facts = {
        "fact_sales_order_line": df_so,
        "fact_purchase_order_line": fact_purchase_order_line,
        "fact_supplier_delivery": fact_supplier_delivery,
        "fact_production_batch": fact_production_batch,
        "fact_material_consumption": fact_material_consumption,
        "fact_quality_inspection": fact_quality_inspection,
        "fact_shipment_line": fact_shipment_line,
        "fact_inventory_snapshot_monthly": fact_inventory_snapshot_monthly,
        "fact_cost_transaction": fact_cost_transaction,
        "fact_workforce_monthly": fact_workforce_monthly,
        "fact_sustainability_monthly": fact_sustainability_monthly,
        "fact_macro_monthly": df_macro,
    }

    elapsed = time.time() - t0
    total_rows = sum(len(v) for v in dims.values()) + sum(len(v) for v in facts.values())
    print(f"Completed full generation of {len(dims)} dimensions and {len(facts)} facts ({total_rows:,} total rows) in {elapsed:.1f}s.")
    return dims, facts


if __name__ == "__main__":
    dims, facts = generate_all_datasets()
    for k, v in dims.items():
        print(f"DIM  | {k:34s} | {len(v):10,d} rows")
    for k, v in facts.items():
        print(f"FACT | {k:34s} | {len(v):10,d} rows")
