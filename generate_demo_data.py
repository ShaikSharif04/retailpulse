from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(20261107)
base = Path(__file__).resolve().parent
products = [
    ("P001", "Wireless Earbuds", "Electronics", 1800, 1080),
    ("P002", "Bluetooth Speaker", "Electronics", 2400, 1500),
    ("P003", "Cotton T-Shirt", "Apparel", 700, 380),
    ("P004", "Denim Jeans", "Apparel", 1600, 900),
    ("P005", "Mixer Grinder", "Home Appliances", 3200, 2150),
    ("P006", "Storage Container Set", "Home & Kitchen", 950, 510),
    ("P007", "Running Shoes", "Footwear", 2200, 1350),
    ("P008", "Water Bottle", "Home & Kitchen", 450, 190),
    ("P009", "Smart Watch", "Electronics", 3500, 2350),
    ("P010", "Casual Sandals", "Footwear", 850, 480),
]
regions = {
    "South": ["Hyderabad Central", "Hyderabad North", "Vijayawada"],
    "West": ["Mumbai Central", "Pune Camp"],
    "North": ["Delhi South", "Jaipur"],
    "East": ["Kolkata Central"],
}
months_orders = [120, 125, 130, 135, 140, 145, 150, 155, 160, 190, 230, 300]
rows = []
order_counter = 100000
customer_ids = [f"C{i:04d}" for i in range(1, 701)]
for month_idx, n_orders in enumerate(months_orders):
    month = pd.Timestamp(2025, month_idx + 1, 1)
    days = month.days_in_month
    # The example company receives more orders over time, but its unit economics worsen.
    discount_mean = np.linspace(0.04, 0.22, 12)[month_idx]
    cost_inflation = np.linspace(1.00, 1.22, 12)[month_idx]
    # A store gradually loses share while other stores continue to grow.
    region_probs = np.array([0.40, 0.25, 0.20, 0.15])
    if month_idx >= 8:
        region_probs = np.array([0.33, 0.22, 0.28, 0.17])
    region_names = list(regions.keys())
    for _ in range(n_orders):
        order_counter += 1
        region = rng.choice(region_names, p=region_probs)
        store = rng.choice(regions[region])
        # Choose mix; lower-margin products become more common in later months.
        product_weights = np.array([0.15,0.12,0.12,0.10,0.10,0.12,0.10,0.10,0.06,0.03])
        if month_idx >= 8:
            product_weights = np.array([0.08,0.08,0.16,0.14,0.08,0.15,0.08,0.15,0.04,0.04])
        product_idx = int(rng.choice(len(products), p=product_weights/product_weights.sum()))
        pid, product, category, price, cost = products[product_idx]
        qty = int(rng.choice([1, 1, 1, 2, 2, 3], p=[.32,.20,.15,.18,.10,.05]))
        unit_price = float(price * rng.uniform(0.94, 1.06))
        unit_cost = float(cost * cost_inflation * rng.uniform(0.98, 1.04))
        # A portion of transactions face unusually high discounts, creating loss-making lines.
        discount_pct = float(np.clip(rng.normal(discount_mean, 0.035), 0, 0.38))
        if month_idx >= 9 and rng.random() < 0.12:
            discount_pct = float(rng.uniform(0.28, 0.42))
        refund_amount = 0.0
        if rng.random() < (0.025 + month_idx * 0.004):
            refund_amount = float(unit_price * qty * rng.uniform(0.25, 1.0))
        customer = rng.choice(customer_ids)
        date = month + pd.Timedelta(days=int(rng.integers(0, days)), hours=int(rng.integers(8, 22)), minutes=int(rng.integers(0,60)))
        payment = rng.choice(["UPI", "Card", "Cash", "Net Banking"], p=[.48,.27,.18,.07])
        rows.append({
            "order_id": f"ORD-{order_counter}", "date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "product_id": pid, "product_name": product, "category": category,
            "quantity": qty, "unit_price": round(unit_price,2), "unit_cost": round(unit_cost,2),
            "discount_pct": round(discount_pct,4), "refund_amount": round(refund_amount,2),
            "store": store, "region": region, "customer_id": customer, "payment_method": payment,
        })

df = pd.DataFrame(rows).sort_values("date")
df.to_csv(base / "sample_retail_transactions.csv", index=False)
print(f"Created {len(df)} demo transactions")
