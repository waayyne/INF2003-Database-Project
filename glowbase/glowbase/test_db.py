from db import get_mariadb_connection, get_mongo_collection

# Test MariaDB
print("=== MariaDB Test ===")
conn = get_mariadb_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT COUNT(*) as count FROM products")
print(f"Products count: {cursor.fetchone()['count']}")
cursor.execute("SELECT COUNT(*) as count FROM brands")
print(f"Brands count: {cursor.fetchone()['count']}")
cursor.close()
conn.close()

# Test MongoDB
print("\n=== MongoDB Test ===")
reviews_collection = get_mongo_collection()
print(f"Reviews count: {reviews_collection.count_documents({})}")

sample = reviews_collection.find_one()
if sample:
    print(f"Sample review: Product={sample.get('product_name')}, Rating={sample.get('rating')}")