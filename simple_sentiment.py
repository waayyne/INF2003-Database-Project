import pandas as pd
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
import re

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('punkt')

class SimpleSentimentAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
    def clean_text(self, text):
        """Basic text cleaning"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove punctuation
        return text
    
    def get_sentiment(self, text):
        """Get sentiment polarity (-1 to 1) and subjectivity"""
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity,
            'sentiment_label': 'positive' if blob.sentiment.polarity > 0.1 
                              else 'negative' if blob.sentiment.polarity < -0.1 
                              else 'neutral'
        }
    
    def extract_aspects(self, text, aspects_list):
        """Extract mentions of specific aspects"""
        text_lower = text.lower()
        found_aspects = []
        for aspect in aspects_list:
            if aspect in text_lower:
                found_aspects.append(aspect)
        return found_aspects
    
    def analyze_reviews(self, df, text_column='review_text'):
        """Main function to analyze all reviews"""
        print(f"Analyzing {len(df)} reviews...")
        
        # Clean text
        df['clean_text'] = df[text_column].apply(self.clean_text)
        
        # Get sentiment
        sentiment_results = df['clean_text'].apply(self.get_sentiment)
        df['polarity'] = sentiment_results.apply(lambda x: x['polarity'])
        df['subjectivity'] = sentiment_results.apply(lambda x: x['subjectivity'])
        df['sentiment'] = sentiment_results.apply(lambda x: x['sentiment_label'])
        
        # Define common beauty aspects
        aspects = ['moisture', 'hydrating', 'dry', 'oily', 'acne', 'smell', 
                   'fragrance', 'coverage', 'texture', 'smooth', 'soft',
                   'color', 'shade', 'long lasting', 'durable']
        
        # Extract aspects
        df['mentioned_aspects'] = df['clean_text'].apply(
            lambda x: self.extract_aspects(x, aspects)
        )
        
        return df

# Load your data
print("Loading sample data...")
df = pd.read_csv('sample_reviews_5000.csv')

# Run analysis
analyzer = SimpleSentimentAnalyzer()
analyzed_df = analyzer.analyze_reviews(df)

# Show results
print("\n=== Sentiment Analysis Results ===")
print(f"Positive reviews: {len(analyzed_df[analyzed_df['sentiment'] == 'positive'])}")
print(f"Negative reviews: {len(analyzed_df[analyzed_df['sentiment'] == 'negative'])}")
print(f"Neutral reviews: {len(analyzed_df[analyzed_df['sentiment'] == 'neutral'])}")

# Show example
print("\nExample review with analysis:")
sample_review = analyzed_df.iloc[0]
print(f"Review: {sample_review['review_text'][:200]}...")
print(f"Sentiment: {sample_review['sentiment']} (polarity: {sample_review['polarity']:.2f})")
print(f"Mentioned aspects: {sample_review['mentioned_aspects']}")

# Save analyzed data
analyzed_df.to_csv('analyzed_reviews.csv', index=False)
print("\nSaved analyzed data to 'analyzed_reviews.csv'")