import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="CosmiQ Beauty Insights", layout="wide")

st.title("💄 CosmiQ: Beauty Product Sentiment Analyzer")
st.markdown("---")

# Load data with better error handling
@st.cache_data
def load_data():
    """Load and prepare the data"""
    try:
        # Try to load analyzed data first
        df = pd.read_csv('analyzed_reviews.csv')
        st.success("✅ Loaded analyzed reviews data")
        return df
    except FileNotFoundError:
        try:
            # Fall back to sample data
            df = pd.read_csv('sample_reviews_5000.csv')
            st.warning("⚠️ Using sample data (run simple_sentiment.py first for full analysis)")
            
            # Add basic sentiment if not present
            if 'sentiment' not in df.columns:
                # Simple rule-based sentiment as fallback
                df['sentiment'] = df['rating'].apply(
                    lambda x: 'positive' if x >= 4 else ('negative' if x <= 2 else 'neutral')
                )
                df['polarity'] = (df['rating'] - 3) / 2
            return df
        except FileNotFoundError:
            st.error("❌ No data files found! Creating sample data...")
            # Create sample data for demonstration
            sample_data = {
                'product_name': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'] * 20,
                'rating': [5,4,3,2,1] * 20,
                'sentiment': ['positive', 'positive', 'neutral', 'negative', 'negative'] * 20,
                'review_text': ['Great product!'] * 100,
                'brand_name': ['Brand X'] * 100,
                'skin_type': ['dry', 'oily', 'combination'] * 33 + ['dry']
            }
            df = pd.DataFrame(sample_data)
            st.info("📝 Using demo data for testing")
            return df

# Load the data
df = load_data()

if df.empty:
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filter Reviews")

# Rating filter
rating_filter = st.sidebar.slider("Minimum Rating", 1, 5, 3)

# Skin type filter (only show if column exists)
if 'skin_type' in df.columns and df['skin_type'].notna().any():
    skin_types = ['All'] + sorted(df['skin_type'].dropna().unique().tolist())
    skin_filter = st.sidebar.selectbox("Skin Type", skin_types)
else:
    skin_filter = 'All'

# Sentiment filter
sentiment_filter = st.sidebar.multiselect(
    "Sentiment", 
    ['positive', 'neutral', 'negative'],
    default=['positive', 'neutral', 'negative']
)

# Brand filter
if 'brand_name' in df.columns:
    brands = ['All'] + sorted(df['brand_name'].dropna().unique().tolist())
    brand_filter = st.sidebar.selectbox("Brand", brands)
else:
    brand_filter = 'All'

# Apply filters
filtered_df = df[df['rating'] >= rating_filter].copy()
filtered_df = filtered_df[filtered_df['sentiment'].isin(sentiment_filter)]

if skin_filter != 'All' and 'skin_type' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['skin_type'] == skin_filter]

if brand_filter != 'All' and 'brand_name' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['brand_name'] == brand_filter]

# Main content - Row 1: Key Metrics
st.subheader("📈 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Reviews", f"{len(filtered_df):,}")

with col2:
    avg_rating = filtered_df['rating'].mean()
    st.metric("Avg Rating", f"{avg_rating:.2f} ⭐")

with col3:
    if 'polarity' in filtered_df.columns:
        avg_polarity = filtered_df['polarity'].mean()
        st.metric("Avg Sentiment Score", f"{avg_polarity:.2f}")
    else:
        st.metric("Avg Sentiment Score", "N/A")

with col4:
    pos_pct = (filtered_df['sentiment'] == 'positive').mean() * 100
    st.metric("Positive Reviews %", f"{pos_pct:.1f}%")

st.markdown("---")

# Row 2: Two columns for charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Rating Distribution")
    rating_counts = filtered_df['rating'].value_counts().sort_index().reset_index()
    rating_counts.columns = ['Rating', 'Count']
    fig1 = px.bar(rating_counts, x='Rating', y='Count', 
                  title="Distribution of Star Ratings")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("😊 Sentiment Distribution")
    sentiment_counts = filtered_df['sentiment'].value_counts().reset_index()
    sentiment_counts.columns = ['Sentiment', 'Count']
    fig2 = px.pie(sentiment_counts, values='Count', names='Sentiment',
                  title="Sentiment Breakdown")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Row 3: Top Products
if 'product_name' in filtered_df.columns:
    st.subheader("🏆 Top Rated Products")
    
    top_products = filtered_df.groupby('product_name').agg({
        'rating': 'mean',
        'review_text': 'count'
    }).rename(columns={'review_text': 'review_count'}).sort_values('rating', ascending=False).head(10)
    
    if not top_products.empty:
        fig3 = px.bar(top_products.reset_index(), x='product_name', y='rating',
                      color='review_count', 
                      title="Top 10 Products by Rating",
                      labels={'product_name': 'Product', 'rating': 'Average Rating'})
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
        
        with st.expander("View Top Products Data"):
            st.dataframe(top_products)

st.markdown("---")

# Row 4: Product Search
if 'product_name' in filtered_df.columns:
    st.subheader("🔎 Search Specific Product")
    
    product_list = filtered_df['product_name'].dropna().unique()
    if len(product_list) > 0:
        selected_product = st.selectbox("Select a product to see detailed reviews", product_list)
        
        if selected_product:
            product_reviews = filtered_df[filtered_df['product_name'] == selected_product]
            
            # Product stats
            col1, col2, col3 = st.columns(3)
            with col1:
                product_rating = product_reviews['rating'].mean()
                st.metric("Product Rating", f"{product_rating:.2f} ⭐")
            with col2:
                st.metric("Number of Reviews", len(product_reviews))
            with col3:
                if 'price_usd' in product_reviews.columns:
                    product_price = product_reviews['price_usd'].iloc[0] if len(product_reviews) > 0 else 0
                    st.metric("Price", f"${product_price:.2f}")
            
            # Show sentiment breakdown
            prod_sentiment = product_reviews['sentiment'].value_counts().reset_index()
            prod_sentiment.columns = ['Sentiment', 'Count']
            if not prod_sentiment.empty:
                fig4 = px.pie(prod_sentiment, values='Count', names='Sentiment', 
                             title="Sentiment for this Product")
                st.plotly_chart(fig4, use_container_width=True)
            
            # Show reviews
            with st.expander(f"📝 View {len(product_reviews)} Reviews"):
                display_cols = ['rating', 'sentiment', 'review_text']
                available_cols = [col for col in display_cols if col in product_reviews.columns]
                st.dataframe(product_reviews[available_cols].head(20))

st.markdown("---")

# Row 5: Recent Reviews
st.subheader("📝 Sample Reviews")

# Display a few reviews
sample_reviews = filtered_df.head(10)
for idx, row in sample_reviews.iterrows():
    sentiment_emoji = "😊" if row['sentiment'] == 'positive' else ("😐" if row['sentiment'] == 'neutral' else "😞")
    
    product_name = row.get('product_name', 'Unknown Product')
    rating = row.get('rating', 'N/A')
    review_text = row.get('review_text', 'No review text')
    
    with st.container():
        st.markdown(f"""
        **{product_name}** {sentiment_emoji} Rating: {rating}/5 ⭐
        
        > {review_text[:200]}...
        ---
        """)

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.info(
    """
    **About CosmiQ**
    
    Analyzing beauty product reviews to help you make informed decisions.
    
    **Data files needed:**
    - analyzed_reviews.csv
    - sample_reviews_5000.csv
    - product_info.csv
    
    Run `python data_explorer.py` to prepare data.
    """
)

st.markdown("---")
st.caption("CosmiQ - Sentiment-Aware Beauty Product Recommendation Engine")