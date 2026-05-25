import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Beauty Review Analyzer", layout="wide")
st.title("✨ Beauty Product Review Analyzer")

# Load your analyzed data (create this first from Phase 3)
@st.cache_data
def load_data():
    # If you haven't run analysis yet, create a simple version
    try:
        df = pd.read_csv('analyzed_reviews.csv')
    except:
        # Create dummy data if no analysis done yet
        st.warning("Running sample analysis on first 1000 reviews...")
        # Load your data here
        df = pd.read_csv('sample_reviews_5000.csv')
        df['sentiment'] = 'positive'  # Placeholder
        df['polarity'] = 0.5
    
    return df

df = load_data()

# Display basic stats
col1, col2, col3 = st.columns(3)
col1.metric("Total Reviews", len(df))
col2.metric("Unique Products", df['product_id'].nunique())
col3.metric("Unique Brands", df['brand_name'].nunique())

# Simple product selector
st.subheader("🔍 Find Product Reviews")
product_list = df['product_name'].dropna().unique()
selected_product = st.selectbox("Choose a product", product_list)

if selected_product:
    product_reviews = df[df['product_name'] == selected_product]
    
    col1, col2 = st.columns(2)
    with col1:
        avg_rating = product_reviews['rating'].mean()
        st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
    
    with col2:
        st.metric("Number of Reviews", len(product_reviews))
    
    st.subheader("Sample Reviews")
    st.dataframe(product_reviews[['rating', 'review_text']].head(10))

print("✅ Ready to run! Use: streamlit run app.py")