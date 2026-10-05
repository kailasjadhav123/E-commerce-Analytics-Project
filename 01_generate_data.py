"""
E-Commerce Analytics Project — Data Generation Script
"""
import pandas as pd
import numpy as np
import random
import sqlite3
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

# ── Configuration ───────────
NUM_CUSTOMERS   = 300
NUM_PRODUCTS    = 80
NUM_ORDERS      = 800
START_DATE      = datetime(2022, 1, 1)
END_DATE        = datetime(2024, 12, 31)
DB_PATH         = os.path.join(os.path.dirname(__file__), "..", "data", "ecommerce.db")

# ── Helpers ────────────
def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]

# ── 1. Customers ───────────────
CITIES = [
    ("Mumbai","Maharashtra"),("Delhi","Delhi"),("Bengaluru","Karnataka"),
    ("Hyderabad","Telangana"),("Chennai","Tamil Nadu"),("Pune","Maharashtra"),
    ("Kolkata","West Bengal"),("Ahmedabad","Gujarat"),("Jaipur","Rajasthan"),
    ("Lucknow","Uttar Pradesh"),("Surat","Gujarat"),("Kochi","Kerala"),
    ("Nagpur","Maharashtra"),("Chandigarh","Punjab"),("Bhopal","Madhya Pradesh"),
]
SEGMENTS = ["Premium","Regular","Budget"]
SEG_W    = [0.2, 0.55, 0.25]

first_names = ["Aarav","Aditi","Amit","Anjali","Arjun","Deepa","Gaurav","Kavya",
               "Manish","Meera","Neha","Priya","Rahul","Raj","Rohan","Sanya",
               "Shruti","Sneha","Suresh","Vikram","Vikas","Zara","Aisha","Ravi"]
last_names  = ["Sharma","Verma","Patel","Singh","Gupta","Joshi","Kumar","Nair",
               "Reddy","Rao","Mehta","Shah","Jain","Agarwal","Mishra","Iyer"]

customers = []
for i in range(1, NUM_CUSTOMERS + 1):
    city, state = random.choice(CITIES)
    seg = weighted_choice(SEGMENTS, SEG_W)
    reg_date = random_date(START_DATE, END_DATE - timedelta(days=30))
    customers.append({
        "customer_id"      : i,
        "first_name"       : random.choice(first_names),
        "last_name"        : random.choice(last_names),
        "email"            : f"customer{i}@email.com",
        "phone"            : f"+91{random.randint(7000000000, 9999999999)}",
        "city"             : city,
        "state"            : state,
        "pincode"          : str(random.randint(100000, 999999)),
        "segment"          : seg,
        "registration_date": reg_date.strftime("%Y-%m-%d"),
        "is_active"        : random.choices([1, 0], weights=[0.85, 0.15])[0],
    })

df_customers = pd.DataFrame(customers)

# ── 2. Products ──────────────────────
CATEGORIES = {
    "Electronics"   : (["Smartphone","Laptop","Tablet","Earbuds","Smartwatch","Charger","Power Bank","Camera"],
                       (500, 80000)),
    "Clothing"      : (["T-Shirt","Jeans","Kurta","Saree","Jacket","Sneakers","Sandals","Dress"],
                       (200, 5000)),
    "Home & Kitchen": (["Mixer","Pressure Cooker","Water Bottle","Bedsheet","Pillow","Air Purifier","Lamp","Cookware Set"],
                       (150, 15000)),
    "Books"         : (["Fiction Novel","Self-Help","Textbook","Biography","Comic","Cookbook","History","Science"],
                       (99, 1500)),
    "Sports"        : (["Yoga Mat","Dumbbells","Cricket Bat","Football","Cycle","Protein Powder","Water Bottle","Resistance Band"],
                       (200, 8000)),
}
BRANDS = ["Samsung","Apple","Xiaomi","boAt","Lenovo","Nike","Adidas","Puma",
          "Prestige","Pigeon","Penguin","S.Chand","Amazon Basics","Decathlon","WOW"]

products = []
pid = 1
for cat, (items, price_range) in CATEGORIES.items():
    for item in items:
        base = round(random.uniform(*price_range), 2)
        cost = round(base * random.uniform(0.4, 0.65), 2)
        products.append({
            "product_id"  : pid,
            "product_name": item,
            "category"    : cat,
            "brand"       : random.choice(BRANDS),
            "unit_price"  : base,
            "cost_price"  : cost,
            "stock_qty"   : random.randint(0, 500),
            "is_active"   : random.choices([1, 0], weights=[0.92, 0.08])[0],
        })
        pid += 1

df_products = pd.DataFrame(products)

# ── 3. Orders ───────────────────
STATUS_OPTIONS = ["Delivered","Shipped","Cancelled","Returned","Processing"]
STATUS_W       = [0.60, 0.10, 0.12, 0.08, 0.10]
PAYMENT_MODES  = ["UPI","Credit Card","Debit Card","Net Banking","COD","Wallet"]
PAY_W          = [0.35, 0.22, 0.18, 0.08, 0.12, 0.05]
CHANNELS       = ["Mobile App","Website","Mobile Web"]
CHAN_W         = [0.50, 0.35, 0.15]

def order_date_weighted():
    """More orders in 2023-2024 to simulate business growth."""
    if random.random() < 0.30:
        return random_date(START_DATE, datetime(2022, 12, 31))
    elif random.random() < 0.55:
        return random_date(datetime(2023, 1, 1), datetime(2023, 12, 31))
    else:
        return random_date(datetime(2024, 1, 1), END_DATE)

orders = []
for i in range(1, NUM_ORDERS + 1):
    cust = random.choice(customers)
    reg  = datetime.strptime(cust["registration_date"], "%Y-%m-%d")
    # Order must be after registration
    order_date = random_date(reg + timedelta(days=1), END_DATE)
    status = weighted_choice(STATUS_OPTIONS, STATUS_W)
    discount = round(random.choices([0, 0.05, 0.10, 0.15, 0.20],
                                    weights=[0.40,0.25,0.20,0.10,0.05])[0], 2)
    orders.append({
        "order_id"       : i,
        "customer_id"    : cust["customer_id"],
        "order_date"     : order_date.strftime("%Y-%m-%d"),
        "status"         : status,
        "payment_mode"   : weighted_choice(PAYMENT_MODES, PAY_W),
        "channel"        : weighted_choice(CHANNELS, CHAN_W),
        "discount_pct"   : discount,
        "shipping_cost"  : round(random.choices([0, 49, 99], weights=[0.4,0.4,0.2])[0], 2),
        "city"           : cust["city"],
        "state"          : cust["state"],
    })

df_orders = pd.DataFrame(orders)

# ── 4. Order Items ──────────────────────────
order_items = []
item_id = 1
for _, order in df_orders.iterrows():
    n_items = random.choices([1, 2, 3, 4, 5], weights=[0.40,0.30,0.15,0.10,0.05])[0]
    chosen  = df_products.sample(n=n_items)
    for _, prod in chosen.iterrows():
        qty      = random.randint(1, 4)
        price    = prod["unit_price"]
        discount = order["discount_pct"]
        line_rev = round(qty * price * (1 - discount), 2)
        order_items.append({
            "item_id"       : item_id,
            "order_id"      : order["order_id"],
            "product_id"    : prod["product_id"],
            "quantity"      : qty,
            "unit_price"    : price,
            "discount_pct"  : discount,
            "line_revenue"  : line_rev,
        })
        item_id += 1

df_items = pd.DataFrame(order_items)

# ── 5. Returns ─────────────────────────
RETURN_REASONS = ["Defective product","Wrong item delivered","Changed mind",
                  "Better price elsewhere","Not as described","Damaged packaging"]
returned_orders = df_orders[df_orders["status"] == "Returned"]["order_id"].tolist()

returns = []
for rid, oid in enumerate(returned_orders, 1):
    order_date = datetime.strptime(
        df_orders[df_orders["order_id"] == oid]["order_date"].values[0], "%Y-%m-%d")
    return_date = order_date + timedelta(days=random.randint(1, 15))
    returns.append({
        "return_id"    : rid,
        "order_id"     : oid,
        "return_date"  : return_date.strftime("%Y-%m-%d"),
        "reason"       : random.choice(RETURN_REASONS),
        "refund_amount": round(random.uniform(200, 5000), 2),
        "status"       : random.choices(["Approved","Pending","Rejected"],
                                        weights=[0.75,0.15,0.10])[0],
    })

df_returns = pd.DataFrame(returns)

# ── 6. Update orders with totals ────────────────────────────────
order_totals = df_items.groupby("order_id")["line_revenue"].sum().reset_index()
order_totals.columns = ["order_id", "total_amount"]
df_orders = df_orders.merge(order_totals, on="order_id", how="left")
df_orders["total_amount"] = df_orders["total_amount"].fillna(0).round(2)

# ── 7. Save to SQLite ──────────────────────────────
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)

df_customers.to_sql("customers",   conn, if_exists="replace", index=False)
df_products.to_sql("products",     conn, if_exists="replace", index=False)
df_orders.to_sql("orders",         conn, if_exists="replace", index=False)
df_items.to_sql("order_items",     conn, if_exists="replace", index=False)
df_returns.to_sql("returns",       conn, if_exists="replace", index=False)

conn.close()

# ── 8. Export CSVs ─────────────────────────────
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
df_customers.to_csv(f"{data_dir}/customers.csv",   index=False)
df_products.to_csv(f"{data_dir}/products.csv",     index=False)
df_orders.to_csv(f"{data_dir}/orders.csv",         index=False)
df_items.to_csv(f"{data_dir}/order_items.csv",     index=False)
df_returns.to_csv(f"{data_dir}/returns.csv",       index=False)

print("✅ Data generation complete!")
print(f"   Customers  : {len(df_customers):,}")
print(f"   Products   : {len(df_products):,}")
print(f"   Orders     : {len(df_orders):,}")
print(f"   Order Items: {len(df_items):,}")
print(f"   Returns    : {len(df_returns):,}")
print(f"   Database   : {DB_PATH}")
