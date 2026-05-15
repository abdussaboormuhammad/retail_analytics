"""
Retail Analytics Data Generator
Generates 18 CSV datasets for a Walmart-style retail analytics project.
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
import os
import random
import uuid
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)
random.seed(42)

# ── Config ────────────────────────────────────────────────────────────────────
YEAR = 2024
NUM_ITEMS = 1000
NUM_CATEGORIES = 10
NUM_STORES = 50
NUM_FC = 10          # fulfillment centers
NUM_DC = 25          # distribution centers
START_DATE = date(YEAR, 1, 1)
END_DATE = date(YEAR, 12, 31)
DATA_DIR = "/Users/abdussaboor/Documents/github/retail_analytics/data"
os.makedirs(DATA_DIR, exist_ok=True)

def save(df, name):
    path = os.path.join(DATA_DIR, f"{name}.csv")
    df.to_csv(path, index=False)
    print(f"  ✓  {name}.csv  ({len(df):,} rows)")

def date_range():
    d = START_DATE
    while d <= END_DATE:
        yield d
        d += timedelta(days=1)

DATES = list(date_range())
STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
]
CATEGORIES = [
    "Grocery", "Electronics", "Apparel", "Home & Garden",
    "Sporting Goods", "Pharmacy", "Automotive", "Toys",
    "Health & Beauty", "Office Supplies"
]
REGIONS = ["North", "South", "East", "West", "Central"]
HOLIDAYS = {
    date(2024, 1, 1): "New Year's Day",
    date(2024, 1, 15): "MLK Day",
    date(2024, 2, 19): "Presidents Day",
    date(2024, 5, 27): "Memorial Day",
    date(2024, 7, 4): "Independence Day",
    date(2024, 9, 2): "Labor Day",
    date(2024, 11, 11): "Veterans Day",
    date(2024, 11, 28): "Thanksgiving",
    date(2024, 11, 29): "Black Friday",
    date(2024, 12, 25): "Christmas",
    date(2024, 12, 31): "New Year's Eve",
}
TENDER_TYPES = ["Credit Card", "Debit Card", "Cash", "EBT/SNAP", "Gift Card", "Mobile Pay", "Check"]
FULFILLMENT_TYPES = ["Ship to Home", "Store Pickup", "Curbside Pickup", "Same-Day Delivery"]
DEVICE_TYPES = ["Mobile", "Desktop", "Tablet"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge", "Samsung Browser"]
REFERRALS = ["Direct", "Google Search", "Email", "Social Media", "Affiliate", "Paid Search"]
EVENT_TYPES = ["page_view", "search", "product_view", "add_to_cart", "remove_from_cart",
               "begin_checkout", "purchase", "wishlist_add", "review_view"]

# ── Brands / vendors per category ─────────────────────────────────────────────
CAT_BRANDS = {
    "Grocery":          ["Great Value", "Sam's Choice", "Marketside", "Equate Food", "Store Brand"],
    "Electronics":      ["Samsung", "Apple", "LG", "Sony", "onn."],
    "Apparel":          ["George", "Time and Tru", "Athletic Works", "Free Assembly", "Wonder Nation"],
    "Home & Garden":    ["Better Homes & Gardens", "Mainstays", "Oster", "Hometrends", "Ozark Trail"],
    "Sporting Goods":   ["Spalding", "Ozark Trail", "Athletic Works", "Wilson", "Russell"],
    "Pharmacy":         ["Equate", "ReliOn", "Sunmark", "Kroger Health", "GoodSense"],
    "Automotive":       ["Super Tech", "EverStart", "Castrol", "Rain-X", "Armor All"],
    "Toys":             ["Fisher-Price", "Hasbro", "Lego", "Barbie", "Hot Wheels"],
    "Health & Beauty":  ["Equate", "No7", "L'Oreal", "Dove", "Pantene"],
    "Office Supplies":  ["Pen+Gear", "Staples", "Avery", "3M", "Sharpie"],
}
SUBCATEGORIES = {
    "Grocery":          ["Dairy", "Bakery", "Frozen", "Snacks", "Beverages"],
    "Electronics":      ["TVs", "Phones", "Computers", "Audio", "Cameras"],
    "Apparel":          ["Men's", "Women's", "Kids'", "Shoes", "Accessories"],
    "Home & Garden":    ["Furniture", "Decor", "Outdoor", "Kitchen", "Bedding"],
    "Sporting Goods":   ["Fitness", "Camping", "Team Sports", "Water Sports", "Cycling"],
    "Pharmacy":         ["OTC Meds", "Vitamins", "First Aid", "Diabetic", "Personal Care"],
    "Automotive":       ["Oil & Fluids", "Batteries", "Tires", "Accessories", "Tools"],
    "Toys":             ["Action Figures", "Board Games", "Outdoor", "Building Sets", "Dolls"],
    "Health & Beauty":  ["Hair Care", "Skin Care", "Cosmetics", "Oral Care", "Men's Grooming"],
    "Office Supplies":  ["Paper", "Writing", "Organization", "Ink & Toner", "Technology"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CALENDAR DIMENSION
# ═══════════════════════════════════════════════════════════════════════════════
def gen_calendar():
    rows = []
    for d in DATES:
        iso = d.isocalendar()
        rows.append({
            "date_key":         d.strftime("%Y%m%d"),
            "date":             d.isoformat(),
            "year":             d.year,
            "quarter":          (d.month - 1) // 3 + 1,
            "month":            d.month,
            "month_name":       d.strftime("%B"),
            "week_number":      iso[1],
            "day_of_week":      d.weekday() + 1,          # 1=Mon
            "day_name":         d.strftime("%A"),
            "is_weekend":       d.weekday() >= 5,
            "is_holiday":       d in HOLIDAYS,
            "holiday_name":     HOLIDAYS.get(d, ""),
            # Walmart fiscal year starts ~last Saturday of January
            "fiscal_week":      iso[1],
            "fiscal_month":     d.month,
            "fiscal_quarter":   (d.month - 1) // 3 + 1,
            "fiscal_year":      YEAR,
            "season":           (
                "Winter" if d.month in [12, 1, 2] else
                "Spring" if d.month in [3, 4, 5] else
                "Summer" if d.month in [6, 7, 8] else "Fall"
            ),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ITEM DIMENSION
# ═══════════════════════════════════════════════════════════════════════════════
def gen_items():
    rows = []
    items_per_cat = NUM_ITEMS // NUM_CATEGORIES
    item_id = 1
    for cat_id, cat in enumerate(CATEGORIES, 1):
        brands = CAT_BRANDS[cat]
        subcats = SUBCATEGORIES[cat]
        for i in range(items_per_cat):
            brand = random.choice(brands)
            subcat = random.choice(subcats)
            unit_cost = round(random.uniform(0.50, 200.00), 2)
            markup = random.uniform(1.20, 1.60)
            unit_retail = round(unit_cost * markup, 2)
            rows.append({
                "item_id":          item_id,
                "item_name":        f"{brand} {subcat} Item {item_id:04d}",
                "category_id":      cat_id,
                "category_name":    cat,
                "subcategory":      subcat,
                "brand":            brand,
                "vendor_id":        f"V{random.randint(1000, 5000):04d}",
                "upc":              f"{random.randint(10**11, 10**12-1)}",
                "unit_cost":        unit_cost,
                "unit_retail":      unit_retail,
                "unit_weight_lbs":  round(random.uniform(0.1, 50.0), 2),
                "unit_volume_cf":   round(random.uniform(0.01, 5.0), 3),
                "is_perishable":    cat in ["Grocery", "Pharmacy"],
                "is_private_label": brand in ["Great Value", "Sam's Choice", "Equate",
                                               "George", "onn.", "Pen+Gear", "Super Tech",
                                               "Marketside"],
                "is_seasonal":      random.random() < 0.15,
                "avg_shelf_days":   random.randint(7, 365),
                "min_shelf_qty":    random.randint(1, 6),
                "max_shelf_qty":    random.randint(12, 72),
                "reorder_point":    random.randint(3, 24),
                "lead_time_days":   random.randint(1, 21),
                "item_status":      random.choices(["Active", "Discontinued", "Seasonal"],
                                                    weights=[0.90, 0.05, 0.05])[0],
            })
            item_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. STORE DIMENSION
# ═══════════════════════════════════════════════════════════════════════════════
def gen_stores():
    store_types = ["Supercenter", "Neighborhood Market", "Discount Store", "Supercenter", "Supercenter"]
    rows = []
    for i, state in enumerate(STATES, 1):
        stype = random.choice(store_types)
        open_year = random.randint(1990, 2020)
        rows.append({
            "store_id":             i,
            "store_number":         f"S{i:04d}",
            "store_name":           f"Walmart {stype} #{i:04d}",
            "store_type":           stype,
            "city":                 f"City_{state}",
            "state":                state,
            "zip":                  f"{random.randint(10000,99999)}",
            "region":               random.choice(REGIONS),
            "district":             f"D{random.randint(1,20):02d}",
            "square_footage":       random.randint(40000, 200000),
            "num_departments":      random.randint(20, 45),
            "open_date":            date(open_year, random.randint(1,12), random.randint(1,28)).isoformat(),
            "store_manager":        f"Manager_{i}",
            "has_pharmacy":         random.random() < 0.80,
            "has_auto_center":      random.random() < 0.60,
            "has_vision_center":    random.random() < 0.70,
            "has_garden_center":    random.random() < 0.65,
            "has_tire_center":      random.random() < 0.55,
            "has_grocery_pickup":   random.random() < 0.90,
            "has_fuel_station":     random.random() < 0.50,
            "avg_weekly_customers": random.randint(5000, 30000),
            "parking_spaces":       random.randint(300, 800),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DISTRIBUTION / FULFILLMENT CENTER DIMENSION
# ═══════════════════════════════════════════════════════════════════════════════
def gen_dc_dim():
    rows = []
    # Distribution Centers (DC)
    dc_states = random.choices(STATES, k=NUM_DC)
    for i in range(1, NUM_DC + 1):
        rows.append({
            "center_id":        f"DC{i:03d}",
            "center_name":      f"Distribution Center {i}",
            "center_type":      "Distribution Center",
            "city":             f"DC_City_{i}",
            "state":            dc_states[i-1],
            "zip":              f"{random.randint(10000,99999)}",
            "region":           random.choice(REGIONS),
            "square_footage":   random.randint(500000, 2000000),
            "num_dock_doors":   random.randint(50, 200),
            "capacity_pallets": random.randint(10000, 50000),
            "has_cold_storage": random.random() < 0.60,
            "has_frozen":       random.random() < 0.40,
            "has_dry_storage":  True,
            "open_date":        date(random.randint(1990,2015),
                                     random.randint(1,12), random.randint(1,28)).isoformat(),
            "num_employees":    random.randint(500, 3000),
        })
    # Fulfillment Centers (FC)
    fc_states = random.choices(STATES, k=NUM_FC)
    for i in range(1, NUM_FC + 1):
        rows.append({
            "center_id":        f"FC{i:03d}",
            "center_name":      f"Fulfillment Center {i}",
            "center_type":      "Fulfillment Center",
            "city":             f"FC_City_{i}",
            "state":            fc_states[i-1],
            "zip":              f"{random.randint(10000,99999)}",
            "region":           random.choice(REGIONS),
            "square_footage":   random.randint(200000, 1000000),
            "num_dock_doors":   random.randint(20, 100),
            "capacity_pallets": random.randint(5000, 25000),
            "has_cold_storage": random.random() < 0.30,
            "has_frozen":       False,
            "has_dry_storage":  True,
            "open_date":        date(random.randint(2010,2022),
                                     random.randint(1,12), random.randint(1,28)).isoformat(),
            "num_employees":    random.randint(200, 1500),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ITEM PRICING
# ═══════════════════════════════════════════════════════════════════════════════
def gen_item_pricing(items_df):
    rows = []
    price_id = 1
    for _, item in items_df.iterrows():
        # Base national price record
        eff = START_DATE
        while eff <= END_DATE:
            duration = random.randint(14, 90)
            end = min(eff + timedelta(days=duration), END_DATE)
            price_type = random.choices(
                ["Regular", "Rollback", "Clearance", "EDLP"],
                weights=[0.60, 0.25, 0.08, 0.07]
            )[0]
            sale_disc = random.uniform(0.05, 0.30) if price_type != "Regular" else 0
            rows.append({
                "pricing_id":        price_id,
                "item_id":           item["item_id"],
                "store_id":          None,            # national
                "effective_date":    eff.isoformat(),
                "end_date":          end.isoformat(),
                "regular_price":     item["unit_retail"],
                "sale_price":        round(item["unit_retail"] * (1 - sale_disc), 2),
                "clearance_price":   round(item["unit_retail"] * 0.50, 2) if price_type == "Clearance" else None,
                "price_type":        price_type,
                "competitor_price":  round(item["unit_retail"] * random.uniform(0.90, 1.15), 2),
                "price_index":       round(random.uniform(0.88, 1.12), 3),
            })
            price_id += 1
            eff = end + timedelta(days=1)
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. STORE SALES
# ═══════════════════════════════════════════════════════════════════════════════
def gen_store_sales(items_df, stores_df):
    rows = []
    sale_id = 1
    item_ids = items_df["item_id"].tolist()
    item_costs = dict(zip(items_df["item_id"], items_df["unit_cost"]))
    item_retail = dict(zip(items_df["item_id"], items_df["unit_retail"]))
    # Each store sells ~200 items per week (weekly granularity)
    weeks = pd.date_range(start=str(START_DATE), end=str(END_DATE), freq="W-SUN")
    for store_id in stores_df["store_id"]:
        store_items = random.sample(item_ids, 250)
        for week_start in weeks:
            wd = week_start.date()
            for item_id in store_items:
                retail = item_retail[item_id]
                cost = item_costs[item_id]
                # Seasonal / holiday lift
                holiday_lift = 2.5 if wd in HOLIDAYS else 1.0
                units = max(0, int(np.random.poisson(3) * holiday_lift))
                if units == 0:
                    continue
                returns = max(0, int(units * random.uniform(0, 0.05)))
                net_units = units - returns
                gross_sales = round(retail * units, 2)
                net_sales = round(retail * net_units, 2)
                cogs = round(cost * net_units, 2)
                rows.append({
                    "sale_id":           sale_id,
                    "week_start_date":   wd.isoformat(),
                    "store_id":          store_id,
                    "item_id":           item_id,
                    "units_sold":        units,
                    "units_returned":    returns,
                    "net_units":         net_units,
                    "gross_sales":       gross_sales,
                    "net_sales":         net_sales,
                    "cogs":              cogs,
                    "gross_margin":      round(net_sales - cogs, 2),
                    "gross_margin_pct":  round((net_sales - cogs) / net_sales * 100, 2) if net_sales > 0 else 0,
                    "num_transactions":  random.randint(1, units),
                    "avg_basket_size":   round(gross_sales / max(random.randint(1, units), 1), 2),
                })
                sale_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ECOMM SALES
# ═══════════════════════════════════════════════════════════════════════════════
def gen_ecomm_sales(items_df):
    rows = []
    sale_id = 1
    fc_ids = [f"FC{i:03d}" for i in range(1, NUM_FC + 1)]
    item_ids = items_df["item_id"].tolist()
    item_retail = dict(zip(items_df["item_id"], items_df["unit_retail"]))
    item_cost = dict(zip(items_df["item_id"], items_df["unit_cost"]))
    weeks = pd.date_range(start=str(START_DATE), end=str(END_DATE), freq="W-SUN")
    for week_start in weeks:
        wd = week_start.date()
        sampled_items = random.sample(item_ids, 300)
        for item_id in sampled_items:
            retail = item_retail[item_id]
            cost = item_cost[item_id]
            ftype = random.choice(FULFILLMENT_TYPES)
            fc_id = random.choice(fc_ids) if "Ship" in ftype else None
            holiday_lift = 3.0 if wd in HOLIDAYS else 1.0
            units = max(1, int(np.random.poisson(5) * holiday_lift))
            returns = max(0, int(units * random.uniform(0, 0.12)))
            net_units = units - returns
            gross_sales = round(retail * units, 2)
            net_sales = round(retail * net_units, 2)
            cogs = round(cost * net_units, 2)
            shipping = round(random.uniform(0, 8.99) if "Ship" in ftype else 0, 2)
            rows.append({
                "ecomm_sale_id":      sale_id,
                "week_start_date":    wd.isoformat(),
                "item_id":            item_id,
                "fulfillment_center_id": fc_id,
                "channel":            random.choices(["Website", "App"], weights=[0.55, 0.45])[0],
                "fulfillment_type":   ftype,
                "units_sold":         units,
                "units_returned":     returns,
                "net_units":          net_units,
                "gross_sales":        gross_sales,
                "net_sales":          net_sales,
                "cogs":               cogs,
                "gross_margin":       round(net_sales - cogs, 2),
                "shipping_revenue":   shipping * units,
                "shipping_cost":      round(shipping * units * 1.5, 2),
                "num_orders":         random.randint(1, max(1, units // 2)),
                "avg_order_value":    round(gross_sales / max(random.randint(1, units), 1), 2),
            })
            sale_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. STORE INVENTORY  (weekly snapshots)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_store_inventory(items_df, stores_df):
    rows = []
    snap_id = 1
    item_ids = items_df["item_id"].tolist()
    item_retail = dict(zip(items_df["item_id"], items_df["unit_retail"]))
    weeks = pd.date_range(start=str(START_DATE), end=str(END_DATE), freq="W-SUN")
    for week_start in weeks:
        wd = week_start.date()
        for store_id in stores_df["store_id"]:
            sampled = random.sample(item_ids, 250)
            for item_id in sampled:
                on_hand = random.randint(0, 100)
                on_order = random.randint(0, 50)
                in_transit = random.randint(0, 30)
                shrink = random.randint(0, 3)
                retail = item_retail[item_id]
                rows.append({
                    "snapshot_id":       snap_id,
                    "snapshot_date":     wd.isoformat(),
                    "store_id":          store_id,
                    "item_id":           item_id,
                    "on_hand_units":     on_hand,
                    "on_order_units":    on_order,
                    "in_transit_units":  in_transit,
                    "available_units":   max(0, on_hand - shrink),
                    "shrink_units":      shrink,
                    "shrink_value":      round(shrink * retail, 2),
                    "days_of_supply":    round(on_hand / max(random.randint(1, 10), 1), 1),
                    "reorder_needed":    on_hand < random.randint(5, 15),
                    "last_receipt_date": (wd - timedelta(days=random.randint(1, 14))).isoformat(),
                })
                snap_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. ECOMM INVENTORY  (weekly snapshots by FC)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_ecomm_inventory(items_df):
    rows = []
    snap_id = 1
    fc_ids = [f"FC{i:03d}" for i in range(1, NUM_FC + 1)]
    weeks = pd.date_range(start=str(START_DATE), end=str(END_DATE), freq="W-SUN")
    item_ids = items_df["item_id"].tolist()
    for week_start in weeks:
        wd = week_start.date()
        for fc_id in fc_ids:
            sampled = random.sample(item_ids, 400)
            for item_id in sampled:
                on_hand = random.randint(0, 500)
                reserved = random.randint(0, min(on_hand, 100))
                in_transit = random.randint(0, 200)
                rows.append({
                    "snapshot_id":         snap_id,
                    "snapshot_date":       wd.isoformat(),
                    "fulfillment_center_id": fc_id,
                    "item_id":             item_id,
                    "on_hand_units":       on_hand,
                    "reserved_units":      reserved,
                    "available_units":     max(0, on_hand - reserved),
                    "in_transit_units":    in_transit,
                    "days_of_supply":      round(on_hand / max(random.randint(5, 50), 1), 1),
                    "reorder_needed":      on_hand < 50,
                    "last_receipt_date":   (wd - timedelta(days=random.randint(1, 7))).isoformat(),
                })
                snap_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. ONLINE PICKUP AND DELIVERY
# ═══════════════════════════════════════════════════════════════════════════════
def gen_online_pickup_delivery(items_df, stores_df):
    rows = []
    item_retail = dict(zip(items_df["item_id"], items_df["unit_retail"]))
    item_ids = items_df["item_id"].tolist()
    fc_ids = [f"FC{i:03d}" for i in range(1, NUM_FC + 1)]
    store_ids = stores_df["store_id"].tolist()
    for i in range(150_000):
        order_date = random.choice(DATES)
        ftype = random.choice(FULFILLMENT_TYPES)
        sla_hours = {"Ship to Home": 72, "Store Pickup": 4,
                     "Curbside Pickup": 2, "Same-Day Delivery": 8}[ftype]
        actual_hours = sla_hours * random.uniform(0.5, 1.6)
        sla_met = actual_hours <= sla_hours
        item_id = random.choice(item_ids)
        units = random.randint(1, 5)
        store_id = random.choice(store_ids) if "Pickup" in ftype or "Delivery" in ftype else None
        fc_id = random.choice(fc_ids) if "Ship" in ftype else None
        rows.append({
            "order_id":               f"ORD{i+1:08d}",
            "order_date":             order_date.isoformat(),
            "fulfillment_date":       (order_date + timedelta(hours=actual_hours)).isoformat()[:10],
            "store_id":               store_id,
            "fulfillment_center_id":  fc_id,
            "item_id":                item_id,
            "fulfillment_type":       ftype,
            "units":                  units,
            "order_total":            round(item_retail[item_id] * units, 2),
            "status":                 random.choices(
                                          ["Delivered", "Picked Up", "Cancelled", "In Transit"],
                                          weights=[0.70, 0.15, 0.08, 0.07])[0],
            "sla_hours":              sla_hours,
            "actual_hours":           round(actual_hours, 2),
            "sla_met":                sla_met,
            "customer_rating":        random.choices([1,2,3,4,5],
                                          weights=[0.03,0.05,0.10,0.30,0.52])[0],
            "distance_miles":         round(random.uniform(0.5, 30.0), 1) if "Delivery" in ftype else None,
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. MODULAR PLAN (Planogram)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_modular_plan(items_df, stores_df):
    rows = []
    plan_id = 1
    store_ids = stores_df["store_id"].tolist()
    for store_id in store_ids:
        items_sample = items_df.sample(frac=0.30, random_state=store_id)
        for _, item in items_sample.iterrows():
            eff = date(YEAR, random.choice([1, 4, 7, 10]), 1)
            rows.append({
                "plan_id":           plan_id,
                "store_id":          store_id,
                "item_id":           item["item_id"],
                "category_id":       item["category_id"],
                "department":        item["category_name"],
                "effective_date":    eff.isoformat(),
                "end_date":          date(YEAR, 12, 31).isoformat(),
                "aisle":             f"A{random.randint(1,30):02d}",
                "shelf_number":      random.randint(1, 6),
                "shelf_position":    random.randint(1, 20),
                "facing_count":      random.randint(1, 4),
                "shelf_capacity":    random.randint(6, 48),
                "min_display_qty":   random.randint(2, 12),
                "is_key_item":       random.random() < 0.20,
                "is_seasonal_slot":  random.random() < 0.10,
                "planogram_version": f"v{random.randint(1,5)}",
            })
            plan_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 12. ORDER FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
def gen_order_forecast(items_df, stores_df):
    rows = []
    fcast_id = 1
    store_ids = stores_df["store_id"].tolist()
    item_ids = items_df["item_id"].tolist()
    weeks = pd.date_range(start=str(START_DATE), end=str(END_DATE), freq="W-SUN")
    dc_ids = [f"DC{i:03d}" for i in range(1, NUM_DC + 1)]
    for week_start in weeks:
        wd = week_start.date()
        sampled_stores = random.sample(store_ids, 20)
        sampled_items = random.sample(item_ids, 50)
        for store_id in sampled_stores:
            for item_id in sampled_items:
                forecast_units = max(0, int(np.random.poisson(20)))
                error_pct = random.uniform(-0.20, 0.20)
                actual = max(0, int(forecast_units * (1 + error_pct)))
                rows.append({
                    "forecast_id":       fcast_id,
                    "forecast_date":     wd.isoformat(),
                    "store_id":          store_id,
                    "item_id":           item_id,
                    "dc_id":             random.choice(dc_ids),
                    "forecast_week":     wd.isocalendar()[1],
                    "forecast_units":    forecast_units,
                    "forecast_cases":    max(1, forecast_units // 12),
                    "ci_low":            max(0, int(forecast_units * 0.80)),
                    "ci_high":           int(forecast_units * 1.20),
                    "actual_units":      actual,
                    "forecast_bias":     actual - forecast_units,
                    "mape":              round(abs(actual - forecast_units) / max(actual, 1) * 100, 2),
                    "model_version":     f"v{random.randint(1,3)}.{random.randint(0,9)}",
                })
                fcast_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 13. PURCHASE ORDER
# ═══════════════════════════════════════════════════════════════════════════════
def gen_purchase_orders(items_df):
    rows = []
    dc_ids = [f"DC{i:03d}" for i in range(1, NUM_DC + 1)]
    vendors = items_df["vendor_id"].unique().tolist()
    item_cost = dict(zip(items_df["item_id"], items_df["unit_cost"]))
    item_vendor = dict(zip(items_df["item_id"], items_df["vendor_id"]))
    item_ids = items_df["item_id"].tolist()
    for po_num in range(1, 15_001):
        order_date = random.choice(DATES)
        lead_days = random.randint(3, 21)
        exp_delivery = order_date + timedelta(days=lead_days)
        item_id = random.choice(item_ids)
        units = random.randint(12, 1440)
        cost = item_cost[item_id]
        rows.append({
            "po_id":                po_num,
            "po_number":            f"PO{po_num:08d}",
            "vendor_id":            item_vendor[item_id],
            "dc_id":                random.choice(dc_ids),
            "item_id":              item_id,
            "order_date":           order_date.isoformat(),
            "expected_delivery_date": exp_delivery.isoformat(),
            "po_status":            random.choices(
                                        ["Open","Confirmed","Shipped","Received","Cancelled"],
                                        weights=[0.10,0.15,0.20,0.50,0.05])[0],
            "po_type":              random.choices(
                                        ["Regular","Rush","Direct Import","Cross-Dock"],
                                        weights=[0.65,0.10,0.15,0.10])[0],
            "ordered_units":        units,
            "ordered_cases":        max(1, units // 12),
            "unit_cost":            cost,
            "total_cost":           round(cost * units, 2),
            "payment_terms":        random.choice(["Net 30", "Net 45", "Net 60", "2/10 Net 30"]),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 14. ON TIME IN FULL (OTIF)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_otif(po_df):
    rows = []
    for _, po in po_df.iterrows():
        if po["po_status"] not in ["Received", "Shipped"]:
            continue
        exp = date.fromisoformat(po["expected_delivery_date"])
        late_days = random.choices([0, 0, 0, 1, 2, 3, 5, 7], weights=[5,3,2,2,2,1,1,1])[0]
        actual = exp + timedelta(days=late_days - random.randint(0, 1))
        on_time = actual <= exp
        ordered = po["ordered_units"]
        short_pct = random.choices([0, 0, 0, random.uniform(0.01, 0.20)], weights=[6,2,1,1])[0]
        received = max(0, int(ordered * (1 - short_pct)))
        in_full = received >= ordered * 0.98
        rows.append({
            "otif_id":               len(rows) + 1,
            "po_number":             po["po_number"],
            "vendor_id":             po["vendor_id"],
            "dc_id":                 po["dc_id"],
            "order_date":            po["order_date"],
            "expected_delivery_date": po["expected_delivery_date"],
            "actual_delivery_date":  actual.isoformat(),
            "expected_units":        ordered,
            "received_units":        received,
            "on_time_flag":          on_time,
            "in_full_flag":          in_full,
            "otif_flag":             on_time and in_full,
            "days_early_late":       (exp - actual).days,
            "short_units":           max(0, ordered - received),
            "fill_rate_pct":         round(received / ordered * 100, 2) if ordered > 0 else 0,
            "otif_score":            round((int(on_time) + int(in_full)) / 2 * 100, 1),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 15. STORE DEMAND FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
def gen_store_demand_forecast(items_df, stores_df):
    rows = []
    fcast_id = 1
    store_ids = stores_df["store_id"].tolist()
    item_ids = items_df["item_id"].tolist()
    weeks = pd.date_range(start=str(START_DATE), end=str(END_DATE), freq="W-SUN")
    for week_start in weeks:
        wd = week_start.date()
        sampled_stores = random.sample(store_ids, 15)
        sampled_items = random.sample(item_ids, 40)
        for store_id in sampled_stores:
            for item_id in sampled_items:
                f_units = max(0, int(np.random.poisson(15)))
                err = random.uniform(-0.25, 0.25)
                actual = max(0, int(f_units * (1 + err)))
                rows.append({
                    "forecast_id":        fcast_id,
                    "forecast_date":      wd.isoformat(),
                    "store_id":           store_id,
                    "item_id":            item_id,
                    "forecast_week":      wd.isocalendar()[1],
                    "forecast_units":     f_units,
                    "actual_units":       actual,
                    "forecast_bias":      actual - f_units,
                    "mape":               round(abs(actual - f_units) / max(actual, 1) * 100, 2),
                    "forecast_accuracy_pct": round(max(0, 100 - abs(actual - f_units) / max(actual, 1) * 100), 2),
                    "safety_stock_units": max(0, int(f_units * 0.15)),
                    "reorder_qty":        max(0, int(f_units * 1.10)),
                })
                fcast_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 16. STORE MARKUP AND MARKDOWNS
# ═══════════════════════════════════════════════════════════════════════════════
def gen_markdowns(items_df, stores_df):
    rows = []
    event_id = 1
    store_ids = stores_df["store_id"].tolist()
    item_retail = dict(zip(items_df["item_id"], items_df["unit_retail"]))
    item_ids = items_df["item_id"].tolist()
    for _ in range(80_000):
        store_id = random.choice(store_ids)
        item_id = random.choice(item_ids)
        event_date = random.choice(DATES)
        duration = random.randint(3, 30)
        end_date = min(event_date + timedelta(days=duration), END_DATE)
        etype = random.choices(["Markdown", "Markup", "Rollback", "Clearance"],
                                weights=[0.50, 0.10, 0.30, 0.10])[0]
        orig_price = item_retail[item_id]
        if etype == "Markup":
            chg_pct = random.uniform(0.02, 0.10)
        elif etype == "Clearance":
            chg_pct = -random.uniform(0.30, 0.70)
        else:
            chg_pct = -random.uniform(0.05, 0.40)
        new_price = round(orig_price * (1 + chg_pct), 2)
        units_during = random.randint(0, 200)
        rows.append({
            "event_id":           event_id,
            "store_id":           store_id,
            "item_id":            item_id,
            "event_date":         event_date.isoformat(),
            "end_date":           end_date.isoformat(),
            "event_type":         etype,
            "reason_code":        random.choice(["Seasonal End", "Overstock", "Competition",
                                                  "Promotion", "Holiday", "Damage", "Expiry"]),
            "original_price":     orig_price,
            "new_price":          new_price,
            "change_pct":         round(chg_pct * 100, 2),
            "markdown_depth":     round(abs(chg_pct) * 100, 2) if chg_pct < 0 else 0,
            "units_sold_during_event": units_during,
            "revenue_during_event":    round(new_price * units_during, 2),
            "margin_impact":      round((new_price - item_retail[item_id]) * units_during, 2),
        })
        event_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 17. TENDER ANALYSIS  (daily by store)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_tender_analysis(stores_df):
    rows = []
    tender_id = 1
    store_ids = stores_df["store_id"].tolist()
    tender_weights = {
        "Credit Card": 0.38, "Debit Card": 0.28, "Cash": 0.16,
        "EBT/SNAP": 0.08, "Gift Card": 0.04, "Mobile Pay": 0.04, "Check": 0.02,
    }
    for d in DATES:
        for store_id in store_ids:
            total_rev = random.uniform(20_000, 250_000)
            for tender, weight in tender_weights.items():
                noise = random.uniform(0.85, 1.15)
                amt = round(total_rev * weight * noise, 2)
                txn_count = random.randint(50, 2000)
                rows.append({
                    "tender_id":         tender_id,
                    "date":              d.isoformat(),
                    "store_id":          store_id,
                    "tender_type":       tender,
                    "transaction_count": txn_count,
                    "total_amount":      amt,
                    "avg_transaction":   round(amt / txn_count, 2),
                    "pct_of_store_total": round(weight * noise * 100, 2),
                    "chargebacks":       random.randint(0, 5) if tender == "Credit Card" else 0,
                    "declined_count":    random.randint(0, 20),
                })
                tender_id += 1
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 18. CLICKSTREAM DATA
# ═══════════════════════════════════════════════════════════════════════════════
def gen_clickstream(items_df):
    rows = []
    item_ids = items_df["item_id"].tolist()
    item_names = dict(zip(items_df["item_id"], items_df["item_name"]))
    for i in range(500_000):
        d = random.choice(DATES)
        hour = random.randint(6, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        ts = datetime(d.year, d.month, d.day, hour, minute, second)
        item_id = random.choice(item_ids) if random.random() < 0.70 else None
        event_type = random.choices(EVENT_TYPES,
                                     weights=[0.30,0.15,0.25,0.12,0.03,0.05,0.04,0.03,0.03])[0]
        rows.append({
            "event_id":       f"EV{i+1:09d}",
            "session_id":     f"SES{random.randint(1, 200_000):08d}",
            "user_id":        f"USR{random.randint(1, 500_000):08d}" if random.random() < 0.65 else "guest",
            "event_timestamp": ts.isoformat(),
            "event_date":     d.isoformat(),
            "event_type":     event_type,
            "item_id":        item_id,
            "item_name":      item_names.get(item_id, "") if item_id else "",
            "search_term":    f"search_term_{random.randint(1,500)}" if event_type == "search" else "",
            "page_category":  random.choice(CATEGORIES) if random.random() < 0.60 else "",
            "device_type":    random.choices(DEVICE_TYPES, weights=[0.55, 0.35, 0.10])[0],
            "browser":        random.choice(BROWSERS),
            "referral_source": random.choices(REFERRALS, weights=[0.25,0.30,0.15,0.15,0.08,0.07])[0],
            "session_page_num": random.randint(1, 20),
            "time_on_page_sec": random.randint(1, 600),
            "add_to_cart_flag": event_type == "add_to_cart",
            "purchase_flag":   event_type == "purchase",
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n=== Retail Analytics Data Generator ===\n")

    print("Generating dimension tables...")
    calendar_df = gen_calendar();        save(calendar_df,  "dim_calendar")
    items_df    = gen_items();           save(items_df,     "dim_item")
    stores_df   = gen_stores();          save(stores_df,    "dim_store")
    dc_df       = gen_dc_dim();          save(dc_df,        "dim_distribution_fulfillment_center")

    print("\nGenerating pricing...")
    pricing_df  = gen_item_pricing(items_df);  save(pricing_df, "fact_item_pricing")

    print("\nGenerating sales facts...")
    store_sales_df   = gen_store_sales(items_df, stores_df);   save(store_sales_df,  "fact_store_sales")
    ecomm_sales_df   = gen_ecomm_sales(items_df);              save(ecomm_sales_df,  "fact_ecomm_sales")

    print("\nGenerating inventory snapshots...")
    store_inv_df   = gen_store_inventory(items_df, stores_df); save(store_inv_df,   "fact_store_inventory")
    ecomm_inv_df   = gen_ecomm_inventory(items_df);            save(ecomm_inv_df,   "fact_ecomm_inventory")

    print("\nGenerating fulfillment orders...")
    opd_df = gen_online_pickup_delivery(items_df, stores_df);  save(opd_df, "fact_online_pickup_delivery")

    print("\nGenerating planning & forecasting...")
    mod_df    = gen_modular_plan(items_df, stores_df);          save(mod_df,     "fact_modular_plan")
    ord_fcast = gen_order_forecast(items_df, stores_df);        save(ord_fcast,  "fact_order_forecast")
    po_df     = gen_purchase_orders(items_df);                  save(po_df,      "fact_purchase_order")
    otif_df   = gen_otif(po_df);                                save(otif_df,    "fact_otif")
    dem_fcast = gen_store_demand_forecast(items_df, stores_df); save(dem_fcast,  "fact_store_demand_forecast")

    print("\nGenerating pricing events...")
    md_df = gen_markdowns(items_df, stores_df);  save(md_df, "fact_store_markup_markdown")

    print("\nGenerating tender analysis...")
    tender_df = gen_tender_analysis(stores_df);  save(tender_df, "fact_tender_analysis")

    print("\nGenerating clickstream...")
    click_df = gen_clickstream(items_df);        save(click_df, "fact_clickstream")

    print("\n=== Done! All 18 datasets written to", DATA_DIR, "===\n")
