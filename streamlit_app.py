
"""
Streamlit UI for Carbon Footprint Analysis
Upload bank statements and get detailed carbon footprint insights with min/max ranges
Shows rule-based vs LLM categorization efficiency
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from core.benchmarks import KG_CO2_PER_TREE_PER_YEAR, WEEKLY_PER_CAPITA_CO2E_KG
from core.exceptions import TransactionExtractionError
from core.logging_config import configure_logging
from orchestrator import run_carbon_analysis
from utils.patterns import EMISSION_FACTORS, get_category_display_name
from utils.reporting import generate_report, generate_csv_data, generate_json_report

load_dotenv(override=True)  # Force reload

# Initialize logging
configure_logging()

# Page config
st.set_page_config(
    page_title="Carbon Footprint Analyzer",
    page_icon="🌱",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .insight-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .recommendation-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .range-indicator {
        font-size: 0.8rem;
        color: #666;
    }
    .efficiency-box {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🌱 Carbon Footprint Analyzer</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

# LLM Provider Selection
llm_provider = st.sidebar.selectbox(
    "🤖 LLM Provider",
    options=["anthropic", "groq"],
    index=0,
    help="Choose between Anthropic Claude or Groq models"
)

# Model Selection based on provider
if llm_provider == "anthropic":
    llm_model = st.sidebar.selectbox(
        "🧠 Model",
        options=[
            "claude-3-5-sonnet-20241022",
            "claude-3-haiku-20240307",
            "claude-3-opus-20240229"
        ],
        index=0,
        help="Claude models - Sonnet is recommended for best balance"
    )
elif llm_provider == "groq":
    llm_model = st.sidebar.selectbox(
        "🧠 Model", 
        options=[
            "llama-3.3-70b-versatile",      # NEW: Latest Llama 3.3
            "llama-3.1-70b-versatile",      # Current best
            "llama-3.1-8b-instant",         # Fast option
            "llama-3.2-90b-text-preview",   # NEW: Larger model
            "llama-3.2-11b-text-preview",   # NEW: Mid-size
            "llama-3.2-3b-preview",         # NEW: Smallest
            "mixtral-8x7b-32768",           # Mixtral (still good)
            "gemma2-9b-it",                 # Gemma (efficient)
            "llama-guard-3-8b",             # NEW: Safety model
        ],
        index=0,
        help="Latest Groq models - Llama 3.3 70B is recommended for best performance"
    )

# Show API key requirements
if llm_provider == "anthropic":
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.sidebar.error("⚠️ ANTHROPIC_API_KEY not found in environment")
elif llm_provider == "groq":
    if not os.getenv("GROQ_API_KEY"):
        st.sidebar.error("⚠️ GROQ_API_KEY not found in environment")

st.sidebar.markdown("---")

# File upload section
st.sidebar.header("📄 Upload Bank Statement")
uploaded_file = st.sidebar.file_uploader(
    "Choose PDF file", 
    type=['pdf'],
    help="Upload your bank statement PDF"
)

# Password input for encrypted PDFs
pdf_password = None
if uploaded_file:
    st.sidebar.success(f"✅ File uploaded: {uploaded_file.name}")
    pdf_password = st.sidebar.text_input(
        "PDF Password (if required)", 
        type="password",
        help="Leave empty if PDF is not password-protected"
    )
    use_sample = st.sidebar.checkbox("Use sample data instead", value=False)
else:
    use_sample = st.sidebar.checkbox("Use sample data for demo", value=True)

analyze_button = st.sidebar.button("🔍 Analyze Carbon Footprint", type="primary")

# Main content
if analyze_button:
    # Check API key
    if llm_provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        st.error("❌ Please set ANTHROPIC_API_KEY in your .env file")
        st.stop()
    elif llm_provider == "groq" and not os.getenv("GROQ_API_KEY"):
        st.error("❌ Please set GROQ_API_KEY in your .env file")
        st.stop()
    
    with st.spinner(f"Analyzing using {llm_provider.title()} {llm_model}..."):
        try:
            if use_sample:
                st.info(f"📋 Using sample data with {llm_provider.title()} {llm_model}")
                result = run_carbon_analysis(
                    llm_provider=llm_provider,
                    llm_model=llm_model
                )
            else:
                if uploaded_file:
                    # Save uploaded file temporarily
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    st.info(f"📄 Analyzing {uploaded_file.name} with {llm_provider.title()} {llm_model}")
                    result = run_carbon_analysis(
                        pdf_path=temp_path,
                        password=pdf_password,
                        llm_provider=llm_provider,
                        llm_model=llm_model
                    )

                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                else:
                    st.warning("Please upload a PDF file or use sample data")
                    st.stop()

            # Store results
            st.session_state['analysis_result'] = result
            st.session_state['analysis_complete'] = True

        except TransactionExtractionError as e:
            st.error(
                f"❌ Could not read transactions from this PDF. {str(e)}\n\n"
                f"Try: (1) uploading a different PDF, (2) using sample data, or "
                f"(3) checking if the file is password-protected."
            )
            st.session_state['analysis_complete'] = False
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.session_state['analysis_complete'] = False

# Display results
if st.session_state.get('analysis_complete', False):
    result = st.session_state['analysis_result']

    # Show data source and any errors
    processing_status = result.get('processing_status', 'unknown')
    errors = result.get('errors', [])

    # Display errors if any
    if errors:
        with st.expander("⚠️ Processing Warnings/Errors", expanded=True):
            for error in errors:
                st.warning(error)

    # Show data source
    if processing_status in ['using_sample_data', 'fallback_to_sample', 'using_sample_transactions']:
        st.warning("📋 **Data Source:** Sample data (for demonstration)")
        if processing_status == 'fallback_to_sample':
            st.info("💡 **Tip:** Your PDF may be password-protected, scanned (image-based), or in an unsupported format. Try a text-based PDF.")
    elif processing_status in ['transactions_extracted', 'completed']:
        st.success("📄 **Data Source:** Your uploaded PDF bank statement")

    # Show transaction count breakdown
    total_txns = len(result.get('transactions', []))
    debit_txns = len(result.get('carbon_estimates', []))
    credit_txns = total_txns - debit_txns

    if total_txns > 0:
        st.info(f"📊 **Transactions:** {total_txns} total ({debit_txns} debits analyzed, {credit_txns} credits excluded)")

    # Summary metrics with min/max ranges
    st.header("📊 Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Carbon Footprint (Min)",
            value=f"{result['total_carbon_kg_min']:.2f} kg CO2e"
        )
    
    with col2:
        st.metric(
            label="Carbon Footprint (Max)",
            value=f"{result['total_carbon_kg_max']:.2f} kg CO2e"
        )
    
    with col3:
        st.metric(
            label="Average Estimate",
            value=f"{result['total_carbon_kg_avg']:.2f} kg CO2e"
        )
    
    with col4:
        # Equivalent trees needed (based on average)
        trees_needed = result['total_carbon_kg_avg'] / KG_CO2_PER_TREE_PER_YEAR
        st.metric(
            label="Trees to Offset (yearly)",
            value=f"{trees_needed:.1f} trees"
        )
    
    # Range explanation
    st.info("📊 **Why the range?** Carbon emissions vary based on diet (veg/non-veg), energy sources (coal/renewable), vehicle efficiency, and product origins (local/imported).")
    
    # High-value transaction warning
    high_value_txns = result.get('high_value_transactions', [])
    if high_value_txns:
        st.markdown("---")
    
    # Weekly Timeline Chart
    st.header("📈 Emissions Timeline (Weekly)")
    
    # Prepare timeline data from transactions
    timeline_data = []
    for est in result['carbon_estimates']:
        # Flat transaction structure (all fields at top level)
        date_str = est.get('date', '')
        category = est.get('category', 'miscellaneous')
        try:
            # Try multiple date formats
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y', '%Y-%m-%d']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    break
                except:
                    continue
            else:
                continue  # Skip if date parsing fails
            
            timeline_data.append({
                'Date': date_obj,
                'Category': category.replace('_', ' ').title(),
                'CO2_Min': est.get('carbon_kg_min', 0),
                'CO2_Max': est.get('carbon_kg_max', 0),
                'CO2_Avg': est.get('carbon_kg_avg', 0)
            })
        except:
            pass  # Skip transactions with invalid dates
    
    if timeline_data:
        df_timeline = pd.DataFrame(timeline_data)
        df_timeline = df_timeline.sort_values('Date')
        
        # Group by week
        df_timeline['Week'] = df_timeline['Date'].dt.to_period('W').apply(lambda r: r.start_time)
        
        # Aggregate by week
        weekly_totals = df_timeline.groupby('Week').agg({
            'CO2_Min': 'sum',
            'CO2_Max': 'sum',
            'CO2_Avg': 'sum'
        }).reset_index()
        
        # Also get category-wise weekly data for stacked view
        weekly_by_category = df_timeline.groupby(['Week', 'Category'])['CO2_Avg'].sum().reset_index()
        
        # Create tabs for different views
        tab1, tab2 = st.tabs(["Total Emissions", "By Category"])
        
        with tab1:
            # Line chart with min/max range
            fig_timeline = go.Figure()
            
            # Add min/max range as filled area
            fig_timeline.add_trace(go.Scatter(
                x=weekly_totals['Week'],
                y=weekly_totals['CO2_Max'],
                mode='lines',
                name='Max',
                line=dict(width=0),
                showlegend=False,
                hovertemplate='Max: %{y:.2f} kg CO2e<extra></extra>'
            ))
            
            fig_timeline.add_trace(go.Scatter(
                x=weekly_totals['Week'],
                y=weekly_totals['CO2_Min'],
                mode='lines',
                name='Min',
                fill='tonexty',
                fillcolor='rgba(76, 175, 80, 0.2)',
                line=dict(width=0),
                showlegend=False,
                hovertemplate='Min: %{y:.2f} kg CO2e<extra></extra>'
            ))
            
            # Add average line
            fig_timeline.add_trace(go.Scatter(
                x=weekly_totals['Week'],
                y=weekly_totals['CO2_Avg'],
                mode='lines+markers',
                name='Your Average',
                line=dict(color='#2E7D32', width=3),
                marker=dict(size=8, color='#2E7D32'),
                hovertemplate='Week: %{x|%d %b %Y}<br>Your CO2: %{y:.2f} kg<extra></extra>'
            ))
            
            # Add reference line for average urban Indian (weekly)
            urban_avg_weekly = WEEKLY_PER_CAPITA_CO2E_KG
            fig_timeline.add_hline(
                y=urban_avg_weekly,
                line_dash="dot",
                line_color="#FF6B35",
                line_width=2,
                annotation_text=f"Urban India Average (~{urban_avg_weekly:.1f} kg/week)",
                annotation_position="top right",
                annotation=dict(
                    font=dict(size=12, color="#FF6B35"),
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="#FF6B35",
                    borderwidth=1
                )
            )
            
            fig_timeline.update_layout(
                title='Weekly Carbon Emissions Trend vs Urban India Average',
                xaxis_title='Week',
                yaxis_title='CO2 Emissions (kg)',
                hovermode='x unified',
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Show summary stats with comparison
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            with col_t1:
                user_avg = weekly_totals['CO2_Avg'].mean()
                st.metric("Your Avg/Week", f"{user_avg:.2f} kg")
            with col_t2:
                comparison = "Above" if user_avg > urban_avg_weekly else "Below"
                diff = abs(user_avg - urban_avg_weekly)
                st.metric("vs Urban India", f"{comparison}", f"{diff:.1f} kg difference")
            with col_t3:
                st.metric("Highest Week", f"{weekly_totals['CO2_Avg'].max():.2f} kg")
            with col_t4:
                trend = "Increasing" if weekly_totals['CO2_Avg'].iloc[-1] > weekly_totals['CO2_Avg'].iloc[0] else "Decreasing"
                st.metric("Trend", trend)
            
            # Add context explanation
            st.info(f"""
            📊 **Reference Context**: The dotted orange line shows the average weekly carbon footprint for urban Indians (~{WEEKLY_PER_CAPITA_CO2E_KG:.1f} kg CO2e/week, based on spend-based spending patterns).

            **Note**: This analysis measures spend-based emissions from your digital transactions only. It excludes cash spending, owned-vehicle fuel not paid by card, home energy not billed digitally, etc. Comparisons are directional/approximate.

            **Sources**: ScienceDirect "Scale and drivers of carbon footprints in households, cities and regions across India" (urban per-capita ~2,330 kg CO2e/year); ISEC Policy Brief on household footprints.
            """)
        
        with tab2:
            # Stacked area chart by category
            fig_stacked = go.Figure()
            
            # Get unique categories
            categories = weekly_by_category['Category'].unique()
            colors = px.colors.qualitative.Set2
            
            for i, category in enumerate(categories):
                cat_data = weekly_by_category[weekly_by_category['Category'] == category]
                fig_stacked.add_trace(go.Scatter(
                    x=cat_data['Week'],
                    y=cat_data['CO2_Avg'],
                    name=category,
                    mode='lines',
                    stackgroup='one',
                    fillcolor=colors[i % len(colors)],
                    hovertemplate='%{fullData.name}<br>CO2: %{y:.2f} kg<extra></extra>'
                ))
            
            fig_stacked.update_layout(
                title='Weekly Emissions by Category (Stacked)',
                xaxis_title='Week',
                yaxis_title='CO2 Emissions (kg)',
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_stacked, use_container_width=True)
    else:
        st.info("No date information available for timeline chart")
    
    st.markdown("---")
    
    # High-value transaction warning (display after timeline)
    if high_value_txns:
        st.warning(f"""⚠️ **High-Value Transaction Alert**
        
Found **{len(high_value_txns)} transaction(s) ≥ ₹50,000** that may skew spend-based carbon estimation.

For large purchases (electronics, vehicles, property, investments), **activity-based carbon footprint calculation** is recommended for accuracy.
""")
        
        with st.expander("📋 View High-Value Transactions", expanded=True):
            hv_data = []
            for txn in high_value_txns:
                hv_data.append({
                    'Description': txn.get('description', ''),
                    'Amount': f"₹{txn.get('amount', 0):,.0f}",
                    'Category': 'Not Categorized',  # Fixed: Don't access txn['category']
                    'Estimated CO2 (kg)': 'N/A - Use Activity-Based',
                    'Recommendation': 'Use activity-based estimation'
                })
            
            df_hv = pd.DataFrame(hv_data)
            st.dataframe(df_hv, use_container_width=True, hide_index=True)
            
            st.markdown("""
**Why activity-based estimation?**
- A ₹50,000 laptop has a specific manufacturing footprint (~300-400 kg CO2e)
- A ₹1,00,000 flight has emissions based on distance, not just ticket price
- Property/vehicle purchases have lifecycle emissions unrelated to price

**Suggestion:** For accurate results, exclude these from spend-based analysis and calculate their carbon footprint separately using product-specific emission factors.
""")
    
    st.markdown("---")
    
    # Categorization Efficiency
    st.header("🏷️ Categorization Efficiency")
    
    rule_count = result.get('rule_based_count', 0)
    llm_count = result.get('llm_based_count', 0)
    total_count = rule_count + llm_count
    
    col_eff1, col_eff2, col_eff3 = st.columns(3)
    
    with col_eff1:
        st.metric(
            label="Rule-Based (Fast)",
            value=f"{rule_count} txns",
            delta=f"{(rule_count/total_count*100):.0f}% coverage" if total_count > 0 else "0%"
        )
    
    with col_eff2:
        st.metric(
            label="LLM-Based (AI)",
            value=f"{llm_count} txns",
            delta=f"Only {llm_count} needed AI" if llm_count > 0 else "None needed"
        )
    
    with col_eff3:
        st.metric(
            label="Total Processed",
            value=f"{total_count} txns"
        )
    
    # Efficiency visualization
    if total_count > 0:
        fig_efficiency = go.Figure(data=[go.Pie(
            labels=['Rule-Based', 'LLM-Based'],
            values=[rule_count, llm_count],
            hole=.4,
            marker_colors=['#4CAF50', '#FF9800']
        )])
        fig_efficiency.update_layout(
            title_text="Categorization Method Distribution",
            height=300
        )
        st.plotly_chart(fig_efficiency, use_container_width=True)
    
    st.markdown("---")
    
    # Charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🥧 Carbon by Category (Average)")
        
        # Prepare data for pie chart
        category_data = []
        for cat, data in result['category_breakdown'].items():
            if data['total_co2_kg_avg'] > 0:
                category_data.append({
                    'Category': cat.replace('_', ' ').title(),
                    'CO2 Min (kg)': data['total_co2_kg_min'],
                    'CO2 Max (kg)': data['total_co2_kg_max'],
                    'CO2 Avg (kg)': data['total_co2_kg_avg'],
                    'Spend (₹)': data['total_spend']
                })
        
        if category_data:
            df_cat = pd.DataFrame(category_data)
            fig_pie = px.pie(
                df_cat, 
                values='CO2 Avg (kg)', 
                names='Category',
                color_discrete_sequence=px.colors.sequential.Greens_r
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No carbon-emitting transactions found")
    
    with col_right:
        st.subheader("📊 Carbon Range by Category")
        
        if category_data:
            df_bar = pd.DataFrame(category_data)
            df_bar = df_bar.sort_values('CO2 Avg (kg)', ascending=True)
            
            # Create bar chart with error bars for min/max
            fig_range = go.Figure()
            
            # Add bars for average with error bars
            fig_range.add_trace(go.Bar(
                name='CO2 Emissions',
                y=df_bar['Category'],
                x=df_bar['CO2 Avg (kg)'],
                orientation='h',
                marker_color='#4CAF50',
                error_x=dict(
                    type='data',
                    symmetric=False,
                    array=df_bar['CO2 Max (kg)'] - df_bar['CO2 Avg (kg)'],
                    arrayminus=df_bar['CO2 Avg (kg)'] - df_bar['CO2 Min (kg)'],
                    color='#1B5E20'
                )
            ))
            
            fig_range.update_layout(
                height=400,
                xaxis_title="CO2 Emissions (kg)",
                showlegend=False
            )
            st.plotly_chart(fig_range, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed breakdown table
    st.subheader("📋 Category Details")
    
    table_data = []
    for cat, data in result['category_breakdown'].items():
        if data['total_co2_kg_avg'] > 0 or data['total_spend'] > 0:
            table_data.append({
                'Category': cat.replace('_', ' ').title(),
                'Transactions': data['count'],
                'Total Spend (₹)': f"₹{data['total_spend']:,.0f}",
                'CO2 Min (kg)': f"{data['total_co2_kg_min']:.2f}",
                'CO2 Max (kg)': f"{data['total_co2_kg_max']:.2f}",
                'CO2 Avg (kg)': f"{data['total_co2_kg_avg']:.2f}",
                'Factor (kg/₹1000)': f"{data['emission_factor_min']}-{data['emission_factor_max']}"
            })
    
    if table_data:
        df_table = pd.DataFrame(table_data)
        df_table = df_table.sort_values('CO2 Avg (kg)', ascending=False)
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Emission Factors Reference
    with st.expander("📚 Emission Factors Reference"):
        st.markdown("**Based on NSSO-linked studies and Indian GHG inventory research**")
        
        factors_data = []
        for cat, factors in EMISSION_FACTORS.items():
            factors_data.append({
                'Category': cat.replace('_', ' ').title(),
                'Min (kg CO2e/₹1000)': factors['min'],
                'Max (kg CO2e/₹1000)': factors['max'],
                'Notes': factors.get('notes', '')
            })
        
        df_factors = pd.DataFrame(factors_data)
        st.dataframe(df_factors, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Insights and Recommendations
    col_insights, col_recs = st.columns(2)
    
    with col_insights:
        st.subheader("💡 Key Insights")
        if result.get('insights'):
            for insight in result['insights']:
                st.markdown(f'<div class="insight-box">📌 {insight}</div>', unsafe_allow_html=True)
        else:
            st.info("Run analysis to generate insights")
    
    with col_recs:
        st.subheader("🎯 Recommendations")
        if result.get('recommendations'):
            for i, rec in enumerate(result['recommendations'], 1):
                st.markdown(f'<div class="recommendation-box">✅ {rec}</div>', unsafe_allow_html=True)
        else:
            st.info("Run analysis to get personalized recommendations")
    
    st.markdown("---")
    
    # Transaction details (expandable)
    with st.expander("📝 View All Transactions"):
        txn_data = []
        
        # Add regular transactions with carbon estimates
        for est in result['carbon_estimates']:
            # Flat transaction structure (all fields at top level)
            category = est.get('category', 'unknown')
            method = est.get('categorization_method', 'unknown')

            txn_data.append({
                'Date': est.get('date', ''),
                'Description': est.get('description', ''),
                'Amount': f"₹{est.get('amount', 0):,.0f}",
                'Type': est.get('type', '').title(),
                'Category': category.replace('_', ' ').title(),
                'Method': method.replace('_', ' ').title(),
                'CO2 Min': f"{est.get('carbon_kg_min', 0):.3f}",
                'CO2 Max': f"{est.get('carbon_kg_max', 0):.3f}",
                'CO2 Avg': f"{est.get('carbon_kg_avg', 0):.3f}"
            })
        
        # Add high-value transactions (excluded from carbon analysis)
        for hv_txn in result.get('high_value_transactions', []):
            txn_data.append({
                'Date': hv_txn.get('date', ''),
                'Description': hv_txn.get('description', ''),
                'Amount': f"₹{hv_txn.get('amount', 0):,.0f}",
                'Type': 'Debit',
                'Category': '⚠️ High-Value (Excluded)',
                'Method': 'Not Categorized',
                'CO2 Min': 'N/A',
                'CO2 Max': 'N/A',
                'CO2 Avg': 'N/A'
            })
        
        df_txn = pd.DataFrame(txn_data)
        st.dataframe(df_txn, use_container_width=True, hide_index=True)
    
    # Download options
    st.markdown("---")
    st.subheader("📥 Download Results")

    col_dl1, col_dl2, col_dl3 = st.columns(3)

    with col_dl1:
        # Download as JSON
        json_report_data = generate_json_report(result)
        st.download_button(
            label="📄 Download JSON Report",
            data=json_report_data,
            file_name="carbon_footprint_report.json",
            mime="application/json"
        )

    with col_dl2:
        # Download as text report
        text_report = generate_report(result)
        st.download_button(
            label="📝 Download Text Report",
            data=text_report,
            file_name="carbon_footprint_report.txt",
            mime="text/plain"
        )

    with col_dl3:
        # Download as CSV (transaction-level export)
        csv_data = generate_csv_data(result)
        st.download_button(
            label="📊 Download CSV (Transactions)",
            data=csv_data,
            file_name="carbon_footprint_transactions.csv",
            mime="text/csv"
        )

else:
    # Welcome message
    st.markdown("""
    ## Welcome to the Carbon Footprint Analyzer! 🌍
    
    This tool analyzes your Indian bank statement to estimate your carbon footprint based on spending patterns.
    
    ### How it works:
    
    1. **Upload** your bank statement PDF (or use sample data)
    2. **AI Extraction** structures your transactions
    3. **Rule-Based Categorization** - Fast pattern matching for known merchants
    4. **LLM Categorization** - AI handles uncertain transactions only
    5. **Carbon Calculation** estimates CO2 emissions with min/max ranges
    6. **Insights & Recommendations** help you reduce your footprint
    
    ### Categorization Approach:
    
    | Method | Speed | Usage |
    |--------|-------|-------|
    | 🚀 Rule-Based | Fast | Known merchants (Swiggy, IOCL, Netflix, etc.) |
    | 🤖 LLM-Based | Slower | Uncertain/new merchants |
    
    This hybrid approach is **faster** and **more cost-effective** than pure LLM!
    
    ### Categories Analyzed (with emission factors):

    """
    )

    # Generate emission factor table dynamically from patterns.py
    table_lines = ["| Category | Emission Factor (kg CO2e/₹1000) |",
                   "|----------|--------------------------------|"]
    for category, factors in sorted(EMISSION_FACTORS.items(),
                                     key=lambda x: x[1].get("max", 0),
                                     reverse=True):
        display_name = get_category_display_name(category)
        min_factor = factors.get("min", 0)
        max_factor = factors.get("max", 0)
        table_lines.append(f"| {display_name} | {min_factor} - {max_factor} |")

    st.markdown("\n".join(table_lines))

    st.markdown("""
    
    ### Get Started
    
    Click **"Analyze Carbon Footprint"** in the sidebar to begin!
    """)
    
    # Show sample output preview
    st.markdown("---")
    st.subheader("📈 Sample Analysis Preview")
    
    # Create sample visualization with ranges
    sample_data = {
        'Category': ['Transport', 'Housing', 'Food', 'Appliances', 'Recreation', 'Healthcare'],
        'CO2 Min': [50, 28, 7.7, 16, 1.3, 1.35],
        'CO2 Max': [100, 56, 16.5, 32, 5.2, 3.15],
        'CO2 Avg': [75, 42, 12.1, 24, 3.25, 2.25]
    }
    df_sample = pd.DataFrame(sample_data)
    
    fig_sample = go.Figure()
    
    fig_sample.add_trace(go.Bar(
        name='CO2 Range',
        x=df_sample['Category'],
        y=df_sample['CO2 Avg'],
        marker_color='#4CAF50',
        error_y=dict(
            type='data',
            symmetric=False,
            array=df_sample['CO2 Max'] - df_sample['CO2 Avg'],
            arrayminus=df_sample['CO2 Avg'] - df_sample['CO2 Min'],
            color='#1B5E20'
        )
    ))
    
    fig_sample.update_layout(
        title='Sample Carbon Footprint by Category (with ranges)',
        yaxis_title='CO2 Emissions (kg)',
        showlegend=False
    )
    
    st.plotly_chart(fig_sample, use_container_width=True)
    
    st.info("**Note**: Error bars show the min-max range based on lifestyle factors like diet choice, energy sources, and product origins.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>Built with LangGraph + Claude | Emission factors from NSSO & Indian GHG studies</p>
    <p>🌱 Reduce, Reuse, Recycle 🌱</p>
</div>
""", unsafe_allow_html=True)











