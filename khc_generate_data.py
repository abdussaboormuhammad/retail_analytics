"""
Kraft Heinz Retail Analytics Data Generator
Generates 12 CPG-realistic CSV datasets for a KHC selling-story dashboard.
Metrics: ACV%, TDP, Velocity, TPR/Feature/Display, Market Share, Volume Decomp.
"""
import pandas as pd
import numpy as np
import os, random
from datetime import date, timedelta

np.random.seed(42)
random.seed(42)

OUT = "/Users/abdussaboor/Documents/github/retail_analytics/data/khc"
os.makedirs(OUT, exist_ok=True)

def save(df, name):
    df.to_csv(f"{OUT}/{name}.csv", index=False)
    print(f"  ✓  {name}.csv  ({len(df):,} rows)")

# ═══════════════════════════════════════════════════════════════════════════════
# MASTER REFERENCE DATA
# ═══════════════════════════════════════════════════════════════════════════════

BRANDS = [
    # (brand_id, brand_name, segment, business_unit, mkt_share_pct, base_acv, has_seasonal)
    ("B01","Heinz Ketchup",      "Taste Elevation","Condiments & Sauces",  28.5, 96.0, True),
    ("B02","Heinz Mustard",      "Taste Elevation","Condiments & Sauces",  18.2, 88.0, True),
    ("B03","Heinz Mayonnaise",   "Taste Elevation","Condiments & Sauces",  11.4, 82.0, True),
    ("B04","A.1. Steak Sauce",   "Taste Elevation","Condiments & Sauces",  42.0, 76.0, False),
    ("B05","Grey Poupon",        "Taste Elevation","Condiments & Sauces",  22.1, 68.0, False),
    ("B06","Classico",           "Taste Elevation","Pasta Sauces",         10.2, 71.0, False),
    ("B07","Philadelphia",       "Taste Elevation","Cheese & Dairy",       34.8, 91.0, True),
    ("B08","Kraft Singles",      "North America Grocery","Cheese & Dairy", 31.5, 89.0, False),
    ("B09","Velveeta",           "North America Grocery","Cheese & Dairy", 55.0, 84.0, False),
    ("B10","Kraft Mac & Cheese", "North America Grocery","Meals",          29.0, 93.0, False),
    ("B11","Lunchables",         "North America Grocery","Meals",          62.0, 88.0, True),
    ("B12","Oscar Mayer",        "North America Grocery","Meats",          21.3, 87.0, True),
    ("B13","Capri Sun",          "North America Grocery","Beverages",      18.5, 85.0, True),
    ("B14","Maxwell House",      "North America Grocery","Coffee",         12.8, 79.0, False),
    ("B15","Ore-Ida",            "North America Grocery","Frozen Foods",   38.0, 86.0, True),
    ("B16","Jell-O",             "North America Grocery","Desserts",       44.0, 83.0, True),
    ("B17","Cool Whip",          "North America Grocery","Desserts",       59.0, 81.0, True),
    ("B18","Kool-Aid",           "North America Grocery","Beverages",      24.0, 77.0, False),
]

SKUS = [
    # (sku_id, brand_id, sku_name, size, tier, list_price, std_cost, is_innovation)
    ("SK001","B01","Heinz Tomato Ketchup","32oz","Core",4.99,1.82,False),
    ("SK002","B01","Heinz Tomato Ketchup","20oz","Core",3.29,1.10,False),
    ("SK003","B01","Heinz Tomato Ketchup","14oz","Core",2.49,0.85,False),
    ("SK004","B01","Heinz Simply Heinz Ketchup","32oz","Premium",5.49,2.10,False),
    ("SK005","B01","Heinz No Sugar Added Ketchup","32oz","Premium",5.79,2.25,True),
    ("SK006","B02","Heinz Yellow Mustard","14oz","Core",2.19,0.72,False),
    ("SK007","B02","Heinz Yellow Mustard","20oz","Core",2.79,0.95,False),
    ("SK008","B03","Heinz Real Mayonnaise","30oz","Core",5.99,2.05,False),
    ("SK009","B03","Heinz Real Mayonnaise","20oz","Core",4.49,1.55,False),
    ("SK010","B04","A.1. Original Steak Sauce","10oz","Core",3.99,1.35,False),
    ("SK011","B04","A.1. Bold & Spicy","10oz","Premium",4.29,1.45,True),
    ("SK012","B05","Grey Poupon Dijon","10oz","Premium",3.49,1.15,False),
    ("SK013","B05","Grey Poupon Country Dijon","10oz","Premium",3.49,1.18,False),
    ("SK014","B06","Classico Tomato & Basil","24oz","Core",3.79,1.28,False),
    ("SK015","B06","Classico Four Cheese","24oz","Core",3.79,1.30,False),
    ("SK016","B06","Classico Spicy Tomato","24oz","Core",3.79,1.28,False),
    ("SK017","B07","Philadelphia Original Cream Cheese","8oz","Core",3.79,1.35,False),
    ("SK018","B07","Philadelphia Original Cream Cheese","16oz","Core",6.29,2.20,False),
    ("SK019","B07","Philadelphia 1/3 Less Fat","8oz","Premium",3.99,1.42,False),
    ("SK020","B07","Philadelphia Strawberry","8oz","Premium",3.99,1.40,True),
    ("SK021","B08","Kraft Singles American","16ct","Core",4.49,1.62,False),
    ("SK022","B08","Kraft Singles 2% Milk","16ct","Core",4.49,1.65,False),
    ("SK023","B08","Kraft Singles Sharp Cheddar","16ct","Premium",4.79,1.72,True),
    ("SK024","B09","Velveeta Original","32oz","Core",6.49,2.35,False),
    ("SK025","B09","Velveeta Shells & Cheese","12oz","Core",2.99,0.92,False),
    ("SK026","B09","Velveeta Shells & Cheese Bacon","12oz","Premium",3.29,1.05,True),
    ("SK027","B10","Kraft Original Mac & Cheese","7.25oz","Core",1.49,0.45,False),
    ("SK028","B10","Kraft Original Mac & Cheese","4-pack","Value",5.49,1.62,False),
    ("SK029","B10","Kraft Deluxe Mac & Cheese","14oz","Premium",3.29,1.05,False),
    ("SK030","B10","Kraft White Cheddar Mac & Cheese","5.5oz","Premium",1.79,0.58,True),
    ("SK031","B11","Lunchables Turkey & American","3.2oz","Core",2.79,1.08,False),
    ("SK032","B11","Lunchables Ham & American","3.2oz","Core",2.79,1.05,False),
    ("SK033","B11","Lunchables Pepperoni Pizza","4.3oz","Core",2.99,1.12,False),
    ("SK034","B11","Lunchables Nachos Cheese Dip","4.4oz","Core",2.99,1.10,False),
    ("SK035","B11","Lunchables Extra Cheesy Pizza","4.2oz","Premium",3.49,1.30,True),
    ("SK036","B12","Oscar Mayer Classic Hot Dogs","10ct","Core",4.49,1.72,False),
    ("SK037","B12","Oscar Mayer Beef Franks","10ct","Premium",5.29,2.05,False),
    ("SK038","B12","Oscar Mayer Turkey Bacon","12oz","Premium",5.49,2.12,False),
    ("SK039","B12","Oscar Mayer Original Bacon","16oz","Core",7.99,3.05,False),
    ("SK040","B12","Oscar Mayer Bologna","16oz","Core",4.29,1.55,False),
    ("SK041","B12","Oscar Mayer Deli Fresh Turkey","9oz","Premium",5.79,2.20,False),
    ("SK042","B13","Capri Sun Strawberry Kiwi","10pk","Core",3.49,1.18,False),
    ("SK043","B13","Capri Sun Fruit Punch","10pk","Core",3.49,1.15,False),
    ("SK044","B13","Capri Sun Pacific Cooler","10pk","Core",3.49,1.18,False),
    ("SK045","B13","Capri Sun 100% Juice","10pk","Premium",3.99,1.40,True),
    ("SK046","B14","Maxwell House Original Medium Roast","30.6oz","Core",9.99,3.65,False),
    ("SK047","B14","Maxwell House Master Blend","11.5oz","Core",5.49,1.98,False),
    ("SK048","B14","Maxwell House Decaf","11.5oz","Premium",5.99,2.15,False),
    ("SK049","B15","Ore-Ida Tater Tots","32oz","Core",5.49,1.95,False),
    ("SK050","B15","Ore-Ida Golden Fries","32oz","Core",4.99,1.78,False),
    ("SK051","B15","Ore-Ida Steak Fries","28oz","Core",4.49,1.62,False),
    ("SK052","B15","Ore-Ida Extra Crispy Fast Food Fries","28oz","Premium",5.29,1.95,True),
    ("SK053","B16","Jell-O Strawberry","3oz","Core",1.19,0.32,False),
    ("SK054","B16","Jell-O Cherry","3oz","Core",1.19,0.32,False),
    ("SK055","B16","Jell-O Instant Pudding Chocolate","3.9oz","Core",1.49,0.42,False),
    ("SK056","B16","Jell-O Instant Pudding Vanilla","3.4oz","Core",1.49,0.40,False),
    ("SK057","B17","Cool Whip Original","8oz","Core",2.99,0.98,False),
    ("SK058","B17","Cool Whip Lite","8oz","Premium",3.19,1.05,False),
    ("SK059","B17","Cool Whip Extra Creamy","8oz","Premium",3.29,1.10,True),
    ("SK060","B18","Kool-Aid Tropical Punch Powder","0.14oz","Value",0.25,0.06,False),
    ("SK061","B18","Kool-Aid Cherry Powder","0.14oz","Value",0.25,0.06,False),
    ("SK062","B18","Kool-Aid Jammers Tropical Punch","10pk","Core",3.29,1.08,False),
]

RETAILERS = [
    # (ret_id, name, channel, khc_tier, mkt_weight, acv_factor, avg_stores)
    ("R01","Walmart",        "Mass",       "Tier 1", 21.0, 1.00, 4600),
    ("R02","Kroger",         "Grocery",    "Tier 1", 13.5, 0.95, 2800),
    ("R03","Target",         "Mass",       "Tier 1",  9.0, 0.92, 1900),
    ("R04","Costco",         "Club",       "Tier 1",  7.5, 0.85,  575),
    ("R05","Publix",         "Grocery",    "Tier 1",  6.0, 0.94, 1330),
    ("R06","Albertsons",     "Grocery",    "Tier 2",  5.5, 0.90, 2280),
    ("R07","Ahold Delhaize", "Grocery",    "Tier 2",  4.8, 0.88, 2000),
    ("R08","H-E-B",          "Grocery",    "Tier 2",  3.2, 0.96,  340),
    ("R09","Dollar General", "Value",      "Tier 2",  3.0, 0.70, 19000),
    ("R10","Amazon Fresh",   "eCommerce",  "Tier 3",  2.0, 0.55,  None),
]

CATEGORIES_COMP = {
    "Condiments & Sauces":  ["Hunt's","French's","Hellmann's","Private Label","Annie's"],
    "Pasta Sauces":         ["Prego","Ragu","Rao's","Private Label"],
    "Cheese & Dairy":       ["Sargento","Land O Lakes","Private Label","Organic Valley"],
    "Meals":                ["Annie's","Campbell's","Private Label","Chef Boyardee"],
    "Meats":                ["Ball Park","Hebrew National","Nathan's","Private Label"],
    "Beverages":            ["Mott's","Juicy Juice","Honest Kids","Private Label"],
    "Coffee":               ["Folgers","Starbucks K-Cup","Private Label","Dunkin'"],
    "Frozen Foods":         ["Birds Eye","Alexia","McCain","Private Label"],
    "Desserts":             ["Snack Pack","Royal","Private Label","Jell-O PL"],
}

REGIONS = {
    "Northeast": ["CT","ME","MA","NH","RI","VT","NJ","NY","PA"],
    "Mid-Atlantic": ["DE","MD","DC","VA","WV","NC","SC"],
    "Southeast": ["FL","GA","AL","MS","TN","KY","AR"],
    "Midwest": ["IL","IN","MI","OH","WI","MN","IA","MO","ND","SD","NE","KS"],
    "Southwest": ["TX","OK","NM","AZ"],
    "Mountain": ["CO","WY","MT","ID","UT","NV"],
    "Pacific": ["CA","OR","WA","AK","HI","HI"],
}

STATES = [s for states in REGIONS.values() for s in states][:50]

FISCAL_WEEKS = pd.date_range("2024-01-01","2024-12-29", freq="W-MON")[:52]

HOLIDAYS = {   # weeks with big promotional opportunities
    4:  "Super Bowl",
    9:  "Valentine's Day",
    14: "Easter",
    18: "Cinco de Mayo",
    22: "Memorial Day",
    27: "July 4th",
    35: "Back to School",
    37: "Labor Day",
    44: "Halloween",
    47: "Thanksgiving",
    48: "Black Friday",
    50: "Christmas",
    52: "New Year's Eve",
}

# Seasonal index per brand per quarter
SEASONALITY = {
    "B01": [0.85, 1.00, 1.35, 0.85],   # Heinz Ketchup peaks summer
    "B02": [0.88, 1.00, 1.28, 0.90],   # Mustard peaks summer
    "B03": [0.88, 0.98, 1.20, 0.95],   # Mayo peaks summer
    "B04": [0.90, 0.95, 1.15, 1.00],   # A.1. peaks summer
    "B05": [1.05, 0.98, 0.92, 1.05],   # Grey Poupon flat
    "B06": [1.00, 0.95, 0.90, 1.15],   # Classico peaks fall
    "B07": [1.05, 0.95, 0.88, 1.12],   # Philly peaks fall/winter (baking)
    "B08": [1.00, 0.98, 0.95, 1.07],   # Kraft Singles slight winter peak
    "B09": [1.08, 0.95, 0.90, 1.07],   # Velveeta peaks winter (Super Bowl)
    "B10": [1.10, 0.95, 0.88, 1.07],   # KMC peaks winter
    "B11": [0.78, 0.92, 1.35, 1.00],   # Lunchables peaks summer/BTS
    "B12": [0.85, 0.98, 1.40, 0.80],   # OM hot dogs peak summer
    "B13": [0.78, 0.88, 1.45, 0.92],   # Capri Sun peaks summer
    "B14": [1.15, 0.95, 0.80, 1.10],   # Maxwell House peaks winter
    "B15": [1.00, 0.95, 1.10, 0.95],   # Ore-Ida slight summer/fall
    "B16": [0.95, 1.05, 1.05, 0.95],   # Jell-O relatively flat
    "B17": [1.08, 0.98, 0.95, 0.99],   # Cool Whip peaks winter (pies)
    "B18": [0.80, 0.88, 1.45, 0.90],   # Kool-Aid summer
}

# YoY trend: brand growth/decline vs prior year
YOY_TREND = {
    "B01": 1.02, "B02": 0.98, "B03": 1.01, "B04": 0.95,
    "B05": 1.04, "B06": 0.93, "B07": 1.06, "B08": 0.97,
    "B09": 0.96, "B10": 1.01, "B11": 1.08, "B12": 0.99,
    "B13": 1.05, "B14": 0.91, "B15": 1.03, "B16": 0.94,
    "B17": 1.02, "B18": 0.96,
}

brand_dict = {b[0]: b for b in BRANDS}
sku_df_raw = pd.DataFrame(SKUS, columns=["sku_id","brand_id","sku_name","size","tier","list_price","std_cost","is_innovation"])

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DIM BRAND
# ═══════════════════════════════════════════════════════════════════════════════
def gen_dim_brand():
    rows = []
    for b in BRANDS:
        bid, name, seg, bu, share, acv, seasonal = b
        ann_rev = round(random.uniform(150, 1800) * 1e6 / 1e6, 1)  # in $M
        rows.append({
            "brand_id": bid, "brand_name": name, "segment": seg,
            "business_unit": bu, "category_market_share_pct": share,
            "base_acv_pct": acv, "has_seasonality": seasonal,
            "yoy_trend": YOY_TREND[bid],
            "revenue_tier": ">$1B" if ann_rev > 1000 else "$500M-$1B" if ann_rev > 500 else "<$500M",
            "is_category_captain": bu in ["Condiments & Sauces","Meats","Cheese & Dairy"],
            "innovation_pipeline": random.randint(1, 5),
        })
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 2. DIM SKU
# ═══════════════════════════════════════════════════════════════════════════════
def gen_dim_sku():
    df = sku_df_raw.copy()
    df["brand_name"] = df["brand_id"].map({b[0]: b[1] for b in BRANDS})
    df["segment"]    = df["brand_id"].map({b[0]: b[2] for b in BRANDS})
    df["business_unit"] = df["brand_id"].map({b[0]: b[3] for b in BRANDS})
    df["upc"] = [f"{random.randint(10**11, 10**12-1)}" for _ in range(len(df))]
    df["margin_pct"] = ((df["list_price"] - df["std_cost"]) / df["list_price"] * 100).round(1)
    df["is_core_item"] = df["tier"] == "Core"
    df["velocity_index"] = [round(random.uniform(0.7, 1.3), 2) for _ in range(len(df))]  # vs category avg
    return df

# ═══════════════════════════════════════════════════════════════════════════════
# 3. DIM RETAILER
# ═══════════════════════════════════════════════════════════════════════════════
def gen_dim_retailer():
    rows = []
    for r in RETAILERS:
        rid, name, channel, tier, wt, acvf, stores = r
        rows.append({
            "retailer_id": rid, "retailer_name": name, "channel": channel,
            "khc_account_tier": tier, "market_weight_pct": wt,
            "acv_factor": acvf, "est_store_count": stores,
            "has_category_review": tier in ["Tier 1"],
            "khc_category_captain": name in ["Walmart","Kroger","Target"],
            "planogram_cycle": "Quarterly" if channel == "Grocery" else "Bi-Annual",
            "promo_compliance_baseline": round(random.uniform(55, 85), 1),
        })
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 4. DIM CALENDAR (Fiscal Weeks)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_dim_calendar():
    rows = []
    for i, week_start in enumerate(FISCAL_WEEKS, 1):
        q = (i-1)//13 + 1
        rows.append({
            "fiscal_week": i,
            "week_start_date": week_start.date().isoformat(),
            "week_end_date": (week_start + timedelta(days=6)).date().isoformat(),
            "month": week_start.month,
            "month_name": week_start.strftime("%B"),
            "quarter": q,
            "fiscal_quarter": f"Q{q}",
            "is_holiday_week": i in HOLIDAYS,
            "holiday_occasion": HOLIDAYS.get(i, ""),
            "is_summer": q == 3,
            "is_back_to_school": 32 <= i <= 37,
            "is_super_bowl": i == 4,
            "is_grilling_season": 20 <= i <= 36,
            "seasonality_index": round(1.0 + 0.3 * np.sin((i/52)*2*np.pi - np.pi/3), 3),
        })
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 5. DIM MARKET
# ═══════════════════════════════════════════════════════════════════════════════
def gen_dim_market():
    rows = []
    for region, states in REGIONS.items():
        for state in states[:50]:
            rows.append({
                "state": state, "region": region,
                "market_size": random.choice(["Large","Medium","Small"]),
                "population_index": round(random.uniform(0.5, 3.0), 2),
                "urbanization": random.choice(["Urban","Suburban","Rural"]),
                "income_index": round(random.uniform(0.7, 1.5), 2),
            })
    return pd.DataFrame(rows).drop_duplicates("state").head(50)

# ═══════════════════════════════════════════════════════════════════════════════
# 6. FACT WEEKLY SALES
# ═══════════════════════════════════════════════════════════════════════════════
def gen_weekly_sales(sku_df, brand_dim):
    rows = []
    sid = 1
    brand_acv = {b[0]: b[5] for b in BRANDS}
    for _, sku in sku_df.iterrows():
        bid = sku["brand_id"]
        b_info = brand_dict[bid]
        base_units_per_wk_per_ret = round(sku["list_price"] * 0.8 + 20)
        seasonal = SEASONALITY.get(bid, [1,1,1,1])
        yoy = YOY_TREND.get(bid, 1.0)

        for week_i, week_start in enumerate(FISCAL_WEEKS, 1):
            q = (week_i-1)//13
            seas_idx = seasonal[q]
            holiday_lift = 1.4 if week_i in HOLIDAYS else 1.0

            for ret in RETAILERS:
                rid = ret[0]
                ret_acv_factor = ret[4] / 21.0  # normalize to Walmart=1

                base = base_units_per_wk_per_ret * ret_acv_factor * seas_idx * holiday_lift
                units = max(0, int(np.random.normal(base, base * 0.18)))
                if units == 0:
                    continue

                # promotional discount
                is_on_promo = random.random() < 0.22
                discount_pct = round(random.uniform(0.10, 0.28), 3) if is_on_promo else 0.0
                realized_price = round(sku["list_price"] * (1 - discount_pct), 2)

                gross_sales = round(units * sku["list_price"], 2)
                net_sales   = round(units * realized_price, 2)
                cogs        = round(units * sku["std_cost"], 2)
                rows.append({
                    "sale_id":        sid,
                    "fiscal_week":    week_i,
                    "week_start_date":week_start.date().isoformat(),
                    "sku_id":         sku["sku_id"],
                    "brand_id":       bid,
                    "retailer_id":    rid,
                    "units_sold":     units,
                    "gross_sales":    gross_sales,
                    "net_sales":      net_sales,
                    "cogs":           cogs,
                    "gross_margin":   round(net_sales - cogs, 2),
                    "is_on_promo":    is_on_promo,
                    "discount_pct":   round(discount_pct*100, 1),
                    "realized_price": realized_price,
                    "yoy_index":      round(yoy, 3),
                    # Prior year proxy (net_sales / yoy_index)
                    "prior_yr_net_sales": round(net_sales / yoy, 2),
                })
                sid += 1
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 7. FACT DISTRIBUTION (ACV, TDP, Velocity)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_distribution(sku_df, sales_df):
    rows = []
    did = 1
    for _, sku in sku_df.iterrows():
        bid = sku["brand_id"]
        base_acv = brand_dict[bid][5]

        for week_i, week_start in enumerate(FISCAL_WEEKS, 1):
            for ret in RETAILERS:
                rid = ret[0]
                acv_factor = ret[4]

                # ACV varies by retailer strength and SKU tier
                tier_adj = {"Core": 0, "Value": -3, "Premium": -6}[sku["tier"]]
                inno_adj = -8 if sku["is_innovation"] else 0
                acv = round(min(99, max(20, base_acv * (acv_factor/100) + tier_adj + inno_adj + np.random.normal(0, 2))), 1)
                tdp = round(acv * random.uniform(0.85, 1.10), 1)

                # Velocity = $/TDP per week
                sku_sales = sales_df[
                    (sales_df["sku_id"] == sku["sku_id"]) &
                    (sales_df["fiscal_week"] == week_i) &
                    (sales_df["retailer_id"] == rid)
                ]["net_sales"].sum()
                velocity = round(sku_sales / max(tdp, 1), 2) if tdp > 0 else 0

                store_count = int(brand_dict[bid][5] / 100 * (ret[6] or 500))
                rows.append({
                    "dist_id":        did,
                    "fiscal_week":    week_i,
                    "week_start_date":week_start.date().isoformat(),
                    "sku_id":         sku["sku_id"],
                    "brand_id":       bid,
                    "retailer_id":    rid,
                    "acv_pct":        acv,
                    "tdp":            tdp,
                    "velocity_per_tdp": velocity,
                    "store_count_dist": store_count,
                    "numeric_dist_pct": round(min(99, acv + random.uniform(-5, 5)), 1),
                    "acv_gap_pct":    round(max(0, 95 - acv), 1),   # gap to 95% ACV target
                })
                did += 1
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 8. FACT MARKET SHARE (Brand vs Category vs Competitor)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_market_share():
    rows = []
    ms_id = 1

    bus = list({b[3] for b in BRANDS})
    for bu in bus:
        bu_brands = [b for b in BRANDS if b[3] == bu]
        competitors = CATEGORIES_COMP.get(bu, ["Competitor A","Competitor B","Private Label"])
        cat_size_base = random.uniform(50, 300)  # $M per week category size

        for week_i, week_start in enumerate(FISCAL_WEEKS, 1):
            for ret in RETAILERS:
                rid = ret[0]
                q = (week_i-1)//13
                cat_size = cat_size_base * (0.9 + 0.2 * random.random()) * (ret[4]/21.0)

                khc_share_total = 0
                for b in bu_brands:
                    share_base = b[4]   # category market share
                    noise = np.random.normal(0, 1.5)
                    share = round(max(5, min(75, share_base + noise)), 1)
                    khc_share_total += share

                    rows.append({
                        "ms_id":          ms_id, "fiscal_week": week_i,
                        "week_start_date":week_start.date().isoformat(),
                        "brand_id":       b[0], "brand_name": b[1],
                        "business_unit":  bu, "retailer_id": rid,
                        "entity_type":    "KHC Brand",
                        "dollar_share_pct": share,
                        "unit_share_pct": round(share * random.uniform(0.9, 1.1), 1),
                        "dollar_sales":   round(cat_size * share / 100, 2),
                        "category_size_dollars": round(cat_size, 2),
                        "yoy_share_chg":  round(np.random.normal(0, 0.8), 2),
                    })
                    ms_id += 1

                # Competitors
                rem_share = max(0, 100 - khc_share_total)
                per_comp = rem_share / max(len(competitors), 1)
                for comp in competitors:
                    c_share = round(max(0, per_comp + np.random.normal(0, 2)), 1)
                    rows.append({
                        "ms_id":          ms_id, "fiscal_week": week_i,
                        "week_start_date":week_start.date().isoformat(),
                        "brand_id":       None, "brand_name": comp,
                        "business_unit":  bu, "retailer_id": rid,
                        "entity_type":    "Competitor",
                        "dollar_share_pct": c_share,
                        "unit_share_pct": round(c_share * random.uniform(0.9, 1.1), 1),
                        "dollar_sales":   round(cat_size * c_share / 100, 2),
                        "category_size_dollars": round(cat_size, 2),
                        "yoy_share_chg":  round(np.random.normal(-0.2, 0.8), 2),
                    })
                    ms_id += 1
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 9. FACT PROMOTIONAL EVENTS (TPR, Feature, Display)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_promo_events(sku_df):
    rows = []
    pid = 1
    promo_types = ["TPR","Feature","Display","Feature + Display","TPR + Feature"]

    for _, sku in sku_df.iterrows():
        bid = sku["brand_id"]
        seasonal = SEASONALITY.get(bid, [1,1,1,1])

        for ret in RETAILERS:
            rid = ret[0]
            compliance_base = ret[7] if len(ret) > 7 else 65.0  # from gen_dim_retailer

            # Number of promo events this year per SKU per retailer
            n_events = random.randint(3, 14)
            used_weeks = set()

            for _ in range(n_events):
                # Pick a week biased toward high seasonality
                week_probs = np.array([SEASONALITY.get(bid,[1,1,1,1])[(w-1)//13] for w in range(1,53)])
                # Boost holiday weeks
                for hw in HOLIDAYS:
                    if hw <= 52:
                        week_probs[hw-1] *= 1.6
                week_probs /= week_probs.sum()
                week_i = int(np.random.choice(range(1,53), p=week_probs))
                if week_i in used_weeks:
                    continue
                used_weeks.add(week_i)

                ptype = random.choices(promo_types, weights=[0.30,0.20,0.15,0.20,0.15])[0]
                planned_disc = round(random.uniform(0.08, 0.32), 2)
                actual_disc  = round(planned_disc * random.uniform(0.85, 1.05), 2)

                # Lift based on promo type
                base_lift = {"TPR":1.25,"Feature":1.40,"Display":1.30,
                             "Feature + Display":1.65,"TPR + Feature":1.55}[ptype]
                actual_lift = round(base_lift * random.uniform(0.80, 1.20), 2)

                # Compliance
                planned_stores = int(ret[6] or 500)
                compliance_pct = round(min(99, max(20, np.random.normal(
                    ret[7] if len(ret) > 7 else 65, 8))), 1)
                compliant_stores = int(planned_stores * compliance_pct / 100)

                rows.append({
                    "promo_id":          pid,
                    "fiscal_week":       week_i,
                    "week_start_date":   FISCAL_WEEKS[week_i-1].date().isoformat(),
                    "sku_id":            sku["sku_id"],
                    "brand_id":          bid,
                    "retailer_id":       rid,
                    "promo_type":        ptype,
                    "planned_discount_pct": round(planned_disc*100,1),
                    "actual_discount_pct":  round(actual_disc*100,1),
                    "planned_stores":    planned_stores,
                    "compliant_stores":  compliant_stores,
                    "compliance_pct":    compliance_pct,
                    "volume_lift_factor": actual_lift,
                    "incremental_units": int(random.randint(50, 5000) * actual_lift * (ret[4]/21.0)),
                    "promo_spend_dollars": round(planned_stores * planned_disc * sku["list_price"] * random.randint(20,200), 2),
                    "is_holiday_promo":  week_i in HOLIDAYS,
                    "occasion":          HOLIDAYS.get(week_i, ""),
                })
                pid += 1
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 10. FACT SHELF COMPLIANCE (Planogram, SOS, Facings)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_shelf_compliance(sku_df):
    rows = []
    sc_id = 1
    bus = sku_df["business_unit"].unique()

    for bu in bus:
        bu_skus = sku_df[sku_df["business_unit"] == bu]
        for ret in RETAILERS:
            rid = ret[0]
            for month in range(1, 13):
                # Planogram compliance per retailer per BU per month
                planned_facings = random.randint(2, 8)
                actual_facings  = max(1, int(planned_facings * random.uniform(0.75, 1.10)))
                planned_sos = round(random.uniform(20, 45), 1)  # share of shelf %
                actual_sos  = round(planned_sos * random.uniform(0.80, 1.05), 1)
                comp_pct    = round(random.uniform(45, 92), 1)

                rows.append({
                    "sc_id":            sc_id,
                    "month":            month,
                    "retailer_id":      rid,
                    "business_unit":    bu,
                    "planned_facings":  planned_facings,
                    "actual_facings":   actual_facings,
                    "facing_compliance": round(actual_facings/planned_facings*100, 1),
                    "planned_sos_pct":  planned_sos,
                    "actual_sos_pct":   actual_sos,
                    "sos_gap_pct":      round(actual_sos - planned_sos, 1),
                    "planogram_compliance_pct": comp_pct,
                    "osa_pct":          round(random.uniform(88, 99), 1),   # on-shelf availability
                    "oos_incidents":    random.randint(0, 15),
                    "num_skus_in_reset": len(bu_skus),
                    "unauthorized_skus": random.randint(0, 3),
                })
                sc_id += 1
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 11. FACT CONSUMER PANEL (Household Penetration, Purchase Frequency)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_consumer_panel():
    rows = []
    cp_id = 1
    for b in BRANDS:
        bid, name, seg, bu, share, acv, seasonal = b
        base_hh_pen = round(share * 0.85, 1)  # rough proxy

        for month in range(1, 13):
            q = (month-1)//3
            seas = SEASONALITY.get(bid, [1,1,1,1])[q]
            hh_pen = round(min(75, base_hh_pen * seas * random.uniform(0.95, 1.05)), 1)
            rows.append({
                "panel_id":           cp_id,
                "month":              month,
                "brand_id":           bid,
                "brand_name":         name,
                "hh_penetration_pct": hh_pen,
                "purchase_freq_annual": round(random.uniform(2.5, 12.0) * seas, 1),
                "avg_spend_per_trip": round(random.uniform(3.5, 18.0), 2),
                "buyer_loyalty_pct":  round(random.uniform(35, 75), 1),
                "new_buyer_pct":      round(random.uniform(5, 20), 1),
                "lapsed_buyer_pct":   round(random.uniform(8, 25), 1),
                "repeat_rate_pct":    round(random.uniform(40, 70), 1),
                "trip_incidence_pct": round(hh_pen * 0.6, 1),
            })
            cp_id += 1
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# 12. FACT VOLUME DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════════════════
def gen_volume_decomp(sales_df):
    rows = []
    vd_id = 1
    for bid in [b[0] for b in BRANDS]:
        for week_i in range(1, 53):
            for rid in [r[0] for r in RETAILERS]:
                total_net = sales_df[
                    (sales_df["brand_id"] == bid) &
                    (sales_df["fiscal_week"] == week_i) &
                    (sales_df["retailer_id"] == rid)
                ]["net_sales"].sum()
                if total_net == 0:
                    continue

                yoy = YOY_TREND.get(bid, 1.0)
                py = round(total_net / yoy, 2)
                chg = round(total_net - py, 2)

                # Decompose change into drivers
                dist_chg  = round(chg * random.uniform(-0.3, 0.5), 2)
                vel_chg   = round(chg * random.uniform(-0.4, 0.6), 2)
                price_chg = round(chg * random.uniform(-0.3, 0.3), 2)
                promo_chg = round(chg - dist_chg - vel_chg - price_chg, 2)

                rows.append({
                    "vd_id":           vd_id,
                    "fiscal_week":     week_i,
                    "brand_id":        bid,
                    "retailer_id":     rid,
                    "current_net_sales": total_net,
                    "prior_yr_net_sales": py,
                    "total_change":    chg,
                    "pct_change":      round((chg / py * 100) if py > 0 else 0, 1),
                    "distribution_driver": dist_chg,
                    "velocity_driver":    vel_chg,
                    "price_mix_driver":   price_chg,
                    "promo_driver":       promo_chg,
                    "base_volume":        round(total_net * random.uniform(0.55, 0.75), 2),
                    "incremental_volume": round(total_net * random.uniform(0.25, 0.45), 2),
                    "price_elasticity":   round(random.uniform(-2.5, -1.0), 2),
                })
                vd_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n=== Kraft Heinz Retail Analytics Data Generator ===\n")

    print("Generating dimensions...")
    brand_dim = gen_dim_brand();           save(brand_dim,  "dim_brand")
    sku_dim   = gen_dim_sku();             save(sku_dim,    "dim_sku")
    ret_dim   = gen_dim_retailer();        save(ret_dim,    "dim_retailer")
    cal_dim   = gen_dim_calendar();        save(cal_dim,    "dim_calendar")
    mkt_dim   = gen_dim_market();          save(mkt_dim,    "dim_market")

    print("\nGenerating weekly sales (heavy)...")
    sales_df  = gen_weekly_sales(sku_dim, brand_dim); save(sales_df, "fact_weekly_sales")

    print("\nGenerating distribution / ACV / TDP / Velocity...")
    dist_df   = gen_distribution(sku_dim, sales_df);  save(dist_df,  "fact_distribution")

    print("\nGenerating market share...")
    share_df  = gen_market_share();        save(share_df,  "fact_market_share")

    print("\nGenerating promotional events...")
    promo_df  = gen_promo_events(sku_dim); save(promo_df,  "fact_promotional_events")

    print("\nGenerating shelf compliance...")
    shelf_df  = gen_shelf_compliance(sku_dim); save(shelf_df, "fact_shelf_compliance")

    print("\nGenerating consumer panel...")
    panel_df  = gen_consumer_panel();     save(panel_df,  "fact_consumer_panel")

    print("\nGenerating volume decomposition...")
    vd_df     = gen_volume_decomp(sales_df); save(vd_df,  "fact_volume_decomp")

    print(f"\n=== Done! All datasets written to {OUT} ===\n")
