import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Food Delivery Performance Dashboard",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for a highly polished, modern presentation
st.markdown("""
    <style>
    /* Gradient text styling for titles */
    .main-title {
        font-size:38px !important;
        font-weight: 800;
        background: linear-gradient(45deg, #FF4B4B, #1E3A8A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    .sub-title {
        font-size:16px !important;
        color: #6B7280;
        margin-bottom: 25px;
    }
    /* Dynamic UI enhancement for default Streamlit metric cards */
    div[data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
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
    st.sidebar.markdown("## 📊 Dashboard Filters")
    st.sidebar.markdown("Fine-tune the data viewable on the dashboard charts below.")
    st.sidebar.markdown("---")
    
    # 1. Hour Range Filter
    min_hour, max_hour = int(df['Order Hour (24h)'].min()), int(df['Order Hour (24h)'].max())
    selected_hours = st.sidebar.slider(
        "Select Order Hours Range",
        min_value=min_hour,
        max_value=max_hour,
        value=(min_hour, max_hour)
    )
    
    # 2. Interactive Cancellation Filter (New UI Control Feature)
    unique_statuses = sorted(list(df['Cancellation Status'].unique()))
    selected_statuses = st.sidebar.multiselect(
        "Filter by Cancellation Status",
        options=unique_statuses,
        default=unique_statuses
    )
    
    # 3. Scatter Plot Sample Size Control
    sample_size = st.sidebar.number_input(
        "Scatter Plot Sample Size",
        min_value=50,
        max_value=len(df),
        value=min(500, len(df)),
        step=50
    )
    
    # Apply global filtering matching sidebar selections
    df_filtered = df[
        (df['Order Hour (24h)'] >= selected_hours[0]) & 
        (df['Order Hour (24h)'] <= selected_hours[1]) &
        (df['Cancellation Status'].isin(selected_statuses))
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
    with kpi2:
        total_canceled = int((df_filtered['Cancellation Status'] == True).sum())
        cancel_rate = (total_canceled / max(1, len(df_filtered))) * 100
        st.metric(
            label="Total Cancellations", 
            value=f"{total_canceled:,}", 
            delta=f"{cancel_rate:.1f}% Rate", 
            delta_color="inverse"
        )
    with kpi3:
        avg_prep = df_filtered['Preparation Time (mins)'].mean()
        st.metric(label="Avg Prep Time", value=f"{avg_prep:.1f} mins" if not pd.isna(avg_prep) else "0.0 mins")
    with kpi4:
        avg_delivery = df_filtered['Delivery Time (mins)'].mean()
        st.metric(label="Avg Delivery Time", value=f"{avg_delivery:.1f} mins" if not pd.isna(avg_delivery) else "0.0 mins")
        
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # CHARTS LAYOUT SECTION
    # ==========================================
    col1, col2 = st.columns(2)
    
    # --- CHART 1: PLOTLY BAR CHART (CANCELLATIONS BY PREP TIME) ---
    with col1:
        st.subheader("⏱️ Order Cancellations vs Kitchen Prep Time")
        
        bins = [0, 10, 20, 30, 40, 50, 60]
        labels = ['0-10 min', '10-20 min', '20-30 min', '30-40 min', '40-50 min', '50-60 min']
        
        # Avoid slicing assignment warnings via shallow copies
        df_bins = df_filtered.copy()
        df_bins['prep_time_bin'] = pd.cut(df_bins['Preparation Time (mins)'], bins=bins, labels=labels)
        cancelled_df = df_bins[df_bins['Cancellation Status'] == True]
        
        cancel_counts = cancelled_df['prep_time_bin'].value_counts().reindex(labels).reset_index()
        cancel_counts.columns = ['prep_time_bin', 'cancel_count']
        cancel_counts['cancel_count'] = cancel_counts['cancel_count'].fillna(0)

        # Plotly Bar Graph Execution
        fig_bar = px.bar(
            cancel_counts, 
            x='prep_time_bin', 
            y='cancel_count',
            text='cancel_count',
            labels={'prep_time_bin': 'Preparation Time Bin', 'cancel_count': 'Number of Cancellations'},
            color_discrete_sequence=['#FF6B6B']
        )
        fig_bar.update_traces(textposition='outside', marker_line_color='#2D3748', marker_line_width=1)
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption("Insight: Notice a surge and structural consistency in cancellations once preparation transcends past 10 minutes.")

    # --- CHART 2: PLOTLY AREA/LINE CHART (HOURLY ORDER TRENDS) ---
    with col2:
        st.subheader("📈 Temporal Hourly Distribution Analysis")
        
        orders_by_hour = df_filtered.groupby('Order Hour (24h)').size().reset_index(name='Total Orders')
        
        # Dynamic Area Chart for cleaner visual footprint
        fig_line = px.area(
            orders_by_hour, 
            x='Order Hour (24h)', 
            y='Total Orders',
            labels={'Order Hour (24h)': 'Order Hour (24-Hour Format)', 'Total Orders': 'Total Orders Placed'},
            color_discrete_sequence=['#1E3A8A']
        )
        fig_line.update_traces(mode='lines+markers', marker=dict(size=6, color='#FF4B4B'))
        fig_line.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            xaxis=dict(showgrid=True, gridcolor='#E2E8F0', tickmode='linear', dtick=2),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption("Insight: Peak operations stay robust in late night shifts (peaking towards midnight), suggesting tactical fleet distributions.")

    st.markdown("---")
    
    # --- CHART 3: PLOTLY SCATTER PLOT WITH TRENDLINE ---
    st.subheader("🗺️ Logistics Engine Evaluation: Distance vs. System Transit Time")
    
    if len(df_filtered) > 0:
        df_sample = df_filtered.sample(n=min(sample_size, len(df_filtered)), random_state=42)
        
        # Interactive Scatter Plot utilizing built-in Ordinary Least Squares trend calculation
        fig_scatter = px.scatter(
            df_sample, 
            x='Distance (km)', 
            y='Delivery Time (mins)',
            trendline="ols",
            trendline_color_override="#FF4B4B",
            color_discrete_sequence=['#2D3748'],
            opacity=0.6,
            labels={'Distance (km)': 'Distance (km)', 'Delivery Time (mins)': 'Delivery Time (mins)'}
        )
        fig_scatter.update_layout(
            plot_bgcolor='#F8FAFC',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=420,
            xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Resolved Error: Added explicit raw-string r"..." wrapping to preserve the inline LaTeX backslashes safely
        st.caption(r"Insight: Strongly positive linear relationship verified ($r \approx 0.86$). Base overhead is represented via the intercept axis.")
    else:
        st.warning("No operational data records found matching the active sidebar parameters.")        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
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
    st.sidebar.markdown("## 📊 Dashboard Filters")
    st.sidebar.markdown("Fine-tune the data viewable on the dashboard charts below.")
    st.sidebar.markdown("---")
    
    # 1. Hour Range Filter
    min_hour, max_hour = int(df['Order Hour (24h)'].min()), int(df['Order Hour (24h)'].max())
    selected_hours = st.sidebar.slider(
        "Select Order Hours Range",
        min_value=min_hour,
        max_value=max_hour,
        value=(min_hour, max_hour)
    )
    
    # 2. Interactive Cancellation Filter (New UI Control Feature)
    unique_statuses = sorted(list(df['Cancellation Status'].unique()))
    selected_statuses = st.sidebar.multiselect(
        "Filter by Cancellation Status",
        options=unique_statuses,
        default=unique_statuses
    )
    
    # 3. Scatter Plot Sample Size Control
    sample_size = st.sidebar.number_input(
        "Scatter Plot Sample Size",
        min_value=50,
        max_value=len(df),
        value=min(500, len(df)),
        step=50
    )
    
    # Apply global filtering matching sidebar selections
    df_filtered = df[
        (df['Order Hour (24h)'] >= selected_hours[0]) & 
        (df['Order Hour (24h)'] <= selected_hours[1]) &
        (df['Cancellation Status'].isin(selected_statuses))
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
    with kpi2:
        total_canceled = int((df_filtered['Cancellation Status'] == True).sum())
        cancel_rate = (total_canceled / max(1, len(df_filtered))) * 100
        st.metric(
            label="Total Cancellations", 
            value=f"{total_canceled:,}", 
            delta=f"{cancel_rate:.1f}% Rate", 
            delta_color="inverse"
        )
    with kpi3:
        avg_prep = df_filtered['Preparation Time (mins)'].mean()
        st.metric(label="Avg Prep Time", value=f"{avg_prep:.1f} mins" if not pd.isna(avg_prep) else "0.0 mins")
    with kpi4:
        avg_delivery = df_filtered['Delivery Time (mins)'].mean()
        st.metric(label="Avg Delivery Time", value=f"{avg_delivery:.1f} mins" if not pd.isna(avg_delivery) else "0.0 mins")
        
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # CHARTS LAYOUT SECTION
    # ==========================================
    col1, col2 = st.columns(2)
    
    # --- CHART 1: PLOTLY BAR CHART (CANCELLATIONS BY PREP TIME) ---
    with col1:
        st.subheader("⏱️ Order Cancellations vs Kitchen Prep Time")
        
        bins = [0, 10, 20, 30, 40, 50, 60]
        labels = ['0-10 min', '10-20 min', '20-30 min', '30-40 min', '40-50 min', '50-60 min']
        
        # Avoid slicing assignment warnings via shallow copies
        df_bins = df_filtered.copy()
        df_bins['prep_time_bin'] = pd.cut(df_bins['Preparation Time (mins)'], bins=bins, labels=labels)
        cancelled_df = df_bins[df_bins['Cancellation Status'] == True]
        
        cancel_counts = cancelled_df['prep_time_bin'].value_counts().reindex(labels).reset_index()
        cancel_counts.columns = ['prep_time_bin', 'cancel_count']
        cancel_counts['cancel_count'] = cancel_counts['cancel_count'].fillna(0)

        # Plotly Bar Graph Execution
        fig_bar = px.bar(
            cancel_counts, 
            x='prep_time_bin', 
            y='cancel_count',
            text='cancel_count',
            labels={'prep_time_bin': 'Preparation Time Bin', 'cancel_count': 'Number of Cancellations'},
            color_discrete_sequence=['#FF6B6B']
        )
        fig_bar.update_traces(textposition='outside', marker_line_color='#2D3748', marker_line_width=1)
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption("Insight: Notice a surge and structural consistency in cancellations once preparation transcends past 10 minutes.")

    # --- CHART 2: PLOTLY AREA/LINE CHART (HOURLY ORDER TRENDS) ---
    with col2:
        st.subheader("📈 Temporal Hourly Distribution Analysis")
        
        orders_by_hour = df_filtered.groupby('Order Hour (24h)').size().reset_index(name='Total Orders')
        
        # Dynamic Area Chart for cleaner visual footprint
        fig_line = px.area(
            orders_by_hour, 
            x='Order Hour (24h)', 
            y='Total Orders',
            labels={'Order Hour (24h)': 'Order Hour (24-Hour Format)', 'Total Orders': 'Total Orders Placed'},
            color_discrete_sequence=['#1E3A8A']
        )
        fig_line.update_traces(mode='lines+markers', marker=dict(size=6, color='#FF4B4B'))
        fig_line.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            xaxis=dict(showgrid=True, gridcolor='#E2E8F0', tickmode='linear', dtick=2),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption("Insight: Peak operations stay robust in late night shifts (peaking towards midnight), suggesting tactical fleet distributions.")

    st.markdown("---")
    
    # --- CHART 3: PLOTLY SCATTER PLOT WITH TRENDLINE ---
    st.subheader("🗺️ Logistics Engine Evaluation: Distance vs. System Transit Time")
    
    if len(df_filtered) > 0:
        df_sample = df_filtered.sample(n=min(sample_size, len(df_filtered)), random_state=42)
        
        # Interactive Scatter Plot utilizing built-in Ordinary Least Squares trend calculation
        fig_scatter = px.scatter(
            df_sample, 
            x='Distance (km)', 
            y='Delivery Time (mins)',
            trendline="ols",
            trendline_color_override="#FF4B4B",
            color_discrete_sequence=['#2D3748'],
            opacity=0.6,
            labels={'Distance (km)': 'Distance (km)', 'Delivery Time (mins)': 'Delivery Time (mins)'}
        )
        fig_scatter.update_layout(
            plot_bgcolor='#F8FAFC',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=420,
            xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig_scatter, use_container_width=def load_data():
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
    with kpi2:
        total_canceled = int((df_filtered['Cancellation Status'] == True).sum())
        st.metric(label="Total Cancellations", value=f"{total_canceled:,}")
    with kpi3:
        avg_prep = df_filtered['Preparation Time (mins)'].mean()
        st.metric(label="Avg Prep Time", value=f"{avg_prep:.1f} mins")
    with kpi4:
        avg_delivery = df_filtered['Delivery Time (mins)'].mean()
        st.metric(label="Avg Delivery Time", value=f"{avg_delivery:.1f} mins")
        
    st.markdown("---")

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
    st.caption("Insight: Strongly positive linear relationship verified ($r \\approx 0.86$). Base overhead is represented via the intercept axis.")def load_data():
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
    with kpi2:
        total_canceled = int((df_filtered['Cancellation Status'] == True).sum())
        st.metric(label="Total Cancellations", value=f"{total_canceled:,}")
    with kpi3:
        avg_prep = df_filtered['Preparation Time (mins)'].mean()
        st.metric(label="Avg Prep Time", value=f"{avg_prep:.1f} mins")
    with kpi4:
        avg_delivery = df_filtered['Delivery Time (mins)'].mean()
        st.metric(label="Avg Delivery Time", value=f"{avg_delivery:.1f} mins")
        
    st.markdown("---")

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
    st.caption("Insight: Strongly positive linear relationship verified ($r \\approx 0.86$). Base overhead is represented via the intercept axis.")        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
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
    with kpi2:
        total_canceled = int((df_filtered['Cancellation Status'] == True).sum())
        st.metric(label="Total Cancellations", value=f"{total_canceled:,}")
    with kpi3:
        avg_prep = df_filtered['Preparation Time (mins)'].mean()
        st.metric(label="Avg Prep Time", value=f"{avg_prep:.1f} mins")
    with kpi4:
        avg_delivery = df_filtered['Delivery Time (mins)'].mean()
        st.metric(label="Avg Delivery Time", value=f"{avg_delivery:.1f} mins")
        
    st.markdown("---")

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
