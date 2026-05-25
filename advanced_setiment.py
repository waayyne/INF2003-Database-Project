import pandas as pd
from transformers import pipeline
import torch

class AdvancedSentimentAnalyzer:
    def __init__(self):
        # Use a pre-trained sentiment model from Hugging Face
        print("Loading sentiment model...")
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=0 if torch.cuda.is_available() else -1
        )
        
        # For aspect extraction (simplified)
        self.aspect_keywords = {
            'hydration': ['hydrating', 'moisture', 'dry', 'drying', 'dewy'],
            'coverage': ['coverage', 'buildable', 'sheer', 'full coverage'],
            'longevity': ['long lasting', 'wear', 'fades', 'stays', 'durable'],
            'texture': ['texture', 'smooth', 'gritty', 'creamy', 'thick'],
            'scent': ['smell', 'fragrance', 'scent', 'odor', 'perfume'],
            'value': ['worth', 'price', 'expensive', 'cheap', 'value']
        }
    
    def analyze_sentiment_batch(self, texts, batch_size=32):
        """Analyze sentiment for multiple texts"""
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_results = self.sentiment_pipeline(batch)
            results.extend(batch_results)
        return results
    
    def extract_aspects_advanced(self, text):
        """Extract aspects using keyword matching with context"""
        text_lower = text.lower()
        aspects_found = {}
        
        for aspect, keywords in self.aspect_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Simple context check (look for negation words nearby)
                    surrounding_text = text_lower[max(0, text_lower.find(keyword)-30):text_lower.find(keyword)+30]
                    is_negative = any(neg in surrounding_text for neg in ['not', 'no', 'never', "don't", 'isn\'t'])
                    
                    if aspect not in aspects_found:
                        aspects_found[aspect] = {'count': 0, 'negative_count': 0}
                    
                    aspects_found[aspect]['count'] += 1
                    if is_negative:
                        aspects_found[aspect]['negative_count'] += 1
        
        return aspects_found
    
    def analyze_reviews_advanced(self, df, text_column='review_text', sample_size=1000):
        """Full analysis pipeline"""
        # Take a sample for demonstration (since it's computationally intensive)
        sample_df = df.head(sample_size).copy()
        
        print(f"Analyzing {len(sample_df)} reviews with advanced model...")
        
        # Sentiment analysis
        texts = sample_df[text_column].fillna('').tolist()
        sentiment_results = self.analyze_sentiment_batch(texts)
        
        sample_df['hf_sentiment'] = [r['label'] for r in sentiment_results]
        sample_df['hf_confidence'] = [r['score'] for r in sentiment_results]
        
        # Aspect extraction
        sample_df['aspects'] = sample_df[text_column].apply(self.extract_aspects_advanced)
        
        return sample_df

# Usage example
if __name__ == "__main__":
    # Load data
    df = pd.read_csv('sample_reviews_5000.csv')
    
    # Run advanced analysis
    analyzer = AdvancedSentimentAnalyzer()
    analyzed_df = analyzer.analyze_reviews_advanced(df, sample_size=100)
    
    # Display results
    print("\n=== Advanced Analysis Results ===")
    print(analyzed_df[['review_text', 'hf_sentiment', 'hf_confidence', 'aspects']].head())
    
    # Save results
    analyzed_df.to_csv('advanced_analysis.csv', index=False)