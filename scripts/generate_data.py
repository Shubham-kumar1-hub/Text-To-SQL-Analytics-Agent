import os
import random
from datetime import date, timedelta

from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text

load_dotenv()

# Loading DataBase URL from .env file
engine = create_engine(os.getenv("DATABASE_URL"))

# Fixed seeds so we will get same data every time we run the script
random.seed(42)
fake = Faker("en_IN")
Faker.seed(42)

NUM_CUSTOMERS = 200 # Number of customers to generate
NUM_ORDERS = 1500 # Number of orders to generate


# List Of all The tables in the database
TABLES = [
    "customers", "addresses", "categories", "brands", "suppliers",
    "products", "inventory", "coupons", "orders", "order_items",
    "order_coupons", "payments", "shipments", "reviews", "returns",
]

def insert(conn, table, rows):
    """Inserting a list of dicts into a table in one go."""
    columns = list(rows[0].keys())
    col_list = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)
    conn.execute(
        text(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"), rows
    )


# ------------------- building the data for each table -------------------

# Customers (loyalty tier is mostly bronze, rarely gold)
customers = [
    {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": f"user{i}@{fake.free_email_domain()}",  # i keeps emails unique
        "signup_date": fake.date_between(start_date="-3y", end_date="-1m"),
        "loyalty_tier": random.choices(
            ["bronze", "silver", "gold"], weights=[70, 22, 8]
        )[0],
    }
    for i in range(NUM_CUSTOMERS)
]

# Addresses: each customer gets 1 or 2. IDs start at 1 and go up in order.
addresses = []
customer_addresses = {}  # customer_id -> list of their address ids
address_id = 0
for customer_id in range(1, NUM_CUSTOMERS + 1):
    customer_addresses[customer_id] = []
    for _ in range(random.randint(1, 2)):
        address_id += 1
        customer_addresses[customer_id].append(address_id)
        addresses.append({
            "customer_id": customer_id,
            "city": fake.city(),
            "state": fake.state(),
            "country": "India",
            "postal_code": fake.postcode(),
        })

# Categories: 5 parents (ids 1-5), then sub-categories (ids 6-14)
categories = [
    {"name": "Electronics", "parent_category_id": None},       # 1
    {"name": "Fashion", "parent_category_id": None},           # 2
    {"name": "Home & Kitchen", "parent_category_id": None},    # 3
    {"name": "Books", "parent_category_id": None},             # 4
    {"name": "Sports", "parent_category_id": None},            # 5
    {"name": "Mobiles", "parent_category_id": 1},              # 6
    {"name": "Laptops", "parent_category_id": 1},              # 7
    {"name": "Headphones", "parent_category_id": 1},           # 8
    {"name": "Men's Clothing", "parent_category_id": 2},       # 9
    {"name": "Women's Clothing", "parent_category_id": 2},     # 10
    {"name": "Footwear", "parent_category_id": 2},             # 11
    {"name": "Cookware", "parent_category_id": 3},             # 12
    {"name": "Furniture", "parent_category_id": 3},            # 13
    {"name": "Fitness Equipment", "parent_category_id": 5},    # 14
]

# Brands and suppliers
brand_names = ["Nova", "Zenith", "Urban", "Apex", "Pulse", "Orbit",
               "Terra", "Vivo", "Kite", "Lumen", "Aero", "Bolt"]
brands = [{"name": n, "country": random.choice(["India", "USA", "Japan", "Germany"])}
          for n in brand_names]
suppliers = [{"name": fake.company(), "country": "India",
              "contact_email": fake.company_email()} for _ in range(8)]

# ---------- Products ----------

# Product types per category id, and the price range (min, max) for each category
product_types = {
    6: ["Smartphone 5G", "Budget Smartphone", "Flagship Phone"],
    7: ["Gaming Laptop", "Ultrabook", "Student Laptop"],
    8: ["Wireless Earbuds", "Over-Ear Headphones", "Neckband"],
    9: ["Cotton T-Shirt", "Slim Jeans", "Formal Shirt"],
    10: ["Summer Dress", "Kurti", "Denim Jacket"],
    11: ["Running Shoes", "Leather Sandals", "Sneakers"],
    12: ["Non-stick Pan", "Pressure Cooker", "Knife Set"],
    13: ["Office Chair", "Bookshelf", "Study Table"],
    14: ["Yoga Mat", "Dumbbell Set", "Resistance Bands"],
    4: ["Programming Book", "Fiction Novel", "Self-Help Book"],
}
price_ranges = {
    6: (8000, 60000), 7: (30000, 120000), 8: (800, 15000),
    9: (300, 2500), 10: (400, 4000), 11: (600, 6000),
    12: (500, 5000), 13: (2000, 15000), 14: (400, 6000), 4: (150, 800),
}

# Create 2 products (from 2 different brands) for each product type
products = []
for category_id, types in product_types.items():
    low, high = price_ranges[category_id]
    for product_type in types:
        for brand_name in random.sample(brand_names, 2):
            price = round(random.uniform(low, high), 2)
            products.append({
                "name": f"{brand_name} {product_type}",
                "category_id": category_id,
                "brand_id": brand_names.index(brand_name) + 1,
                "supplier_id": random.randint(1, len(suppliers)),
                "price": price,
                "cost": round(price * random.uniform(0.55, 0.8), 2),  # cost is below price
                "created_at": fake.date_between(start_date="-3y", end_date="-6m"),
                "is_active": random.random() < 0.95,  # 95% are active
            })

# Quick lookup: product_id -> price (ids start at 1)
product_prices = {i + 1: p["price"] for i, p in enumerate(products)}

# Inventory: one row per product
inventory = [
    {
        "product_id": product_id,
        "stock_quantity": random.randint(0, 300),
        "reorder_level": 20,
        "last_restocked": fake.date_between(start_date="-6m", end_date="today"),
    }
    for product_id in product_prices
]

# Coupons
coupon_list = [("WELCOME10", 10), ("FESTIVE20", 20), ("SAVE15", 15),
               ("FLASH25", 25), ("LOYAL5", 5), ("SUMMER12", 12)]
coupons = [
    {"code": code, "discount_percent": pct,
     "valid_from": date.today() - timedelta(days=365),
     "valid_to": date.today() + timedelta(days=90)}
    for code, pct in coupon_list
]

# ---------- Orders and everything attached to them ----------

orders, order_items, order_coupons, payments, shipments = [], [], [], [], []
delivered_items = []  # remembered so we can create reviews and returns later
item_id = 0

for order_id in range(1, NUM_ORDERS + 1):
    customer_id = random.randint(1, NUM_CUSTOMERS)
    order_date = fake.date_time_between(start_date="-1y", end_date="now")
    status = random.choices(
        ["delivered", "shipped", "placed", "cancelled"], weights=[70, 12, 8, 10]
    )[0]

    # The order uses one of the customer's own addresses
    orders.append({
        "customer_id": customer_id,
        "address_id": random.choice(customer_addresses[customer_id]),
        "order_date": order_date,
        "status": status,
    })

    # 1 to 4 different products per order
    total = 0
    for product_id in random.sample(range(1, len(products) + 1), random.randint(1, 4)):
        item_id += 1
        quantity = random.randint(1, 3)
        price = product_prices[product_id]
        total += price * quantity
        order_items.append({
            "order_id": order_id, "product_id": product_id,
            "quantity": quantity, "unit_price": price,
        })
        if status == "delivered":
            delivered_items.append({
                "item_id": item_id, "customer_id": customer_id,
                "product_id": product_id, "order_date": order_date,
                "amount": price * quantity,
            })

    # 20% of orders use a coupon, which reduces the total
    if random.random() < 0.2:
        coupon_id = random.randint(1, len(coupons))
        order_coupons.append({"order_id": order_id, "coupon_id": coupon_id})
        total = total * (100 - coupons[coupon_id - 1]["discount_percent"]) / 100

    # One payment per order; cancelled orders are refunded or failed
    if status == "cancelled":
        payment_status = random.choice(["refunded", "failed"])
    else:
        payment_status = "paid"
    payments.append({
        "order_id": order_id,
        "amount": round(total, 2),
        "method": random.choice(["card", "upi", "netbanking", "cod"]),
        "payment_status": payment_status,
        "paid_at": order_date + timedelta(minutes=random.randint(1, 30)),
    })

    # Shipments exist only for shipped or delivered orders
    if status in ("shipped", "delivered"):
        shipped_date = order_date.date() + timedelta(days=random.randint(1, 2))
        delivered_date = None
        if status == "delivered":
            delivered_date = shipped_date + timedelta(days=random.randint(2, 7))
        shipments.append({
            "order_id": order_id,
            "carrier": random.choice(["BlueDart", "Delhivery", "DTDC", "EcomExpress"]),
            "shipped_date": shipped_date,
            "delivered_date": delivered_date,
            "tracking_number": fake.bothify("TRK##########"),
        })

# ---------- Reviews and returns (only for delivered items) ----------

comments = {
    "low": ["Poor quality, not worth the price", "Stopped working quickly"],
    "mid": ["Average product, does the job", "Okay for the price"],
    "high": ["Great quality, highly recommended", "Excellent value for money"],
}

reviews = []
for item in random.sample(delivered_items, 500):
    # Ratings skew positive, like real review data
    rating = random.choices([1, 2, 3, 4, 5], weights=[5, 8, 15, 35, 37])[0]
    group = "low" if rating <= 2 else "mid" if rating == 3 else "high"
    review_date = item["order_date"].date() + timedelta(days=random.randint(5, 20))
    reviews.append({
        "product_id": item["product_id"],
        "customer_id": item["customer_id"],
        "rating": rating,
        "comment": random.choice(comments[group]),
        "review_date": min(review_date, date.today()),  # never in the future
    })

# About 5% of delivered items get returned
returns = []
for item in delivered_items:
    if random.random() < 0.05:
        return_date = item["order_date"].date() + timedelta(days=random.randint(7, 14))
        returns.append({
            "order_item_id": item["item_id"],
            "reason": random.choice(["Defective", "Wrong size", "Not as described", "Changed mind"]),
            "return_date": min(return_date, date.today()),
            "refund_amount": round(item["amount"], 2),
        })


# ---------- Writing everything to the database ----------

with engine.begin() as conn:
    # Empty all tables first so the script can be re-run safely
    conn.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))

    # Inserting parents before children
    insert(conn, "customers", customers)
    insert(conn, "addresses", addresses)
    insert(conn, "categories", categories)
    insert(conn, "brands", brands)
    insert(conn, "suppliers", suppliers)
    insert(conn, "products", products)
    insert(conn, "inventory", inventory)
    insert(conn, "coupons", coupons)
    insert(conn, "orders", orders)
    insert(conn, "order_items", order_items)
    insert(conn, "order_coupons", order_coupons)
    insert(conn, "payments", payments)
    insert(conn, "shipments", shipments)
    insert(conn, "reviews", reviews)
    insert(conn, "returns", returns)

# Printing how many rows each table now has
with engine.connect() as conn:
    for table in TABLES:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count}")