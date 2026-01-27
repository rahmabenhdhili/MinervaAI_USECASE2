import csv

def load_products(csv_path: str):
    products = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                "supplier_name": row["supplier_name"],
                "city": row["city"],
                "address": row["address"],
                "phone": row["phone"],
                "email": row["email"],
                "product_name": row["product_name"],
                "category": row["category"],
                "brand": row["brand"],
                "unit_price": float(row["unit_price"])
            })
    return products
