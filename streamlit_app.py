
"""
Streamlit UI for Carbon Footprint Analysis
Upload bank statements and get detailed carbon footprint insights with min/max ranges
Shows rule-based vs LLM categorization efficiency
"""

import streamlit as st
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import tempfile
import os
from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload

from orchestrator import run_carbon_analysis
from utils.reporting import generate_report
from utils.patterns import EMISSION_FACTORS

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
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
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
        trees_needed = result['total_carbon_kg_avg'] / 21  # ~21kg CO2 per tree per year
        st.metric(
            label="Trees to Offset (yearly)",
            value=f"{trees_needed:.1f} trees"
        )
    
    # Range explanation
    st.info("📊 **Why the range?** Carbon emissions vary based on diet (veg/non-veg), energy sources (coal/renewable), vehicle efficiency, and product origins (local/imported).")
    
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
        for est in result['carbon_estimates']:
            # Handle both nested and flat transaction structures
            if 'transaction' in est and isinstance(est['transaction'], dict) and 'transaction' in est['transaction']:
                txn = est['transaction']['transaction']
                category = est['transaction']['category']
                method = est['transaction'].get('categorization_method', 'unknown')
            else:
                # Flat structure - transaction fields directly in estimate
                txn = est
                category = est.get('category', 'unknown')
                method = est.get('categorization_method', 'unknown')
            
            txn_data.append({
                'Date': txn.get('date', ''),
                'Description': txn.get('description', ''),
                'Amount': f"₹{txn.get('amount', 0):,.0f}",
                'Type': txn.get('type', '').title(),
                'Category': category.replace('_', ' ').title(),
                'Method': method.replace('_', ' ').title(),
                'CO2 Min': f"{est.get('carbon_kg_min', 0):.3f}",
                'CO2 Max': f"{est.get('carbon_kg_max', 0):.3f}",
                'CO2 Avg': f"{est.get('carbon_kg_avg', 0):.3f}"
            })
        
        df_txn = pd.DataFrame(txn_data)
        st.dataframe(df_txn, use_container_width=True, hide_index=True)
    
    # Download options
    st.markdown("---")
    st.subheader("📥 Download Results")
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        # Download as JSON
        json_result = {
            "total_carbon_kg_min": result["total_carbon_kg_min"],
            "total_carbon_kg_max": result["total_carbon_kg_max"],
            "total_carbon_kg_avg": result["total_carbon_kg_avg"],
            "rule_based_count": result.get("rule_based_count", 0),
            "llm_based_count": result.get("llm_based_count", 0),
            "category_breakdown": result["category_breakdown"],
            "monthly_breakdown": result["monthly_breakdown"],
            "insights": result["insights"],
            "recommendations": result["recommendations"]
        }
        st.download_button(
            label="📄 Download JSON Report",
            data=json.dumps(json_result, indent=2),
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
    
    | Category | Emission Factor (kg CO2e/₹1000) |
    |----------|--------------------------------|
    | 🚗 Transport | 20 - 40 |
    | 🏠 Housing & Utilities | 10 - 20 |
    | 🍽️ Food & Groceries | 7 - 15 |
    | 🛒 Household Appliances | 5 - 10 |
    | 👕 Clothing & Footwear | 5 - 10 |
    | 🎭 Recreation & Leisure | 2 - 8 |
    | 🏥 Healthcare | 3 - 7 |
    | 📱 Education & Communication | 1 - 5 |
    | 💰 Financial Services | 1 - 3 |
    
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







