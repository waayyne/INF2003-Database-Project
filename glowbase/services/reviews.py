from db import get_mongo_collection
from utils import fix_mongo_id


def get_reviews_by_product_id(product_id):
    reviews_collection = get_mongo_collection()

    reviews = list(
        reviews_collection.find(
            {"product_id": str(product_id)}
        ).limit(10)
    )

    return [fix_mongo_id(review) for review in reviews]


def get_product_chemicals(product_id):
    reviews_collection = get_mongo_collection()
    pipeline = [
        {"$match": {"product_id": product_id, "chemicals": {"$exists": True, "$ne": []}}},
        {"$unwind": "$chemicals"},
        {"$group": {"_id": "$chemicals"}}
    ]
    chemical_results = list(reviews_collection.aggregate(pipeline))
    return [chem["_id"] for chem in chemical_results]
