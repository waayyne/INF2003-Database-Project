import os
import glob
import pandas as pd
import numpy as np

# Load your data (adjust file paths to match your actual files)
base_dir = os.path.dirname(__file__)
print("Loading data...")

# Look for the expected reviews file, with fallbacks to files like 'reviews_0-250.csv'
candidates = [os.path.join(base_dir, 'reviews.csv')] + sorted(glob.glob(os.path.join(base_dir, 'reviews*.csv')))
reviews_path = None
for c in candidates:
    if os.path.exists(c):
        reviews_path = c
        break
if reviews_path is None:
    # try any CSV that looks like reviews (contains 'review' in filename)
    candidates2 = [p for p in sorted(glob.glob(os.path.join(base_dir, '*.csv'))) if 'review' in os.path.basename(p).lower()]
    if candidates2:
        reviews_path = candidates2[0]
if reviews_path is None:
    available = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(base_dir, '*.csv')))]
    raise FileNotFoundError(f"Couldn't find 'reviews.csv' or 'reviews*.csv'. CSVs in project: {available}")

print(f"Loading data from {os.path.basename(reviews_path)}")
products_df = pd.read_csv(os.path.join(base_dir, 'product_info.csv'))
reviews_df = pd.read_csv(reviews_path)

# Basic info
print(f"Products: {len(products_df)} rows")
print(f"Reviews: {len(reviews_df)} rows")
print("\nFirst 5 reviews:")
print(reviews_df.head())

# Check for missing values
print("\nMissing values in reviews:")
print(reviews_df.isnull().sum())

# Explore ratings distribution
print("\nRating distribution:")
print(reviews_df['rating'].value_counts().sort_index())

# Explore skin types
print("\nSkin type distribution:")
print(reviews_df['skin_type'].value_counts())

# Merge product info with reviews
merged_df = reviews_df.merge(
    products_df[['product_id', 'product_name', 'brand_name', 'price_usd', 'primary_category']], 
    on='product_id', 
    how='left'
)

print(f"\nMerged data shape: {merged_df.shape}")
print("\nColumns available:", merged_df.columns.tolist())

# Save a sample for faster prototyping
sample_n = min(5000, len(merged_df))
sample_df = merged_df.sample(n=sample_n, random_state=42)
sample_df.to_csv(os.path.join(base_dir, 'sample_reviews_5000.csv'), index=False)
print(f"\nSaved {sample_n} sample reviews for faster development!")