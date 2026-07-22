import sqlite3
import pandas as pd

# ==========================================================
# CONFIGURATION
# ==========================================================

CSV_PATH = "/Users/bishnoijayanbishnoijayan/Downloads/amazon_sales_2025_INR 2.csv"
DB_NAME = "business.db"

# ==========================================================
# LOAD DATA
# ==========================================================

df = pd.read_csv(CSV_PATH)

# Clean column names
df.columns = df.columns.str.strip()

# ==========================================================
# DATABASE CONNECTION
# ==========================================================

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# ==========================================================
# DROP TABLES
# ==========================================================

cursor.executescript("""

DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Products;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Categories;

""")

# ==========================================================
# CREATE TABLES
# ==========================================================

cursor.executescript("""

CREATE TABLE Categories(
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE
);

CREATE TABLE Customers(
    customer_id TEXT PRIMARY KEY,
    state TEXT,
    country TEXT
);

CREATE TABLE Products(
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT UNIQUE,
    category_id INTEGER,

    FOREIGN KEY(category_id)
    REFERENCES Categories(category_id)
);

CREATE TABLE Orders(

    order_id TEXT PRIMARY KEY,

    order_date TEXT,

    customer_id TEXT,

    product_id INTEGER,

    quantity INTEGER,

    unit_price REAL,

    sales REAL,

    payment_method TEXT,

    delivery_status TEXT,

    rating REAL,

    review TEXT,

    FOREIGN KEY(customer_id)
    REFERENCES Customers(customer_id),

    FOREIGN KEY(product_id)
    REFERENCES Products(product_id)

);

""")

# ==========================================================
# INSERT CATEGORIES
# ==========================================================

categories = (
    df["Product_Category"]
    .drop_duplicates()
    .sort_values()
)

category_map = {}

for category in categories:

    cursor.execute(
        """
        INSERT INTO Categories(category_name)
        VALUES(?)
        """,
        (category,)
    )

    category_map[category] = cursor.lastrowid

# ==========================================================
# INSERT CUSTOMERS
# ==========================================================

customers = (
    df[
        [
            "Customer_ID",
            "State",
            "Country"
        ]
    ]
    .drop_duplicates(subset=["Customer_ID"])
)

for _, row in customers.iterrows():

    cursor.execute("""

        INSERT INTO Customers
        VALUES(?,?,?)

    """,(

        row["Customer_ID"],
        row["State"],
        row["Country"]

    ))

# ==========================================================
# INSERT PRODUCTS
# ==========================================================

products = (
    df[
        [
            "Product_Name",
            "Product_Category"
        ]
    ]
    .drop_duplicates()
)

product_map = {}

for _, row in products.iterrows():

    cursor.execute("""

        INSERT INTO Products
        (
            product_name,
            category_id
        )
        VALUES(?,?)

    """,(

        row["Product_Name"],
        category_map[row["Product_Category"]]

    ))

    product_map[row["Product_Name"]] = cursor.lastrowid

# ==========================================================
# INSERT ORDERS
# ==========================================================

for _, row in df.iterrows():

    rating = None

    if pd.notna(row["Review_Rating"]):
        rating = float(row["Review_Rating"])

    cursor.execute("""

        INSERT INTO Orders
        VALUES(?,?,?,?,?,?,?,?,?,?,?)

    """,(

        row["Order_ID"],
        row["Date"],
        row["Customer_ID"],
        product_map[row["Product_Name"]],
        int(row["Quantity"]),
        float(row["Unit_Price_INR"]),
        float(row["Total_Sales_INR"]),
        row["Payment_Method"],
        row["Delivery_Status"],
        rating,
        row["Review_Text"]

    ))

# ==========================================================
# INDEXES
# ==========================================================

cursor.executescript("""

CREATE INDEX idx_orders_customer
ON Orders(customer_id);

CREATE INDEX idx_orders_product
ON Orders(product_id);

CREATE INDEX idx_orders_date
ON Orders(order_date);

CREATE INDEX idx_orders_sales
ON Orders(sales);

CREATE INDEX idx_products_category
ON Products(category_id);

""")

# ==========================================================
# SAVE DATABASE
# ==========================================================

conn.commit()

print("\n===================================")
print("Database Created Successfully!")
print("===================================\n")

print(f"Categories : {len(categories)}")
print(f"Customers  : {len(customers)}")
print(f"Products   : {len(products)}")
print(f"Orders     : {len(df)}")

conn.close()
