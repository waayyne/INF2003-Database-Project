import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class BeautyRecommender:
    def __init__(self, products_df, reviews_df):
        self.products_df = products_df
        self.reviews_df = reviews_df
        
        # Calculate product aggregates
        self.product_scores = reviews_df.groupby('product_id').agg({
            'rating': 'mean',
            'polarity': 'mean',
            'review_text': 'count'
        }).rename(columns={'review_text': 'review_count'})
        
        # Merge with product info
        self.product_features = self.products_df.merge(
            self.product_scores, 
            on='product_id', 
            how='inner'
        )
        
        # Create text features for similarity
        self._prepare_text_features()
    
    def _prepare_text_features(self):
        """Combine product name, brand, category, and highlights for similarity"""
        self.product_features['text_features'] = (
            self.product_features['product_name'].fillna('') + ' ' +
            self.product_features['brand_name'].fillna('') + ' ' +
            self.product_features['primary_category'].fillna('') + ' ' +
            self.product_features['highlights'].apply(
                lambda x: ' '.join(eval(x)) if pd.notna(x) else ''
            )
        )
        
        # Create TF-IDF matrix
        self.tfidf = TfidfVectorizer(stop_words='english', max_features=1000)
        self.tfidf_matrix = self.tfidf.fit_transform(self.product_features['text_features'])
    
    def recommend_by_text(self, query, top_n=5):
        """Recommend products based on text query"""
        query_vec = self.tfidf.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        top_indices = similarities.argsort()[-top_n:][::-1]
        recommendations = self.product_features.iloc[top_indices][
            ['product_name', 'brand_name', 'rating', 'review_count']
        ].copy()
        recommendations['similarity_score'] = similarities[top_indices]
        
        return recommendations
    
    def recommend_by_skin_type(self, skin_type, top_n=10):
        """Recommend products highly rated by users with specific skin type"""
        skin_reviews = self.reviews_df[self.reviews_df['skin_type'] == skin_type]
        
        if len(skin_reviews) == 0:
            return pd.DataFrame()
        
        skin_ratings = skin_reviews.groupby('product_id')['rating'].mean()
        skin_counts = skin_reviews.groupby('product_id')['rating'].count()
        
        # Filter products with at least 3 reviews
        valid_products = skin_counts[skin_counts >= 3].index
        
        recommendations = self.product_features[
            self.product_features['product_id'].isin(valid_products)
        ].copy()
        
        recommendations['skin_type_rating'] = recommendations['product_id'].map(skin_ratings)
        recommendations = recommendations.dropna(subset=['skin_type_rating'])
        recommendations = recommendations.sort_values('skin_type_rating', ascending=False)
        
        return recommendations.head(top_n)[
            ['product_name', 'brand_name', 'rating', 'review_count', 'skin_type_rating']
        ]
    
    def get_product_details(self, product_id):
        """Get detailed info about a product"""
        product = self.product_features[self.product_features['product_id'] == product_id]
        if len(product) == 0:
            return None
        
        # Get sample reviews
        reviews = self.reviews_df[self.reviews_df['product_id'] == product_id].head(5)
        
        return {
            'product': product.iloc[0].to_dict(),
            'reviews': reviews[['rating', 'sentiment', 'review_text']].to_dict('records')
        }

# Usage example
if __name__ == "__main__":
    # Load data
    products = pd.read_csv('product_info.csv')
    reviews = pd.read_csv('analyzed_reviews.csv')  # From earlier step
    
    # Create recommender
    recommender = BeautyRecommender(products, reviews)
    
    # Test text recommendation
    print("\n=== Recommendations for 'natural looking foundation' ===")
    results = recommender.recommend_by_text("natural looking foundation", top_n=5)
    print(results)
    
    # Test skin type recommendation
    print("\n=== Recommendations for Dry Skin ===")
    dry_skin_recs = recommender.recommend_by_skin_type('dry', top_n=5)
    print(dry_skin_recs)