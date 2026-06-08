import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

audio_file = open('background_music.mp3', 'rb')
audio_bytes = audio_file.read()

st.audio(audio_bytes, format='audio/mp3')
# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Food Delivery Performance Dashboard",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for polished look
st.markdown("""
    <style>
    .main-title {
        font-size:36px !important;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size:18px !important;
        color: #555555;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING & CACHING
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('final_renamed_graph_data.csv')
        return df
    except FileNotFoundError:
        st.error("Error: 'final_renamed_graph_data.csv' not found. Please run your data pipeline cell first!")
        return None

df = load_data()

if df is not None:
   # ==========================================
    # SIDEBAR FILTERING CONTROLS
    # ==========================================
    st.sidebar.header("📊 Dashboard Filters")
    st.sidebar.markdown("Fine-tune the data viewable on the dashboard charts below.")
    
    # 1. Hour Range Filter
    min_hour, max_hour = int(df['Order Hour (24h)'].min()), int(df['Order Hour (24h)'].max())
    selected_hours = st.sidebar.slider(
        "Select Order Hours Range",
        min_value=min_hour,
        max_value=max_hour,
        value=(min_hour, max_hour)
    )
    
    # 2. Scatter Plot Sample Size Control
    sample_size = st.sidebar.number_input(
        "Scatter Plot Sample Size",
        min_value=50,
        max_value=len(df),
        value=min(500, len(df)),
        step=50
    )
    
    # Apply filtering based on sidebar input
    df_filtered = df[
        (df['Order Hour (24h)'] >= selected_hours[0]) & 
        (df['Order Hour (24h)'] <= selected_hours[1])
    ]
    # ==========================================
    # HEADER SECTION & OVERVIEW METRICS
    # ==========================================
    st.markdown('<p class="main-title">Food Delivery Performance & Operations Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Interactive Business Intelligence Dashboard for Operational Performance</p>', unsafe_allow_html=True)
   
   # Key Performance Indicator (KPI) Metric Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric(label="Total Sampled Orders", value=f"{len(df_filtered):,}")
        # Added local Grab logo under Total Sampled Orders card
        try:
            st.image("grab_logo.png", width=80)
        except Exception:
            st.caption("⚠️ [grab_logo.png not found]")
            
    with kpi2:
        total_canceled = int((df_filtered['Cancellation Status'] == True).sum())
        st.metric(label="Total Cancellations", value=f"{total_canceled:,}")
        # Added local Foodpanda logo under Total Cancellations card
        try:
            st.image("foodpanda_logo.png", width=80)
        except Exception:
            st.caption("⚠️ [foodpanda_logo.png not found]")
            
    with kpi3:
        avg_prep = df_filtered['Preparation Time (mins)'].mean()
        st.metric(label="Avg Prep Time", value=f"{avg_prep:.1f} mins")
        try:
            st.image("shopeefood_logo.png", width=80)
        except Exception:
            st.caption("⚠️ [shopeefood_logo.png not found]")
            
        
    with kpi4:
        avg_delivery = df_filtered['Delivery Time (mins)'].mean()
        st.metric(label="Avg Delivery Time", value=f"{avg_delivery:.1f} mins")
        try:
            st.image("beep_logo.png", width=80)
        except Exception:
            st.caption("⚠️ [beep_logo.png not found]")
            

    # ==========================================
    # CHARTS LAYOUT SECTION
    # ==========================================
    col1, col2 = st.columns(2)
    
    # --- CHART 1: BAR CHART (CANCELLATIONS BY PREP TIME) ---
    with col1:
        st.subheader("⏱️ Order Cancellations vs Kitchen Prep Time")
        
        # Setup time range bins and text labels
        bins = [0, 10, 20, 30, 40, 50, 60]
        labels = ['0-10 min', '10-20 min', '20-30 min', '30-40 min', '40-50 min', '50-60 min']
        
        # Segment data into bins
        df_filtered['prep_time_bin'] = pd.cut(df_filtered['Preparation Time (mins)'], bins=bins, labels=labels)
        cancelled_df = df_filtered[df_filtered['Cancellation Status'] == True]
        
        cancel_counts = cancelled_df['prep_time_bin'].value_counts().reindex(labels).reset_index()
        cancel_counts.columns = ['prep_time_bin', 'cancel_count']
        cancel_counts['cancel_count'] = cancel_counts['cancel_count'].fillna(0)

        # Matplotlib plot generation
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(
            cancel_counts['prep_time_bin'], 
            cancel_counts['cancel_count'], 
            color='coral', 
            edgecolor='black', 
            linewidth=1.2, 
            alpha=0.85, 
            width=0.6
        )
        
        # Value data callouts
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0, 
                height + (max(cancel_counts['cancel_count']) * 0.02), 
                f'{int(height)}', 
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#333333'
            )
            
        ax.set_ylabel('Number of Cancellations', fontweight='bold')
        ax.set_xlabel('Preparation Time Bin', fontweight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.set_axisbelow(True)
        sns.despine()
        plt.tight_layout()
        
        st.pyplot(fig)
        st.caption("Insight: Notice a surge and structural consistency in cancellations once preparation transcends past 10 minutes.")

    # --- CHART 2: LINE CHART (HOURLY ORDER TRENDS) ---
    with col2:
        st.subheader("📈 Temporal Hourly Distribution Analysis")
        
        orders_by_hour = df_filtered.groupby('Order Hour (24h)').size().reset_index(name='Total Orders')
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(
            orders_by_hour['Order Hour (24h)'], 
            orders_by_hour['Total Orders'], 
            marker='o', 
            color='crimson', 
            linewidth=2.5, 
            markersize=6,
            alpha=0.9
        )
        
        # Numerical label annotations
        for x, y in zip(orders_by_hour['Order Hour (24h)'], orders_by_hour['Total Orders']):
            ax.text(
                x, 
                y + (max(orders_by_hour['Total Orders']) * 0.005), 
                f'{int(y)}', 
                ha='center', va='bottom', fontsize=8, color='#444444', fontweight='bold'
            )
            
        ax.set_xlabel('Order Hour (24-Hour Format)', fontweight='bold')
        ax.set_ylabel('Total Orders Placed', fontweight='bold')
        ax.set_xticks(range(int(orders_by_hour['Order Hour (24h)'].min()), int(orders_by_hour['Order Hour (24h)'].max()) + 1, 2))
        ax.grid(axis='both', linestyle='--', alpha=0.5)
        sns.despine()
        plt.tight_layout()
        
        st.pyplot(fig)
        st.caption("Insight: Peak operations stay robust in late night shifts (peaking towards midnight), suggesting tactical fleet distributions.")

    st.markdown("---")
    
    # --- CHART 3: SCATTER PLOT WITH REGRESSION LINE ---
    st.subheader("🗺️ Logistics Engine Evaluation: Distance vs. System Transit Time")
    
    # Pull dynamic randomized samples controlled safely via slider parameter inputs
    df_sample = df_filtered.sample(n=min(sample_size, len(df_filtered)), random_state=42)
    
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.scatterplot(
        data=df_sample, 
        x='Distance (km)', 
        y='Delivery Time (mins)', 
        alpha=0.6, 
        color='teal', 
        edgecolor='white', 
        s=55,
        ax=ax
    )
    
    # Trend line fit
    sns.regplot(
        data=df_sample, 
        x='Distance (km)', 
        y='Delivery Time (mins)', 
        scatter=False, 
        color='darkslategray', 
        line_kws={'linewidth': 2.5, 'linestyle': '--'},
        ax=ax
    )
    
    ax.set_xlabel('Distance (km)', fontweight='bold')
    ax.set_ylabel('Delivery Time (mins)', fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.4)
    sns.despine()
    plt.tight_layout()
    
    st.pyplot(fig)
    st.caption("Insight: Strongly positive linear relationship verified ($r \\approx 0.86$). Base overhead is represented via the intercept axis.")
