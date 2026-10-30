"""
generate_dimensions.py
Generates all 10 relational dimension tables for the 20-year Bangladesh RMG Supply Chain Intelligence platform:
1. dim_date (7,305 rows: 2006-01-01 to 2025-12-31)
2. dim_company (8 fictional Bangladesh RMG manufacturing groups)
3. dim_factory (26 factories across Gazipur, Savar, Ashulia, Narayanganj, Chattogram, Mymensingh, Cumilla, Dhaka)
4. dim_factory_line (188 production lines with shift patterns, capacities, and opening/closing dates)
5. dim_supplier (180 domestic & international raw material/packaging suppliers)
6. dim_buyer (52 international retail/brand buyers across EU, USA, UK, Canada, and Non-Traditional markets)
7. dim_product (125 garment styles across Knitwear, Woven, Denim, Sweater, and Activewear)
8. dim_material (64 raw material, yarn, fabric, dye/chemical, trim, and packaging items)
9. dim_cost_category (12 standardized cost & expense categories)
10. dim_order_line (generated during fact_sales_order_line creation to maintain 1:1 conformed bridge integrity)
"""

import datetime
import numpy as np
import pandas as pd

SEED = 20261026


def generate_dim_date() -> pd.DataFrame:
    # Exact Eid-ul-Fitr and Eid-ul-Adha dates in Bangladesh (2006-2025)
    eid_ul_fitr_dates = {
        2006: [datetime.date(2006, 10, 24)],
        2007: [datetime.date(2007, 10, 13)],
        2008: [datetime.date(2008, 10, 2)],
        2009: [datetime.date(2009, 9, 21)],
        2010: [datetime.date(2010, 9, 10)],
        2011: [datetime.date(2011, 8, 31)],
        2012: [datetime.date(2012, 8, 19)],
        2013: [datetime.date(2013, 8, 8)],
        2014: [datetime.date(2014, 7, 28)],
        2015: [datetime.date(2015, 7, 18)],
        2016: [datetime.date(2016, 7, 6)],
        2017: [datetime.date(2017, 6, 26)],
        2018: [datetime.date(2018, 6, 15)],
        2019: [datetime.date(2019, 6, 5)],
        2020: [datetime.date(2020, 5, 25)],
        2021: [datetime.date(2021, 5, 14)],
        2022: [datetime.date(2022, 5, 3)],
        2023: [datetime.date(2023, 4, 22)],
        2024: [datetime.date(2024, 4, 10)],
        2025: [datetime.date(2025, 3, 31)],
    }

    eid_ul_adha_dates = {
        2006: [datetime.date(2006, 1, 11), datetime.date(2006, 12, 31)],
        2007: [datetime.date(2007, 12, 20)],
        2008: [datetime.date(2008, 12, 9)],
        2009: [datetime.date(2009, 11, 28)],
        2010: [datetime.date(2010, 11, 17)],
        2011: [datetime.date(2011, 11, 7)],
        2012: [datetime.date(2012, 10, 26)],
        2013: [datetime.date(2013, 10, 15)],
        2014: [datetime.date(2014, 10, 5)],
        2015: [datetime.date(2015, 9, 25)],
        2016: [datetime.date(2016, 9, 13)],
        2017: [datetime.date(2017, 9, 2)],
        2018: [datetime.date(2018, 8, 22)],
        2019: [datetime.date(2019, 8, 12)],
        2020: [datetime.date(2020, 8, 1)],
        2021: [datetime.date(2021, 7, 21)],
        2022: [datetime.date(2022, 7, 10)],
        2023: [datetime.date(2023, 6, 29)],
        2024: [datetime.date(2024, 6, 17)],
        2025: [datetime.date(2025, 6, 7)],
    }

    # Build lookup sets for Ramadan (29 days prior to Eid-ul-Fitr) and 3-day Eid holidays
    ramadan_dates = set()
    eid_holidays = {}
    for yr, fitr_list in eid_ul_fitr_dates.items():
        for fitr_dt in fitr_list:
            for d_back in range(1, 30):
                ramadan_dates.add(fitr_dt - datetime.timedelta(days=d_back))
            for d_off in (-1, 0, 1, 2):
                eid_holidays[fitr_dt + datetime.timedelta(days=d_off)] = "Eid-ul-Fitr Festival Holiday"
    for yr, adha_list in eid_ul_adha_dates.items():
        for adha_dt in adha_list:
            for d_off in (-1, 0, 1, 2):
                eid_holidays[adha_dt + datetime.timedelta(days=d_off)] = "Eid-ul-Adha Festival Holiday"

    fixed_holidays = {
        (2, 21): "International Mother Language Day (Shaheed Dibosh)",
        (3, 17): "National Day / Birthday of Father of the Nation",
        (3, 26): "Independence and National Day",
        (4, 14): "Pahela Baishakh (Bangla New Year)",
        (5, 1): "May Day (International Workers' Day)",
        (12, 16): "Victory Day of Bangladesh",
    }

    start_dt = datetime.date(2006, 1, 1)
    end_dt = datetime.date(2025, 12, 31)
    total_days = (end_dt - start_dt).days + 1

    rows = []
    for i in range(total_days):
        dt = start_dt + datetime.timedelta(days=i)
        yr = dt.year
        mo = dt.month
        dy = dt.day
        date_key = yr * 10000 + mo * 100 + dy

        # Weekday: Monday=1 ... Sunday=7
        iso_weekday = dt.isoweekday()
        weekday_name = dt.strftime("%A")
        # In Bangladesh RMG factories, Friday is the primary weekly holiday
        is_weekend = iso_weekday == 5

        # Fiscal Year (Bangladesh: July to June)
        if mo >= 7:
            fy_start = yr
            fy_end = yr + 1
            fiscal_month = mo - 6
            fiscal_quarter = ((mo - 7) // 3) + 1
        else:
            fy_start = yr - 1
            fy_end = yr
            fiscal_month = mo + 6
            fiscal_quarter = ((mo + 5) // 3) + 1

        fiscal_year = f"FY{fy_start}-{str(fy_end)[-2:]}"
        fiscal_quarter_label = f"{fiscal_year}-Q{fiscal_quarter}"

        # Month start / end
        is_month_start = dy == 1
        next_day = dt + datetime.timedelta(days=1)
        is_month_end = next_day.month != mo
        is_leap_year = (yr % 4 == 0 and yr % 100 != 0) or (yr % 400 == 0)

        # Public holidays & Ramadan
        is_ramadan = dt in ramadan_dates
        holiday_name = eid_holidays.get(dt, fixed_holidays.get((mo, dy), "None"))
        is_public_holiday = holiday_name != "None"
        is_working_day = (not is_weekend) and (not is_public_holiday)

        # International Apparel Buying & Production Seasonality
        if mo in (11, 12, 1, 2):
            buying_season = "Spring/Summer (SS) Peak Manufacturing & Shipment"
        elif mo in (3, 4):
            buying_season = "Spring/Summer Late Drop & Autumn/Winter Sampling"
        elif mo in (5, 6, 7, 8):
            buying_season = "Autumn/Winter (AW) & Holiday Peak Manufacturing"
        else:
            buying_season = "Holiday Re-orders & Spring/Summer Early Booking"

        if mo in (6, 7, 8, 9):
            bd_climate_season = "Monsoon (High Humidity & Port/Inland Transit Risk)"
        elif mo in (11, 12, 1, 2):
            bd_climate_season = "Dry Winter (Optimal Manufacturing & Utility Stability)"
        else:
            bd_climate_season = "Pre-Monsoon Hot Summer (Peak Cooling Electricity Load)"

        rows.append({
            "date_key": date_key,
            "full_date": dt,
            "day_of_month": dy,
            "day_of_year": dt.timetuple().tm_yday,
            "iso_weekday": iso_weekday,
            "weekday_name": weekday_name,
            "iso_week_of_year": int(dt.isocalendar()[1]),
            "calendar_month": mo,
            "month_name": dt.strftime("%B"),
            "month_short": dt.strftime("%b"),
            "year_month": f"{yr:04d}-{mo:02d}",
            "calendar_quarter": ((mo - 1) // 3) + 1,
            "calendar_quarter_label": f"{yr}-Q{((mo - 1) // 3) + 1}",
            "calendar_year": yr,
            "fiscal_year": fiscal_year,
            "fiscal_year_numeric": fy_end,
            "fiscal_quarter": fiscal_quarter,
            "fiscal_quarter_label": fiscal_quarter_label,
            "fiscal_month": fiscal_month,
            "is_leap_year": is_leap_year,
            "is_weekend": is_weekend,
            "is_month_start": is_month_start,
            "is_month_end": is_month_end,
            "is_public_holiday": is_public_holiday,
            "holiday_name": holiday_name,
            "is_ramadan_period": is_ramadan,
            "is_eid_festival_window": "Eid" in holiday_name,
            "is_working_day": is_working_day,
            "apparel_buying_season": buying_season,
            "bangladesh_climate_season": bd_climate_season,
        })

    return pd.DataFrame(rows)


def generate_dim_company() -> pd.DataFrame:
    companies = [
        {
            "company_key": 1,
            "company_code": "PADMA",
            "company_name": "Padma Composite Knitwear Ltd.",
            "operating_archetype": "Vertically Integrated Fiber-to-Fashion Knit Composite",
            "year_established": 1998,
            "primary_product_specialization": "Knit Tops, Polos, Jersey & Activewear",
            "business_model": "Spinning-Knitting-Dyeing-Sewing Composite FOB",
            "trade_association": "BKMEA & BGMEA",
            "headquarters_city": "Dhaka",
            "backward_linkage_level": "High (75% In-House Yarn & Knit Fabric)",
            "active_from_date": datetime.date(2006, 1, 1),
            "active_to_date": datetime.date(2025, 12, 31),
            "is_currently_active": True,
            "base_market_share_weight": 0.195,
        },
        {
            "company_key": 2,
            "company_code": "MEGHNA",
            "company_name": "Meghna Woven & Apparels Group",
            "operating_archetype": "High-Volume Multi-Factory Woven & Bottoms Group",
            "year_established": 1995,
            "primary_product_specialization": "Woven Dress Shirts, Chinos & Casual Trousers",
            "business_model": "Scale-Driven FOB with In-House Washing & Packaging",
            "trade_association": "BGMEA",
            "headquarters_city": "Dhaka",
            "backward_linkage_level": "Medium (In-House Trims/Wash, Imported Woven Fabric)",
            "active_from_date": datetime.date(2006, 1, 1),
            "active_to_date": datetime.date(2025, 12, 31),
            "is_currently_active": True,
            "base_market_share_weight": 0.210,
        },
        {
            "company_key": 3,
            "company_code": "KARNAPHULI",
            "company_name": "Karnaphuli Denim & Jeans Co.",
            "operating_archetype": "Port-Cluster (CEPZ) Premium Denim & Wash Specialist",
            "year_established": 2001,
            "primary_product_specialization": "Five-Pocket Denim Jeans, Jackets & Laser-Wash Casuals",
            "business_model": "Design-to-Delivery FOB with Advanced Wet Processing",
            "trade_association": "BGMEA",
            "headquarters_city": "Chattogram",
            "backward_linkage_level": "Medium-High (In-House R&D, Laser/Ozone Wash, Mixed Fabric)",
            "active_from_date": datetime.date(2006, 1, 1),
            "active_to_date": datetime.date(2025, 12, 31),
            "is_currently_active": True,
            "base_market_share_weight": 0.145,
        },
        {
            "company_key": 4,
            "company_code": "JAMUNA",
            "company_name": "Jamuna Eco-Knit & Sustainable Attire",
            "operating_archetype": "Green-Certified Lean Knitwear Manufacturer",
            "year_established": 2009,
            "primary_product_specialization": "Organic Cotton T-Shirts, Eco-Polos & Loungewear",
            "business_model": "Resource-Efficient High-Compliance Knit FOB",
            "trade_association": "BKMEA",
            "headquarters_city": "Narayanganj",
            "backward_linkage_level": "Medium-High (In-House Eco-Knitting & Biological ETP Dyeing)",
            "active_from_date": datetime.date(2009, 3, 1),
            "active_to_date": datetime.date(2025, 12, 31),
            "is_currently_active": True,
            "base_market_share_weight": 0.105,
        },
        {
            "company_key": 5,
            "company_code": "BRAHMAPUTRA",
            "company_name": "Brahmaputra Textiles & Denim Mills",
            "operating_archetype": "Fabric-First Integrated Denim Mill & Garment Exporter",
            "year_established": 2003,
            "primary_product_specialization": "Stretch Denim, Selvedge Jeans & Heavy Workwear",
            "business_model": "Vertical Denim Weaving Mill + Garment Sewing Units",
            "trade_association": "BGMEA & BTMA",
            "headquarters_city": "Mymensingh",
            "backward_linkage_level": "High (In-House Rope Dyeing, Denim Weaving & Finishing)",
            "active_from_date": datetime.date(2006, 1, 1),
            "active_to_date": datetime.date(2025, 12, 31),
            "is_currently_active": True,
            "base_market_share_weight": 0.125,
        },
        {
            "company_key": 6,
            "company_code": "SURMA",
            "company_name": "Surma Jacquard & Sweaters Ltd.",
            "operating_archetype": "Automated Flat-Knit Sweater & Winterwear Specialist",
            "year_established": 2000,
            "primary_product_specialization": "Acrylic/Cotton/Wool Pullovers, Cardigans & Jacquard Knits",
            "business_model": "Seasonal Heavy-Gauge & Computerized Jacquard Knitting",
            "trade_association": "BGMEA",
            "headquarters_city": "Gazipur",
            "backward_linkage_level": "Medium (Yarn Dyeing & Computerized Flat-Knitting)",
            "active_from_date": datetime.date(2006, 1, 1),
            "active_to_date": datetime.date(2025, 12, 31),
            "is_currently_active": True,
            "base_market_share_weight": 0.085,
        },
        {
            "company_key": 7,
            "company_code": "TEESTA",
            "company_name": "Teesta Automated Apparel Systems",
            "operating_archetype": "Tech-Forward Synthetic & Man-Made Fiber (MMF) Innovator",
            "year_established": 2012,
            "primary_product_specialization": "Performance Sportswear, Athleisure & Technical Outerwear",
            "business_model": "Automated CAD/Cutting & High-Value MMF FOB",
            "trade_association": "BGMEA",
            "headquarters_city": "Gazipur",
            "backward_linkage_level": "Low-Medium (Imported Technical MMF Fabrics, High Automation)",
            "active_from_date": datetime.date(2012, 6, 1),
            "active_to_date": datetime.date(2025, 12, 31),
            "is_currently_active": True,
            "base_market_share_weight": 0.090,
        },
        {
            "company_key": 8,
            "company_code": "DHALESWARI",
            "company_name": "Dhaleswari Heritage Garments Ltd.",
            "operating_archetype": "Legacy Basic Woven/Knit Subcontract & FOB Manufacturer",
            "year_established": 1992,
            "primary_product_specialization": "Basic Woven Shirts & Entry-Level Cotton T-Shirts",
            "business_model": "Low-Margin Basic FOB & Subcontracting (Closed Post-COVID)",
            "trade_association": "BGMEA",
            "headquarters_city": "Dhaka",
            "backward_linkage_level": "Low (Pure Cut-Make-Trim / Sourced Fabric)",
            "active_from_date": datetime.date(2006, 1, 1),
            "active_to_date": datetime.date(2020, 10, 31),
            "is_currently_active": False,
            "base_market_share_weight": 0.045,
        },
    ]
    return pd.DataFrame(companies)


def generate_dim_factory() -> pd.DataFrame:
    # 26 factories across the 8 companies with realistic opening/closure dates and locations
    factories_spec = [
        # Company 1: PADMA (4 factories)
        (1, "FAC-01", "Padma Knit Composite Unit-1", "Gazipur", "Tongi BSCIC Industrial Area", "Knit Tops & Jersey", "Circular Knitting, Auto-Dyeing & Modular Sewing", 10, 220000, datetime.date(2006, 1, 1), None, "Tier-1 High Compliance (RSC/Accord Remediated)", 0.84, 1.00),
        (1, "FAC-02", "Padma Knit Composite Unit-2", "Gazipur", "Konabari Industrial Belt", "Knit Polos & Fleece", "Automated Spreading & High-Speed Sewing", 9, 200000, datetime.date(2006, 1, 1), None, "Tier-1 High Compliance (RSC/Accord Remediated)", 0.85, 0.99),
        (1, "FAC-03", "Padma Narayanganj Knit Park", "Narayanganj", "Fatullah Knit Cluster", "Fine-Gauge Knitwear", "Integrated Knitting & Garmenting", 8, 175000, datetime.date(2008, 4, 1), None, "Tier-1 High Compliance (Green Modernized)", 0.87, 0.97),
        (1, "FAC-04", "Padma Eco-Active Studio Unit-4", "Gazipur", "Sreepur Industrial Corridor", "Seamless & Active Knitwear", "Digital Printing, Laser Cutting & Lean Lines", 7, 165000, datetime.date(2016, 7, 1), None, "Tier-1 Eco-Design Benchmark", 0.91, 0.95),
        # Company 2: MEGHNA (5 factories)
        (2, "FAC-05", "Meghna Woven Apparels Unit-1", "Savar", "DEPZ Extension Corridor", "Woven Dress & Casual Shirts", "High-Volume Progressive Bundle Lines", 10, 210000, datetime.date(2006, 1, 1), None, "Tier-1 High Compliance (RSC/Accord Remediated)", 0.81, 1.01),
        (2, "FAC-06", "Meghna Bottoms & Chino Plant", "Ashulia", "Jamgora Industrial Zone", "Twill Chinos & Cargo Trousers", "Automated Pocket Welt & Garment Wash", 9, 195000, datetime.date(2006, 1, 1), None, "Tier-1 High Compliance (RSC/Accord Remediated)", 0.82, 1.00),
        (2, "FAC-07", "Meghna Gazipur Woven Complex", "Gazipur", "Kaliakoir Industrial Park", "Woven Tops & Blouses", "Computerized Cutting & Modular Sewing", 8, 180000, datetime.date(2010, 1, 1), None, "Tier-1 High Compliance", 0.84, 0.98),
        (2, "FAC-08", "Meghna Casualwear Unit-4", "Savar", "Hemayetpur Industrial Area", "Woven Bottoms & Shorts", "Standard Bundle Sewing Lines", 7, 150000, datetime.date(2006, 1, 1), datetime.date(2023, 6, 30), "Tier-2 Standard Compliance (Consolidated in 2023)", 0.76, 1.04),
        (2, "FAC-09", "Meghna Smart Woven Park Unit-5", "Gazipur", "Rajendrapur Green Zone", "Premium Shirts & Structured Woven", "Automated Hanger System (UPS) & RFID Floor", 8, 190000, datetime.date(2018, 1, 1), None, "Tier-1 Eco-Design Benchmark", 0.90, 0.94),
        # Company 3: KARNAPHULI (3 factories)
        (3, "FAC-10", "Karnaphuli CEPZ Denim Plant-1", "Chattogram", "Chattogram EPZ (CEPZ)", "Five-Pocket Denim Jeans", "Laser Whiskering, Ozone Wash & Heavy Denim Lines", 9, 195000, datetime.date(2006, 1, 1), None, "Tier-1 EPZ International Compliance", 0.86, 0.98),
        (3, "FAC-11", "Karnaphuli CEPZ Casuals Plant-2", "Chattogram", "Chattogram EPZ (CEPZ)", "Denim Jackets & Washed Twills", "Advanced Wet Processing & Automated Sewing", 8, 175000, datetime.date(2006, 1, 1), None, "Tier-1 EPZ International Compliance", 0.85, 0.99),
        (3, "FAC-12", "Karnaphuli Eco-Wash & Jeans Unit-3", "Chattogram", "Karnaphuli EPZ (KEPZ)", "Premium Stretch & Selvedge Denim", "Zero-Liquid-Discharge (ZLD) Wash & Robotics", 7, 165000, datetime.date(2014, 9, 1), None, "Tier-1 Eco-Design Benchmark", 0.90, 0.96),
        # Company 4: JAMUNA (3 factories)
        (4, "FAC-13", "Jamuna Green Knitwear Plant-1", "Narayanganj", "Siddhirganj Eco-Industrial Belt", "Organic Cotton T-Shirts & Polos", "Daylight Harvesting, Solar Roof & Lean Lines", 7, 160000, datetime.date(2009, 3, 1), None, "Tier-1 Eco-Design Benchmark", 0.89, 0.96),
        (4, "FAC-14", "Jamuna Sustainable Attire Unit-2", "Narayanganj", "Araihazar Industrial Park", "Sustainable Loungewear & Kids Knit", "Biological ETP, Rainwater Recycling & Auto-Cut", 7, 155000, datetime.date(2013, 1, 1), None, "Tier-1 Eco-Design Benchmark", 0.90, 0.95),
        (4, "FAC-15", "Jamuna Cumilla Eco-Apparel Unit-3", "Cumilla", "Cumilla EPZ", "Recycled Cotton & Blended Knitwear", "Ultra-Low Energy Modular Lines", 6, 140000, datetime.date(2017, 6, 1), None, "Tier-1 Eco-Design Benchmark", 0.92, 0.93),
        # Company 5: BRAHMAPUTRA (3 factories)
        (5, "FAC-16", "Brahmaputra Mymensingh Denim Mill & Sewing-1", "Mymensingh", "Bhaluka Industrial Corridor", "Heavy Denim Jeans & Workwear", "Rope-Dyed Weaving + Integrated Garment Lines", 8, 180000, datetime.date(2006, 1, 1), None, "Tier-1 High Compliance", 0.83, 0.99),
        (5, "FAC-17", "Brahmaputra Gazipur Denim Unit-2", "Gazipur", "Mawna Industrial Belt", "Stretch Denim & Casual Bottoms", "Automated Slasher/Wash & Progressive Sewing", 8, 175000, datetime.date(2007, 7, 1), None, "Tier-1 High Compliance", 0.84, 1.00),
        (5, "FAC-18", "Brahmaputra Bhaluka Green Denim Unit-3", "Mymensingh", "Bhaluka Industrial Corridor", "Eco-Washed Fashion Denim", "Cogeneration Captive Power & Laser Wash", 6, 145000, datetime.date(2015, 3, 1), None, "Tier-1 Eco-Design Benchmark", 0.88, 0.96),
        # Company 6: SURMA (3 factories)
        (6, "FAC-19", "Surma Flat-Knit Sweater Plant-1", "Gazipur", "Board Bazar Industrial Area", "12GG & 7GG Pullovers & Cardigans", "Semi-Auto Upgraded to Computerized Jacquard (2014)", 7, 130000, datetime.date(2006, 1, 1), None, "Tier-2 Upgraded to Tier-1 (Post-2013)", 0.79, 1.02),
        (6, "FAC-20", "Surma Savar Jacquard Unit-2", "Savar", "Baipail Industrial Belt", "5GG Heavy Winter Sweaters & Knits", "Computerized Flat-Bed Knitting & Linking", 6, 120000, datetime.date(2006, 1, 1), None, "Tier-1 High Compliance", 0.82, 1.00),
        (6, "FAC-21", "Surma Automated Knit-Studio Unit-3", "Gazipur", "joydebpur Industrial Zone", "3D Whole-Garment & Fine Merino/Cotton Knits", "Automated Whole-Garment Flat Knitting", 5, 110000, datetime.date(2015, 1, 1), None, "Tier-1 High Compliance", 0.89, 0.95),
        # Company 7: TEESTA (3 factories)
        (7, "FAC-22", "Teesta Tech-Apparel Plant-1", "Gazipur", "Gazipur Chowrasta Tech Park", "Synthetic Sportswear & Performance Tops", "Ultrasonic Bonding, Seam Sealing & Auto-Cut", 7, 155000, datetime.date(2012, 6, 1), None, "Tier-1 High Compliance", 0.88, 0.97),
        (7, "FAC-23", "Teesta Cumilla EPZ Activewear Unit-2", "Cumilla", "Cumilla EPZ", "Athleisure Leggings, Jackets & Tracksuits", "Automated Synthetic Handling & CAD Studio", 6, 145000, datetime.date(2014, 1, 1), None, "Tier-1 EPZ International Compliance", 0.90, 0.95),
        (7, "FAC-24", "Teesta Outerwear & Technical Unit-3", "Gazipur", "Kaliakoir Hi-Tech Corridor", "Padded Jackets, Windbreakers & Rainwear", "Quilting, Down-Fill & Seam-Taping Lines", 6, 135000, datetime.date(2018, 7, 1), None, "Tier-1 Eco-Design Benchmark", 0.91, 0.94),
        # Company 8: DHALESWARI (2 legacy factories - closed in 2014 and 2020)
        (8, "FAC-25", "Dhaleswari Keraniganj Unit-1", "Dhaka", "Keraniganj Apparel Cluster", "Basic Woven Shirts & Bottoms", "Conventional Manual Bundle Lines", 6, 105000, datetime.date(2006, 1, 1), datetime.date(2014, 8, 31), "Tier-3 Legacy (Closed Post-2013 Audit Remediation)", 0.71, 1.08),
        (8, "FAC-26", "Dhaleswari Ashulia Annex Unit-2", "Ashulia", "Narsinghapur Industrial Area", "Basic Cotton T-Shirts & Casual Shirts", "Conventional Sewing & Manual Cutting", 6, 115000, datetime.date(2006, 1, 1), datetime.date(2020, 10, 31), "Tier-2 Basic Compliance (Closed Oct 2020 COVID Shock)", 0.74, 1.06),
    ]

    rows = []
    for idx, spec in enumerate(factories_spec, start=1):
        (
            comp_key, fac_code, fac_name, city, zone, spec_prod,
            tech, num_lines, monthly_cap, open_dt, close_dt,
            comp_profile, base_eff, unit_cost_mult
        ) = spec
        rows.append({
            "factory_key": idx,
            "company_key": comp_key,
            "factory_code": fac_code,
            "factory_name": fac_name,
            "location_city": city,
            "industrial_zone": zone,
            "product_specialization": spec_prod,
            "production_technology": tech,
            "design_line_count": num_lines,
            "base_monthly_capacity_pcs": monthly_cap,
            "opening_date": open_dt,
            "closure_date": close_dt if close_dt is not None else datetime.date(9999, 12, 31),
            "is_closed": close_dt is not None,
            "compliance_profile": comp_profile,
            "base_efficiency_factor": base_eff,
            "unit_cost_multiplier": unit_cost_mult,
        })
    return pd.DataFrame(rows)


def generate_dim_factory_line(df_factory: pd.DataFrame) -> pd.DataFrame:
    rows = []
    line_key = 1
    shift_patterns = [
        ("Single 8-Hour Shift + 2-Hour Max Overtime", 10.0),
        ("Standard 8-Hour Shift + Seasonal Overtime", 9.5),
        ("Double 8-Hour Shift (High Utilization)", 15.0),
    ]
    for _, fac in df_factory.iterrows():
        n_lines = int(fac["design_line_count"])
        per_line_cap = int(round(fac["base_monthly_capacity_pcs"] / n_lines))
        for ln in range(1, n_lines + 1):
            sp_label, daily_hrs = shift_patterns[(ln - 1) % len(shift_patterns)]
            rows.append({
                "production_line_key": line_key,
                "factory_key": int(fac["factory_key"]),
                "company_key": int(fac["company_key"]),
                "line_code": f"{fac['factory_code']}-L{ln:02d}",
                "line_name": f"{fac['factory_name']} - Line {ln:02d}",
                "line_specialization": fac["product_specialization"],
                "shift_pattern": sp_label,
                "standard_daily_hours": daily_hrs,
                "operators_per_line": 42 if "Sweater" not in fac["product_specialization"] else 28,
                "helpers_per_line": 14 if "Sweater" not in fac["product_specialization"] else 8,
                "monthly_standard_capacity_pcs": per_line_cap,
                "active_from_date": fac["opening_date"],
                "active_to_date": fac["closure_date"],
            })
            line_key += 1
    return pd.DataFrame(rows)


def generate_dim_buyer(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 10)
    # Calibrated to EPB/BGMEA destination shares: EU (~48%), USA (~21%), UK (~11%), Canada (~3.5%), Non-Traditional (~16.5%)
    buyer_specs = [
        # EU (24 buyers)
        ("Germany", "European Union (EU)", "Traditional", "Fast Fashion Retailer"),
        ("Germany", "European Union (EU)", "Traditional", "Hypermarket & Value Chain"),
        ("Germany", "European Union (EU)", "Traditional", "Eco & Sustainable Lifestyle Brand"),
        ("Germany", "European Union (EU)", "Traditional", "Department Store Group"),
        ("Germany", "European Union (EU)", "Traditional", "Athletic & Sportswear Brand"),
        ("Spain", "European Union (EU)", "Traditional", "Global Fast Fashion Group"),
        ("Spain", "European Union (EU)", "Traditional", "Casual & Denim Specialty Chain"),
        ("Spain", "European Union (EU)", "Traditional", "Department Store & Youth Brand"),
        ("France", "European Union (EU)", "Traditional", "Family Value Apparel Chain"),
        ("France", "European Union (EU)", "Traditional", "Mid-Market Fashion & Menswear"),
        ("France", "European Union (EU)", "Traditional", "Sportswear & Outdoor Retailer"),
        ("France", "European Union (EU)", "Traditional", "Hypermarket Private Label"),
        ("Italy", "European Union (EU)", "Traditional", "Denim & Knitwear Fashion Brand"),
        ("Italy", "European Union (EU)", "Traditional", "Contemporary Casual Retailer"),
        ("Italy", "European Union (EU)", "Traditional", "Childrenswear & Family Chain"),
        ("Netherlands", "European Union (EU)", "Traditional", "Denim Lifestyle Specialist"),
        ("Netherlands", "European Union (EU)", "Traditional", "Value Apparel & Basics Retailer"),
        ("Netherlands", "European Union (EU)", "Traditional", "Sustainable Knitwear Brand"),
        ("Sweden", "European Union (EU)", "Traditional", "Global Fast Fashion & Conscious Line"),
        ("Sweden", "European Union (EU)", "Traditional", "Nordic Outdoor & Casual Brand"),
        ("Poland", "European Union (EU)", "Traditional", "Central European Value Fashion Group"),
        ("Poland", "European Union (EU)", "Traditional", "Casual & Youth Apparel Chain"),
        ("Denmark", "European Union (EU)", "Traditional", "Multi-Brand Menswear & Denim Group"),
        ("Belgium", "European Union (EU)", "Traditional", "European Workwear & Corporate Uniforms"),
        # USA (11 buyers)
        ("United States", "North America (USA)", "Traditional", "Mass Merchandiser & Hypermarket"),
        ("United States", "North America (USA)", "Traditional", "Global Denim & Heritage Brand"),
        ("United States", "North America (USA)", "Traditional", "Specialty Casual & Mall Retailer"),
        ("United States", "North America (USA)", "Traditional", "Performance Athletic & Sportswear Giant"),
        ("United States", "North America (USA)", "Traditional", "Off-Price & Value Department Store"),
        ("United States", "North America (USA)", "Traditional", "American Workwear & Rugged Apparel"),
        ("United States", "North America (USA)", "Traditional", "Menswear & Formal Shirt Brand"),
        ("United States", "North America (USA)", "Traditional", "Youth & Collegiate Casual Chain"),
        ("United States", "North America (USA)", "Traditional", "Outdoor & Active Lifestyle Brand"),
        ("United States", "North America (USA)", "Traditional", "Private Label Apparel Wholesaler"),
        ("United States", "North America (USA)", "Traditional", "Eco-Conscious Direct-to-Consumer Brand"),
        # UK (6 buyers)
        ("United Kingdom", "United Kingdom (UK)", "Traditional", "High-Street Value Fashion Giant"),
        ("United Kingdom", "United Kingdom (UK)", "Traditional", "Supermarket Apparel Private Label"),
        ("United Kingdom", "United Kingdom (UK)", "Traditional", "British Heritage Department Store"),
        ("United Kingdom", "United Kingdom (UK)", "Traditional", "UK Online Fast Fashion Platform"),
        ("United Kingdom", "United Kingdom (UK)", "Traditional", "British Casual & Knitwear Brand"),
        ("United Kingdom", "United Kingdom (UK)", "Traditional", "UK Sportswear & Teamwear Specialist"),
        # Canada (3 buyers)
        ("Canada", "North America (Canada)", "Traditional", "Canadian National Supermarket Apparel"),
        ("Canada", "North America (Canada)", "Traditional", "Winterwear, Fleece & Sweater Retailer"),
        ("Canada", "North America (Canada)", "Traditional", "Canadian Athleisure & Basics Brand"),
        # Non-Traditional / Emerging Markets (8 buyers)
        ("Japan", "Asia-Pacific (Non-Traditional)", "Non-Traditional", "Japanese Minimalist Basics & Lifewear Giant"),
        ("Japan", "Asia-Pacific (Non-Traditional)", "Non-Traditional", "Tokyo Specialty Denim & Casual Select Shop"),
        ("Australia", "Asia-Pacific (Non-Traditional)", "Non-Traditional", "Australian Department & Value Chain"),
        ("Australia", "Asia-Pacific (Non-Traditional)", "Non-Traditional", "Southern Hemisphere Workwear & Surf Brand"),
        ("India", "South Asia (Non-Traditional)", "Non-Traditional", "Indian Organized Retail & Fashion Chain"),
        ("Turkiye", "Middle East & Eurasia (Non-Traditional)", "Non-Traditional", "Eurasian Fast Fashion & Denim Retailer"),
        ("South Korea", "Asia-Pacific (Non-Traditional)", "Non-Traditional", "Korean Streetwear & Casual Apparel Group"),
        ("United Arab Emirates", "Middle East & Eurasia (Non-Traditional)", "Non-Traditional", "Gulf Lifestyle & Hypermarket Retail Group"),
    ]

    prefixes = [
        "Aurelia", "Nordic", "Vanguard", "Meridian", "Crestline", "Solstice", "Harbor", "Stratos",
        "Kestrel", "Boreal", "Zephyr", "Vertex", "Alba", "Veritas", "Monarch", "orion",
        "Pacifica", "Sovereign", "Caledonia", "Atlas", "Lumina", "Equinox", "Summit", "Cascade",
        "Velour", "indigo", "Pinnacle", "Horizon", "Sterling", "Nova", "Arbor", "pulse",
        "urban", "Beacon", "Prism", "Halcyon", "Zenith", "Fjord", "Sierra", "Metro",
        "Thames", "Maple", "Sakura", "Southern", "Deccan", "Bosphorus", "Hanul", "Oasis",
        "Continental", "Crown", "Emerald", "Cobalt"
    ]

    payment_terms_pool = [
        "At Sight Irrevocable L/C",
        "60 Days Deferred Usance L/C",
        "90 Days Deferred Usance L/C",
        "Open Account / Telegraphic Transfer (TT) 45 Days",
        "Open Account / Telegraphic Transfer (TT) 60 Days",
    ]

    rows = []
    for idx, (country, region, mkt_class, seg) in enumerate(buyer_specs, start=1):
        prefix = prefixes[idx - 1].capitalize()
        buyer_code = f"BUY-{idx:03d}"
        buyer_name = f"{prefix} {seg.split()[0]} {country[:3].upper()} Ltd."

        if "Denim" in seg or "Workwear" in seg:
            pref_prod = "Denim & Woven Bottoms"
        elif "Athletic" in seg or "Sportswear" in seg or "Outdoor" in seg or "Athleisure" in seg:
            pref_prod = "Activewear, Knitwear & Outerwear"
        elif "Winterwear" in seg:
            pref_prod = "Sweaters, Fleece & Heavy Knitwear"
        elif "Menswear" in seg:
            pref_prod = "Woven Shirts, Chinos & Polos"
        else:
            pref_prod = "Full-Basket Knitwear, Woven & Denim"

        # Non-traditional and eco buyers onboarded progressively over the 20-year window
        if mkt_class == "Non-Traditional" and idx % 2 == 0:
            start_yr = int(rng.choice([2009, 2011, 2013, 2015]))
        elif "Eco" in seg or "Sustainable" in seg or "Online" in seg:
            start_yr = int(rng.choice([2009, 2010, 2012, 2014]))
        else:
            start_yr = int(rng.choice([2006, 2006, 2006, 2007, 2008]))

        # Assign Pareto volume weight (top buyers hold much larger share)
        raw_weight = float(rng.pareto(a=1.65) + 0.35)
        if country in ("Germany", "United States", "United Kingdom", "Spain", "France", "Japan"):
            raw_weight *= 1.45

        rows.append({
            "buyer_key": idx,
            "buyer_code": buyer_code,
            "buyer_name": buyer_name,
            "customer_segment": seg,
            "destination_country": country,
            "market_region": region,
            "market_classification": mkt_class,
            "product_preference": pref_prod,
            "order_size_tier": "High-Volume Core Program" if raw_weight > 1.8 else ("Mid-Size Seasonal" if raw_weight > 0.9 else "Boutique / Spot Repeat"),
            "payment_terms": payment_terms_pool[idx % len(payment_terms_pool)],
            "quality_tolerance_aql": 1.5 if ("Japan" in country or "Eco" in seg or "Athletic" in seg) else 2.5,
            "compliance_strictness": "Strict Tier-1 Only" if mkt_class == "Traditional" or country == "Japan" else "Standard Audited",
            "relationship_start_date": datetime.date(start_yr, 1, 1),
            "relationship_end_date": datetime.date(9999, 12, 31),
            "demand_share_weight": round(raw_weight, 4),
        })

    df = pd.DataFrame(rows)
    df["demand_share_weight"] = (df["demand_share_weight"] / df["demand_share_weight"].sum()).round(6)
    return df


def generate_dim_material() -> pd.DataFrame:
    # 64 raw materials across Cotton/Yarn, Knit Fabric, Woven/Denim Fabric, Dyes/Chemicals, Trims/Accessories, Packaging
    materials = []
    mat_specs = [
        # Yarn & Raw Fiber (12 items)
        ("Yarn", "30/1 Combed Compact Cotton Yarn", "KG", "Domestic Spinning & India Import", 18, 3.15, "Dry Humidity-Controlled Yarn Store"),
        ("Yarn", "26/1 Carded Ring-Spun Cotton Yarn", "KG", "Domestic Spinning & India Import", 16, 2.75, "Dry Humidity-Controlled Yarn Store"),
        ("Yarn", "40/1 Combed Organic Cotton Yarn (GOTS)", "KG", "India & Turkiye Import", 28, 3.85, "Certified Organic Segregated Store"),
        ("Yarn", "20/1 Open-End (OE) Cotton Yarn", "KG", "Domestic Spinning", 14, 2.30, "Standard Yarn Warehouse"),
        ("Yarn", "30/1 CVC (60% Cotton / 40% Polyester) Melange Yarn", "KG", "Domestic & China Import", 22, 2.95, "Standard Yarn Warehouse"),
        ("Yarn", "24/1 PC (65% Polyester / 35% Cotton) Blended Yarn", "KG", "Domestic & Indonesia Import", 20, 2.55, "Standard Yarn Warehouse"),
        ("Yarn", "75D/72F Recycled Polyester DTY Filament Yarn", "KG", "China & Taiwan Import", 32, 2.40, "Synthetic Filament Store"),
        ("Yarn", "40D Bare Elastane / Spandex Core Yarn", "KG", "China & Vietnam Import", 30, 6.80, "Temperature-Controlled Elastane Store"),
        ("Yarn", "2/28 Nm High-Bulk Acrylic Sweater Yarn", "KG", "China & Indonesia Import", 28, 3.40, "Sweater Cone Warehouse"),
        ("Yarn", "2/32 Nm Cotton-Acrylic (60/40) Jacquard Yarn", "KG", "Domestic & China Import", 24, 3.75, "Sweater Cone Warehouse"),
        ("Yarn", "2/36 Nm Merino Wool-Blend Sweater Yarn", "KG", "China & Australia Import", 38, 8.90, "Climate-Controlled Wool Store"),
        ("Cotton Fiber", "Raw Upland / Shankar-6 Ginned Cotton Bale", "KG", "India, USA & West Africa Import", 42, 1.95, "Bonded Raw Cotton Bale Godown"),
        # Knit Fabrics (10 items)
        ("Knit Fabric", "160 GSM 100% Cotton Single Jersey Fabric (Dyed)", "KG", "In-House / Domestic Composite", 15, 4.90, "Tubular/Open-Width Fabric Racks"),
        ("Knit Fabric", "180 GSM 95/5 Cotton-Spandex Single Jersey", "KG", "In-House / Domestic Composite", 16, 5.45, "Relaxation Fabric Racks"),
        ("Knit Fabric", "200 GSM 100% Cotton Pique Polo Fabric", "KG", "In-House / Domestic Composite", 16, 5.20, "Fabric Roll Racks"),
        ("Knit Fabric", "220 GSM Organic Cotton Interlock Knit Fabric", "KG", "In-House / Domestic Eco-Mill", 18, 6.30, "Certified Organic Fabric Store"),
        ("Knit Fabric", "280 GSM 3-Thread Brushed CVC Fleece Fabric", "KG", "Domestic & China Import", 22, 5.60, "Heavy Roll Fabric Store"),
        ("Knit Fabric", "240 GSM French Terry Unbrushed Loopback Fabric", "KG", "In-House / Domestic Composite", 17, 5.35, "Fabric Roll Racks"),
        ("Knit Fabric", "1x1 Cotton-Elastane Collar & Cuff Rib (220 GSM)", "KG", "In-House / Domestic Composite", 14, 5.10, "Accessory Fabric Bins"),
        ("Knit Fabric", "145 GSM Recycled Polyester Moisture-Wicking Mesh", "KG", "China & Taiwan Import", 34, 6.15, "Synthetic Fabric Racks"),
        ("Knit Fabric", "210 GSM Nylon-Spandex 4-Way Stretch Tricot", "KG", "China & South Korea Import", 36, 7.80, "Technical Activewear Store"),
        ("Knit Fabric", "175 GSM Viscose-Elastane Drape Jersey", "KG", "China & India Import", 30, 5.85, "Standard Fabric Store"),
        # Woven & Denim Fabrics (14 items)
        ("Woven Fabric", "100% Cotton Poplin Shirting Fabric (40x40, 120 GSM)", "YARD", "China & India Import", 35, 1.65, "Woven Inspection & Roll Racks"),
        ("Woven Fabric", "100% Cotton Yarn-Dyed Check Oxford Shirting", "YARD", "China & India Import", 38, 1.95, "Woven Inspection & Roll Racks"),
        ("Woven Fabric", "65/35 Easy-Care Poly-Cotton Dress Shirting", "YARD", "China & Indonesia Import", 32, 1.45, "Woven Inspection & Roll Racks"),
        ("Woven Fabric", "98/2 Cotton-Spandex Stretch Peached Twill (245 GSM)", "YARD", "Domestic & China Import", 28, 2.35, "Bottoms Fabric Warehouse"),
        ("Woven Fabric", "100% Cotton Heavy Canvas / Ripstop Cargo Fabric", "YARD", "China & Pakistan Import", 36, 2.50, "Bottoms Fabric Warehouse"),
        ("Woven Fabric", "Linen-Cotton Blended Summer Woven Shirting", "YARD", "China Import", 40, 2.85, "Specialty Woven Racks"),
        ("Woven Fabric", "12.5 oz 100% Cotton Indigo Rope-Dyed Rigid Denim", "YARD", "In-House / Domestic & Pakistan", 22, 2.40, "Denim Roll Warehouse"),
        ("Woven Fabric", "11.0 oz 98/2 Cotton-Elastane Comfort Stretch Denim", "YARD", "In-House / Domestic & Pakistan", 22, 2.65, "Denim Roll Warehouse"),
        ("Woven Fabric", "10.5 oz Bi-Stretch Cotton-Poly-Spandex High-Recovery Denim", "YARD", "China & Turkiye Import", 34, 3.10, "Denim Roll Warehouse"),
        ("Woven Fabric", "13.5 oz Red-Cast Selvedge Premium Denim Fabric", "YARD", "Japan & Turkiye Import", 42, 4.75, "Premium Bonded Denim Store"),
        ("Woven Fabric", "9.5 oz Black-Sulfur Dyed Stretch Denim", "YARD", "In-House / Domestic Denim Mill", 20, 2.55, "Denim Roll Warehouse"),
        ("Woven Fabric", "75D TPU-Laminated Waterproof Breathable Ripstop Shell", "YARD", "China & Taiwan Import", 38, 3.45, "Technical Outerwear Store"),
        ("Woven Fabric", "210T Polyester Taffeta Lining Fabric", "YARD", "China Import", 28, 0.78, "Lining & Interlining Racks"),
        ("Woven Fabric", "120 GSM Synthetic Down / Polyester Wadding Insulation", "YARD", "China & Domestic", 22, 1.15, "High-Volume Loft Store"),
        # Dyes & Wet-Processing Chemicals (8 items)
        ("Dyes & Chemicals", "Reactive Bifunctional Dye Conc. (ZDHC MRSL Level-1)", "KG", "Germany, India & China Import", 30, 8.40, "Hazmat Chemical & Dye Store"),
        ("Dyes & Chemicals", "Disperse High-Fastness Dye for Polyester/MMF", "KG", "China & India Import", 30, 7.60, "Hazmat Chemical & Dye Store"),
        ("Dyes & Chemicals", "Pre-Reduced Liquid Indigo Vat Dye", "KG", "Germany & China Import", 34, 6.90, "Denim Dye Vat Storage"),
        ("Dyes & Chemicals", "Cellulase Bio-Polishing & Denim Wash Enzyme", "KG", "Denmark & India Import", 28, 5.20, "Cool Chemical Drum Store"),
        ("Dyes & Chemicals", "Hydrophilic Silicone Fabric Softener Emulsion", "KG", "Domestic & Import", 18, 2.80, "Chemical Drum Store"),
        ("Dyes & Chemicals", "Hydrogen Peroxide (50% Industrial Bleaching Grade)", "KG", "Domestic Chemical Plants", 10, 0.72, "Ventilated Oxidizer Store"),
        ("Dyes & Chemicals", "Caustic Soda Flakes & Glaubers Salt Auxiliary", "KG", "Domestic & India Import", 12, 0.55, "Dry Chemical Store"),
        ("Dyes & Chemicals", "ETP Biological Coagulant & Polyelectrolyte Dosing Pack", "KG", "Domestic & Import", 14, 1.95, "ETP Utility Store"),
        # Trims & Garment Accessories (12 items)
        ("Trims & Accessories", "Spun Polyester Sewing Thread (40/2 & 60/3 Ticket)", "CONE", "Domestic Thread Mills", 10, 1.15, "Trim & Thread Bin System"),
        ("Trims & Accessories", "Core-Spun Poly-Poly Heavy Denim Sewing Thread", "CONE", "Domestic & China", 12, 1.65, "Trim & Thread Bin System"),
        ("Trims & Accessories", "YKK / Metal Brass Auto-Lock Jeans Zipper", "PCS", "Domestic MNC Plant & Import", 14, 0.22, "Secured Trim Room"),
        ("Trims & Accessories", "Nylon Coil & Waterproof Reverse-Coil Jacket Zipper", "PCS", "China & Domestic", 20, 0.48, "Secured Trim Room"),
        ("Trims & Accessories", "Lead-Free Brass Shank Button & Copper Rivet Set", "SET", "China & Domestic", 18, 0.14, "Metal Trim Bin System"),
        ("Trims & Accessories", "4-Hole Chalk / Horn-Effect Resin Shirt Button", "GROSS", "Domestic & China", 12, 0.95, "Trim & Button Store"),
        ("Trims & Accessories", "Woven Damask Main Brand Label & Size Tab Set", "SET", "Domestic Garment Accessories", 10, 0.06, "Buyer-Segregated Label Vault"),
        ("Trims & Accessories", "Printed Satin Wash-Care & Multi-Language Content Label", "PCS", "Domestic Garment Accessories", 9, 0.03, "Buyer-Segregated Label Vault"),
        ("Trims & Accessories", "Woven Fusible Shirt Collar & Placket Interlining", "YARD", "China & Domestic", 16, 0.52, "Interlining Rack"),
        ("Trims & Accessories", "Knitted Jacquard Waistband Elastic (38mm)", "YARD", "Domestic Narrow Fabrics", 12, 0.28, "Trim & Elastic Racks"),
        ("Trims & Accessories", "Jacquard Drawcord with Metal/Silicone Aglet Tip", "PCS", "Domestic Accessories", 12, 0.11, "Trim Bin System"),
        ("Trims & Accessories", "Leatherette / Jacron Back-Waist Brand Patch", "PCS", "Domestic & China", 15, 0.16, "Buyer-Segregated Label Vault"),
        # Packaging Materials (8 items)
        ("Packaging", "FSC-Certified Printed Retail Hangtag & Barcode Sticker", "SET", "Domestic Printing & Packaging", 9, 0.07, "Finishing & Packing Store"),
        ("Packaging", "RFID-Embedded UHF Retail Inventory Smart Tag", "PCS", "China & Taiwan Nominated Supplier", 21, 0.13, "High-Security RFID Vault"),
        ("Packaging", "Recycled LDPE Self-Adhesive Garment Polybag", "PCS", "Domestic Packaging Unit", 8, 0.04, "Packing Consumables Store"),
        ("Packaging", "Acid-Free Tissue Paper, Collar Butterfly & Clip Set", "SET", "Domestic Packaging Unit", 8, 0.05, "Shirt Packing Store"),
        ("Packaging", "7-Ply Corrugated Master Export Carton Box", "PCS", "Domestic Carton Plant", 7, 1.35, "Dry Carton Mezzanine"),
        ("Packaging", "Molded Recycled Plastic Garment Hanger (GOH Program)", "PCS", "Domestic & Nominated Import", 12, 0.18, "Packing Store"),
        ("Packaging", "Silica Gel / Calcium Chloride Anti-Mold Desiccant Pouch", "PCS", "Domestic & China", 10, 0.03, "Dry Packing Cabinet"),
        ("Packaging", "PP Carton Strapping Band, Gum Tape & Corner Board Kit", "SET", "Domestic Packaging Unit", 7, 0.25, "Dispatch Warehouse Store"),
    ]

    for idx, (cat, name, uom, src_prof, lead_days, base_usd, storage) in enumerate(mat_specs, start=1):
        is_imp = "Import" in src_prof and not src_prof.startswith("Domestic")
        if src_prof.startswith("In-House"):
            src_class = "In-House Backward Linkage / Domestic"
        elif "Domestic" in src_prof and "Import" in src_prof:
            src_class = "Dual-Sourced (Domestic & Import)"
        elif "Domestic" in src_prof:
            src_class = "Domestic Back-to-Back L/C"
        else:
            src_class = "Direct Import (Bonded Warehouse)"

        materials.append({
            "material_key": idx,
            "material_code": f"MAT-{idx:03d}",
            "material_name": name,
            "material_category": cat,
            "material_group": (
                "Cotton & Yarn" if cat in ("Yarn", "Cotton Fiber")
                else ("Fabric" if "Fabric" in cat
                      else ("Dyes & Chemicals" if "Dyes" in cat
                            else ("Trims" if "Trims" in cat else "Packaging")))
            ),
            "base_uom": uom,
            "sourcing_profile": src_prof,
            "sourcing_classification": src_class,
            "is_primarily_imported": is_imp,
            "standard_lead_time_days": lead_days,
            "base_unit_cost_usd_2015": base_usd,
            "storage_characteristics": storage,
            "is_critical_path_material": cat in ("Yarn", "Cotton Fiber", "Knit Fabric", "Woven Fabric") or "RFID" in name or "Zipper" in name,
        })
    return pd.DataFrame(materials)


def generate_dim_supplier(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 20)
    # 180 suppliers across Bangladesh (domestic backward linkage & packaging), China, India, Pakistan, Turkiye, Vietnam, Indonesia, Taiwan, etc.
    country_specs = [
        ("Bangladesh", "Domestic", "Spinning & Knit Yarn Mill", "Cotton & Yarn", 14, "Back-to-Back L/C 60 Days", 34),
        ("Bangladesh", "Domestic", "Garment Trims, Labels & Packaging Manufacturer", "Trims & Packaging", 9, "Back-to-Back L/C 45 Days", 38),
        ("Bangladesh", "Domestic", "Knit & Denim Fabric Composite Mill", "Fabric", 17, "Back-to-Back L/C 60 Days", 22),
        ("Bangladesh", "Domestic", "Industrial Chemical & Auxiliary Distributor", "Dyes & Chemicals", 11, "Local Credit 30 Days", 10),
        ("China", "Imported", "Woven & Synthetic Technical Fabric Mill", "Fabric", 34, "Master L/C at Sight / 90 Days Usance", 28),
        ("China", "Imported", "Specialty Trims, Zippers, RFID & Outerwear Components", "Trims & Packaging", 26, "60 Days Usance L/C", 12),
        ("India", "Imported", "Combed/Organic Cotton Yarn & Shirting Fabric Exporter", "Cotton, Yarn & Fabric", 24, "60 Days Usance L/C", 16),
        ("Pakistan", "Imported", "Denim & Heavy Twill Bottoms Fabric Mill", "Fabric", 28, "60 Days Usance L/C", 6),
        ("Turkiye", "Imported", "Premium Stretch Denim & Organic Yarn Mill", "Cotton, Yarn & Fabric", 36, "90 Days Usance L/C", 4),
        ("Indonesia", "Imported", "Blended Spun Yarn & Woven Shirting Mill", "Cotton, Yarn & Fabric", 29, "60 Days Usance L/C", 4),
        ("Taiwan", "Imported", "High-Performance MMF Tricot & Laminated Shell Mill", "Fabric", 35, "At Sight L/C", 3),
        ("Germany", "Imported", "ZDHC Certified Reactive Dyes & Textile Auxiliaries", "Dyes & Chemicals", 38, "90 Days Usance L/C", 3),
    ]

    prefixes = [
        "Delta", "Karnaphuli", "Shitalakhya", "Titas", "Sonargaon", "Purbachal", "Barendra", "Sundarban",
        "Eastern", "Bengal", "Dhaka", "Gazipur", "Narayanganj", "Chattogram", "Silver", "Golden",
        "Crown", "Pioneer", "Apex", "Prime", "United", "Reliance", "National", "Standard",
        "Shandong", "Zhejiang", "Jiangsu", "Guangdong", "Shaoxing", "Ningbo", "Suzhou", "Hangzhou",
        "Gujarat", "TamilNadu", "Maharashtra", "Tirupur", "Coimbatore", "Ludhiana", "Karachi", "Lahore",
        "Faisalabad", "Bursa", "Istanbul", "Bandung", "Taipei", "Rhine", "Bavaria"
    ]

    rows = []
    sup_idx = 1
    for country, dom_imp, sup_type, mat_focus, base_lt, pay_terms, count in country_specs:
        for c in range(count):
            pfx = prefixes[(sup_idx * 3 + c) % len(prefixes)]
            sup_code = f"SUP-{sup_idx:03d}"
            sup_name = f"{pfx} {sup_type.split()[0]} {country[:3].upper()}-{sup_idx:03d} Ltd."

            lead_time = int(max(5, base_lt + rng.integers(-3, 5)))
            reliability = round(float(np.clip(rng.normal(0.86 if dom_imp == "Domestic" else 0.83, 0.065), 0.64, 0.98)), 3)
            start_yr = int(rng.choice([2006, 2006, 2006, 2007, 2008, 2010, 2012, 2015]))
            end_yr = 2020 if (sup_idx % 29 == 0 and start_yr <= 2012) else 9999

            # Pareto concentration weight
            weight = float(rng.pareto(a=1.8) + 0.3)

            rows.append({
                "supplier_key": sup_idx,
                "supplier_code": sup_code,
                "supplier_name": sup_name,
                "supplier_type": sup_type,
                "origin_country": country,
                "domestic_import_classification": dom_imp,
                "major_materials_supplied": mat_focus,
                "average_lead_time_days": lead_time,
                "lead_time_variability_days": round(float(max(1.2, (1.0 - reliability) * 22.0)), 1),
                "payment_terms": pay_terms,
                "baseline_reliability_score": reliability,
                "minimum_order_value_usd": int(rng.choice([1500, 3000, 5000, 8000, 12000])) if dom_imp == "Imported" else int(rng.choice([500, 1000, 2500])),
                "active_from_date": datetime.date(start_yr, 1, 1),
                "active_to_date": datetime.date(end_yr, 12, 31),
                "is_currently_active": end_yr == 9999,
                "spend_share_weight": round(weight, 4),
            })
            sup_idx += 1

    df = pd.DataFrame(rows)
    df["spend_share_weight"] = (df["spend_share_weight"] / df["spend_share_weight"].sum()).round(6)
    return df


def generate_dim_product(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 30)
    # 125 garment products across Knitwear, Woven Tops, Woven Bottoms, Denim, Sweaters, and MMF Activewear/Outerwear
    product_archetypes = [
        # (Category, Knit/Woven, Garment Type, Fabric Type, Target Market, Value Tier, Complexity, SMV range, Base Price USD, Primary Mat Key, Mat Consumption per pc, Count)
        ("Knit Tops", "Knit", "Basic Crew-Neck T-Shirt", "160 GSM 100% Cotton Single Jersey", "Mass Basics & Casual", "Basic Volume", "Low", (5.5, 7.5), (2.25, 3.10), 13, 0.21, 18),
        ("Knit Tops", "Knit", "Elastane Fitted Fashion Tee", "180 GSM 95/5 Cotton-Spandex Jersey", "High-Street Fashion", "Mid-Tier Fashion", "Medium", (7.5, 10.5), (3.40, 4.65), 14, 0.23, 12),
        ("Knit Tops", "Knit", "Classic Pique Polo Shirt", "200 GSM 100% Cotton Pique", "Menswear & Corporate Casual", "Mid-Tier Fashion", "Medium", (11.5, 15.0), (4.50, 6.20), 15, 0.28, 14),
        ("Knit Tops", "Knit", "Organic Cotton Eco-Tee & Lounge Top", "220 GSM Organic Cotton Interlock", "Sustainable & Conscious Retail", "Premium / Eco", "Medium", (8.5, 12.0), (4.80, 6.90), 16, 0.25, 10),
        ("Knit Fleece & Hoodies", "Knit", "Brushed Fleece Pullover Hoodie", "280 GSM CVC 3-Thread Fleece", "Autumn/Winter Casual", "Mid-Tier Fashion", "Medium-High", (16.0, 22.0), (6.80, 9.50), 17, 0.52, 10),
        ("Knit Fleece & Hoodies", "Knit", "French Terry Jogger & Sweatshirt", "240 GSM Loopback French Terry", "Athleisure & Youth", "Mid-Tier Fashion", "Medium", (14.0, 18.5), (5.60, 7.90), 18, 0.44, 8),
        ("Woven Shirts", "Woven", "Long-Sleeve Formal Poplin Dress Shirt", "100% Cotton Poplin 40x40", "Menswear & Department Store", "Mid-Tier Fashion", "High", (18.0, 24.0), (6.20, 8.80), 23, 1.55, 10),
        ("Woven Shirts", "Woven", "Yarn-Dyed Check Casual Button-Down Shirt", "100% Cotton Yarn-Dyed Oxford", "Casual & Smart-Casual", "Mid-Tier Fashion", "High", (19.0, 25.5), (6.80, 9.40), 24, 1.60, 8),
        ("Woven Bottoms", "Woven", "Stretch Peached Twill Chino Trouser", "98/2 Cotton-Spandex Twill 245 GSM", "Menswear & Specialty Retail", "Mid-Tier Fashion", "High", (21.0, 27.0), (7.40, 10.20), 26, 1.48, 8),
        ("Woven Bottoms", "Woven", "Multi-Pocket Ripstop Cargo Pant", "100% Cotton Heavy Canvas/Ripstop", "Workwear & Casual Utility", "Mid-Tier Fashion", "High", (25.0, 33.0), (8.50, 11.80), 27, 1.72, 5),
        ("Denim Apparel", "Woven", "Classic 5-Pocket Indigo Rigid Jeans", "12.5 oz 100% Cotton Indigo Denim", "Mass & Heritage Denim", "Mid-Tier Fashion", "High", (20.0, 26.0), (7.80, 10.50), 29, 1.52, 6),
        ("Denim Apparel", "Woven", "Laser-Whiskered Comfort Stretch Jeans", "11.0 oz 98/2 Stretch Denim", "Specialty Denim & EU/US Retail", "Premium / Wash-Intensive", "High", (23.0, 31.0), (9.20, 13.40), 30, 1.48, 6),
        ("Denim Apparel", "Woven", "Selvedge / Bi-Stretch Designer Denim & Jacket", "13.5 oz Selvedge / Bi-Stretch Denim", "Premium Brand & Select Shop", "Premium / Eco", "Very High", (28.0, 38.0), (12.80, 17.50), 32, 1.65, 3),
        ("Sweaters & Flat-Knit", "Knit", "7GG / 12GG Acrylic-Cotton Pullover Sweater", "2/28 Nm High-Bulk Acrylic/Cotton Yarn", "Autumn/Winter Retail", "Mid-Tier Fashion", "High", (22.0, 30.0), (6.40, 9.20), 9, 0.38, 4),
        ("Sweaters & Flat-Knit", "Knit", "Computerized Jacquard & Merino-Blend Cardigan", "2/32 Nm Jacquard / Merino-Blend Yarn", "Premium Winterwear", "Premium / Eco", "Very High", (26.0, 36.0), (9.50, 14.20), 11, 0.42, 3),
        ("MMF Activewear & Outerwear", "Knit", "Moisture-Wicking Performance Training Top & Legging", "Recycled Poly Mesh / Nylon-Spandex Tricot", "Athletic & Sportswear", "Premium / Technical", "High", (14.5, 21.0), (6.50, 9.80), 21, 0.30, 5),
        ("MMF Activewear & Outerwear", "Woven", "Waterproof Seam-Sealed Padded Jacket", "75D TPU Ripstop Shell + Taffeta + Wadding", "Outdoor & Technical Outerwear", "Premium / Technical", "Very High", (34.0, 48.0), (14.50, 22.00), 34, 1.85, 5),
    ]

    # Wait: total count above is 18+12+14+10+10+8+10+8+8+5+6+6+3+4+3+5+5 = 135! Let's adjust counts to sum to exactly 125:
    adjusted_counts = [16, 11, 12, 9, 9, 7, 9, 7, 8, 5, 6, 6, 3, 4, 3, 5, 5]  # sum = 125

    rows = []
    prod_idx = 1
    for arch_i, spec in enumerate(product_archetypes):
        (
            cat, kw_class, g_type, fab_type, tgt_mkt, val_tier,
            comp, smv_rng, price_rng, prim_mat_key, mat_cons, _
        ) = spec
        cnt = adjusted_counts[arch_i]
        for k in range(cnt):
            smv = round(float(rng.uniform(smv_rng[0], smv_rng[1])), 2)
            base_price = round(float(rng.uniform(price_rng[0], price_rng[1])), 2)
            cons = round(float(mat_cons * rng.uniform(0.92, 1.10)), 3)

            if "Organic" in g_type or "MMF" in cat or "Laser" in g_type or "Selvedge" in g_type:
                intro_yr = int(rng.choice([2009, 2011, 2012, 2014, 2016]))
            else:
                intro_yr = int(rng.choice([2006, 2006, 2006, 2007, 2008, 2010]))

            disc_yr = 2019 if (prod_idx % 25 == 0 and intro_yr == 2006) else 9999

            if "Sweater" in cat or "Fleece" in cat or "Outerwear" in cat:
                season_prof = "Autumn/Winter Peak (May-Oct Production)"
            elif "Linen" in fab_type or "Crew-Neck" in g_type:
                season_prof = "Spring/Summer Peak (Nov-Apr Production)"
            else:
                season_prof = "Year-Round Core with Dual Season Drops"

            rows.append({
                "product_key": prod_idx,
                "product_code": f"STL-{prod_idx:04d}",
                "style_name": f"{g_type} - Style #{prod_idx:03d}",
                "product_category": cat,
                "knit_woven_classification": kw_class,
                "garment_type": g_type,
                "fabric_type": fab_type,
                "fiber_composition": "Man-Made Fiber (MMF) / Synthetic" if "MMF" in cat else ("Organic Cotton" if "Organic" in g_type else "Cotton & Cotton-Blend"),
                "target_market_segment": tgt_mkt,
                "value_tier": val_tier,
                "manufacturing_complexity": comp,
                "standard_minute_value_smv": smv,
                "primary_material_key": prim_mat_key,
                "primary_material_consumption_per_unit": cons,
                "primary_material_uom": "KG" if kw_class == "Knit" else "YARD",
                "base_fob_unit_price_usd": base_price,
                "seasonality_profile": season_prof,
                "introduction_date": datetime.date(intro_yr, 1, 1),
                "discontinuation_date": datetime.date(disc_yr, 12, 31),
                "is_active_style": disc_yr == 9999,
            })
            prod_idx += 1

    return pd.DataFrame(rows)


def generate_dim_cost_category() -> pd.DataFrame:
    categories = [
        (1, "COST-DM", "Direct Materials (Fabric, Yarn & Dyes)", "Direct Manufacturing Cost", "Variable", "Production Batch / Material Consumption", "COGS - Direct Material"),
        (2, "COST-TRM", "Garment Trims, Accessories & Retail Packaging", "Direct Manufacturing Cost", "Variable", "Production Batch / Order Quantity", "COGS - Direct Material"),
        (3, "COST-DL", "Direct Production Labour & Overtime Payroll", "Direct Manufacturing Cost", "Variable / Step-Fixed", "Factory Monthly Workforce / Standard Minutes", "COGS - Direct Labour"),
        (4, "COST-FOH", "Factory Indirect Supervision & Floor Overhead", "Factory Overhead", "Fixed / Semi-Variable", "Factory Monthly Allocation", "COGS - Factory Overhead"),
        (5, "COST-UTL", "Industrial Utilities (Electricity, Gas, Steam & ETP)", "Factory Overhead", "Semi-Variable", "Factory Monthly Sustainability & Output", "COGS - Factory Overhead"),
        (6, "COST-MNT", "Machinery Preventive Maintenance, Spares & Depreciation", "Factory Overhead", "Semi-Variable", "Factory Line Count & Modernization Level", "COGS - Factory Overhead"),
        (7, "COST-QLT", "Quality Assurance, Lab Testing, Rework & Audit Compliance", "Quality & Compliance Cost", "Variable / Event-Driven", "Inspection & Compliance Audit Events", "COGS - Quality & Compliance"),
        (8, "COST-INL", "Inland Haulage, Covered Van Transport & C&F Port Handling", "Logistics & Selling Expense", "Variable", "Shipment Dispatch Events", "Operating Expense - Selling & Distribution"),
        (9, "COST-FRT", "International Ocean/Air Freight & Forwarder Charges", "Logistics & Selling Expense", "Variable", "Shipment Line (CIF/DDP/Air Recovery)", "Operating Expense - Selling & Distribution"),
        (10, "COST-ADM", "Corporate Administration, Merchandising & IT Systems", "Administrative Expense", "Fixed", "Company Monthly Allocation", "Operating Expense - G&A"),
        (11, "COST-FIN", "Working Capital Interest, L/C Commission & Bank Charges", "Financing Cost", "Semi-Variable", "Company Monthly Working Capital & L/C Volume", "Non-Operating - Finance Cost"),
        (12, "COST-SUB", "Subcontracting & External Washing/Embroidery Charges", "Direct Manufacturing Cost", "Variable", "Peak-Season Capacity Overflow Batches", "COGS - Subcontract & Processing"),
    ]
    rows = []
    for k, code, name, grp, behavior, basis, pnl_line in categories:
        rows.append({
            "cost_category_key": k,
            "cost_category_code": code,
            "cost_category_name": name,
            "cost_group": grp,
            "cost_behavior": behavior,
            "allocation_basis": basis,
            "income_statement_classification": pnl_line,
            "is_direct_production_cost": grp == "Direct Manufacturing Cost",
        })
    return pd.DataFrame(rows)


def generate_all_dimensions(seed: int = SEED) -> dict[str, pd.DataFrame]:
    dim_date = generate_dim_date()
    dim_company = generate_dim_company()
    dim_factory = generate_dim_factory()
    dim_factory_line = generate_dim_factory_line(dim_factory)
    dim_buyer = generate_dim_buyer(seed)
    dim_material = generate_dim_material()
    dim_supplier = generate_dim_supplier(seed)
    dim_product = generate_dim_product(seed)
    dim_cost_category = generate_dim_cost_category()

    return {
        "dim_date": dim_date,
        "dim_company": dim_company,
        "dim_factory": dim_factory,
        "dim_factory_line": dim_factory_line,
        "dim_buyer": dim_buyer,
        "dim_material": dim_material,
        "dim_supplier": dim_supplier,
        "dim_product": dim_product,
        "dim_cost_category": dim_cost_category,
    }


if __name__ == "__main__":
    dims = generate_all_dimensions()
    for name, df in dims.items():
        print(f"{name:22s}: {len(df):6,d} rows | {len(df.columns):2d} cols")
