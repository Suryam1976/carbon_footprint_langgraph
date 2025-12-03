"""Node 8: Enhanced Insights and Recommendations Generation"""

from langchain_core.messages import AIMessage
from core.state import GraphState
from core.llm_factory import get_llm
from langchain_core.prompts import ChatPromptTemplate


def generate_insights_node(state: GraphState) -> GraphState:
    """
    Node 8: Generate specific, data-driven insights and recommendations
    with benchmark comparisons and actionable advice
    """
    
    # Extract key metrics
    total_carbon = state.get("total_carbon_kg_avg", 0)
    category_breakdown = state.get("category_breakdown", {})
    transactions = state.get("carbon_estimates", [])
    high_value_count = state.get("high_value_count", 0)
    
    # Analyze spending patterns
    insights_data = analyze_spending_patterns(
        total_carbon,
        category_breakdown,
        transactions,
        high_value_count
    )
    
    # Try LLM-based generation first
    try:
        llm = get_llm(
            provider=state.get("llm_provider", "groq"),
            model=state.get("llm_model", "llama-3.3-70b-versatile"),
            temperature=0.3,
            max_tokens=2000
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a carbon footprint analyst providing specific, actionable insights.

CRITICAL RULES:
1. Use EXACT numbers from the data provided
2. Compare to benchmarks and explain what they mean
3. Provide SPECIFIC recommendations with expected impact
4. Be HONEST - if emissions are high, say so clearly
5. NEVER contradict yourself (e.g., don't say "low" when data shows "high")
6. Focus on highest-impact categories first
7. Every recommendation must include: action + category + expected reduction + difficulty

Generate 3-5 insights and 3-5 recommendations.

Insight Format:
- Start with the finding (with exact numbers)
- Explain what it means
- Show comparison to benchmark

Recommendation Format:
- **Category Name** (current CO2): Specific action. Expected reduction: X kg CO2e/month. Difficulty: Easy/Medium/Hard

Benchmarks for Urban India (monthly):
- Average household: 200-250 kg CO2e
- Low footprint: <150 kg CO2e  
- High footprint: >300 kg CO2e

Category-wise red flags:
- Transport >100 kg: High emissions
- Food >60 kg: Consider diet changes
- Shopping >40 kg: Overconsumption"""),
            ("human", """Analyze this carbon footprint data:

SUMMARY:
- Total Carbon: {total_carbon:.1f} kg CO2e
- Period: Monthly
- Benchmark: Urban India average is 200-250 kg/month

TOP CATEGORIES:
{category_summary}

SPENDING PATTERNS:
{pattern_analysis}

HIGH-VALUE TRANSACTIONS:
- Count: {high_value_count}
{high_value_note}

Generate specific insights and actionable recommendations based on this data.
Be honest about the footprint level - use exact numbers in comparisons.""")
        ])
        
        chain = prompt | llm
        
        high_value_note = "- These may need activity-based calculation for accuracy" if high_value_count > 0 else "- None detected"
        
        result = chain.invoke({
            "total_carbon": total_carbon,
            "category_summary": insights_data["category_summary"],
            "pattern_analysis": insights_data["pattern_analysis"],
            "high_value_count": high_value_count,
            "high_value_note": high_value_note
        })
        
        response_text = result.content if hasattr(result, 'content') else str(result)
        insights, recommendations = parse_llm_response(response_text)
        
    except Exception as e:
        print(f"LLM insights generation failed: {e}")
        insights, recommendations = [], []
    
    # Fallback to rule-based if LLM fails or returns empty
    if not insights or len(insights) < 2:
        insights = generate_rule_based_insights(insights_data)
    
    if not recommendations or len(recommendations) < 2:
        recommendations = generate_rule_based_recommendations(insights_data)
    
    state["insights"] = insights
    state["recommendations"] = recommendations
    
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"✅ Generated {len(insights)} insights and {len(recommendations)} recommendations"),
        AIMessage(content="🎯 Analysis complete! Check your personalized carbon footprint report.")
    ]
    
    return state


def analyze_spending_patterns(total_carbon, category_breakdown, transactions, high_value_count):
    """Analyze spending patterns and calculate insights data"""
    
    # Sort categories by carbon impact
    sorted_categories = sorted(
        category_breakdown.items(),
        key=lambda x: x[1].get('total_co2_kg_avg', 0),
        reverse=True
    )
    
    # Top 3 categories
    top_3 = sorted_categories[:3]
    
    # Category summary with details
    category_lines = []
    for i, (cat, data) in enumerate(top_3, 1):
        cat_name = cat.replace('_', ' ').title()
        co2 = data.get('total_co2_kg_avg', 0)
        spend = data.get('total_spend', 0)
        txn_count = data.get('count', 0)
        
        category_lines.append(
            f"{i}. {cat_name}: {co2:.1f} kg CO2e (₹{spend:,.0f} spent, {txn_count} transactions)"
        )
    
    category_summary = "\n".join(category_lines) if category_lines else "No significant categories"
    
    # Pattern analysis with specific benchmarks
    patterns = []
    
    # Overall assessment - BE HONEST
    if total_carbon > 300:
        patterns.append(f"⚠️ Total {total_carbon:.1f} kg is SIGNIFICANTLY ABOVE AVERAGE (benchmark: 200-250 kg)")
    elif total_carbon > 250:
        patterns.append(f"⚠️ Total {total_carbon:.1f} kg is ABOVE AVERAGE (benchmark: 200-250 kg)")
    elif total_carbon >= 200:
        patterns.append(f"📊 Total {total_carbon:.1f} kg is WITHIN AVERAGE RANGE (benchmark: 200-250 kg)")
    elif total_carbon >= 150:
        patterns.append(f"✅ Total {total_carbon:.1f} kg is BELOW AVERAGE (benchmark: 200-250 kg)")
    else:
        patterns.append(f"✅ Total {total_carbon:.1f} kg is WELL BELOW AVERAGE - Great job! (benchmark: 200-250 kg)")
    
    # Check for high transport emissions
    transport_co2 = category_breakdown.get('transport', {}).get('total_co2_kg_avg', 0)
    if transport_co2 > 100:
        patterns.append(f"⚠️ Transport emissions are VERY HIGH at {transport_co2:.1f} kg (benchmark: <100 kg)")
    elif transport_co2 > 50:
        patterns.append(f"⚠️ Transport emissions are MODERATE-HIGH at {transport_co2:.1f} kg (benchmark: <100 kg)")
    elif transport_co2 > 0:
        patterns.append(f"✅ Transport emissions are LOW at {transport_co2:.1f} kg (benchmark: <100 kg)")
    
    # Check for high food emissions
    food_co2 = category_breakdown.get('food_and_groceries', {}).get('total_co2_kg_avg', 0)
    if food_co2 > 60:
        patterns.append(f"⚠️ Food emissions are HIGH at {food_co2:.1f} kg (benchmark: <60 kg)")
    elif food_co2 > 40:
        patterns.append(f"📊 Food emissions are MODERATE at {food_co2:.1f} kg (benchmark: <60 kg)")
    elif food_co2 > 0:
        patterns.append(f"✅ Food emissions are LOW at {food_co2:.1f} kg (benchmark: <60 kg)")
    
    # Check for shopping patterns
    shopping_cats = ['household_goods_and_appliances', 'clothing_and_footwear']
    shopping_co2 = sum(
        category_breakdown.get(cat, {}).get('total_co2_kg_avg', 0)
        for cat in shopping_cats
    )
    if shopping_co2 > 40:
        patterns.append(f"⚠️ Shopping emissions are HIGH at {shopping_co2:.1f} kg (benchmark: <40 kg)")
    elif shopping_co2 > 20:
        patterns.append(f"📊 Shopping emissions are MODERATE at {shopping_co2:.1f} kg")
    
    pattern_analysis = "\n".join(patterns) if patterns else "No significant patterns detected"
    
    return {
        "category_summary": category_summary,
        "pattern_analysis": pattern_analysis,
        "top_categories": top_3,
        "total_carbon": total_carbon,
        "transport_co2": transport_co2,
        "food_co2": food_co2,
        "shopping_co2": shopping_co2
    }


def parse_llm_response(response_text):
    """Parse insights and recommendations from LLM response"""
    
    insights = []
    recommendations = []
    
    lines = response_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect sections
        line_lower = line.lower()
        if 'insight' in line_lower and ':' in line:
            current_section = 'insights'
            continue
        elif 'recommendation' in line_lower and ':' in line:
            current_section = 'recommendations'
            continue
        
        # Parse content lines
        if line.startswith(('-', '•', '*', '✓', '⚠️', '📊', '✅')):
            item = line.lstrip('-•*✓⚠️📊✅ ').strip()
            if item:
                if current_section == 'insights':
                    insights.append(item)
                elif current_section == 'recommendations':
                    recommendations.append(item)
        # Parse numbered items
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            item = line[2:].strip()
            if item:
                if current_section == 'insights':
                    insights.append(item)
                elif current_section == 'recommendations':
                    recommendations.append(item)
    
    return insights, recommendations


def generate_rule_based_insights(insights_data):
    """Generate rule-based insights using actual data"""
    
    insights = []
    total_carbon = insights_data["total_carbon"]
    top_categories = insights_data["top_categories"]
    
    # Overall assessment - BE HONEST
    if total_carbon > 300:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is significantly above the urban India "
            f"average of 200-250 kg/month. This equals approximately {total_carbon/21:.0f} trees needed to offset annually."
        )
    elif total_carbon > 250:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is above the urban India average of 200-250 kg/month. "
            f"Small changes in high-impact areas can bring you to the average range."
        )
    elif total_carbon >= 200:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is within the urban India average range of 200-250 kg/month."
        )
    elif total_carbon >= 150:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is below the urban India average of 200-250 kg/month. "
            f"Great job maintaining sustainable spending patterns!"
        )
    else:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is well below the urban India average of 200-250 kg/month. "
            f"Excellent work maintaining a low carbon lifestyle!"
        )
    
    # Top category insights
    if top_categories:
        top_cat, top_data = top_categories[0]
        cat_name = top_cat.replace('_', ' ').title()
        cat_co2 = top_data.get('total_co2_kg_avg', 0)
        cat_percent = (cat_co2 / total_carbon * 100) if total_carbon > 0 else 0
        
        insights.append(
            f"{cat_name} is your highest emission category at {cat_co2:.1f} kg CO2e ({cat_percent:.0f}% of total). "
            f"This represents your primary opportunity for reduction."
        )
    
    # Second category
    if len(top_categories) > 1:
        cat, data = top_categories[1]
        cat_name = cat.replace('_', ' ').title()
        cat_co2 = data.get('total_co2_kg_avg', 0)
        cat_percent = (cat_co2 / total_carbon * 100) if total_carbon > 0 else 0
        
        insights.append(
            f"{cat_name} is your second-highest category at {cat_co2:.1f} kg CO2e ({cat_percent:.0f}% of total)."
        )
    
    # Specific warnings based on benchmarks
    transport_co2 = insights_data.get("transport_co2", 0)
    if transport_co2 > 100:
        insights.append(
            f"⚠️ Your transport emissions of {transport_co2:.1f} kg are significantly above the recommended "
            f"<100 kg benchmark. This is a critical area for reduction."
        )
    
    food_co2 = insights_data.get("food_co2", 0)
    if food_co2 > 60:
        insights.append(
            f"⚠️ Your food emissions of {food_co2:.1f} kg exceed the recommended <60 kg benchmark. "
            f"Diet changes can have significant impact."
        )
    
    return insights[:5]  # Limit to 5 insights


def generate_rule_based_recommendations(insights_data):
    """Generate specific, actionable recommendations based on actual data"""
    
    recommendations = []
    top_categories = insights_data["top_categories"]
    total_carbon = insights_data["total_carbon"]
    
    # Category-specific recommendations with expected impact
    for cat, data in top_categories[:3]:
        cat_co2 = data.get('total_co2_kg_avg', 0)
        cat_name = cat.replace('_', ' ').title()
        
        if cat == 'transport' and cat_co2 > 50:
            if cat_co2 > 100:
                recommendations.append(
                    f"**Transport** ({cat_co2:.0f} kg): Switch to public transport or carpooling 3-4 days/week. "
                    f"Expected reduction: 30-50 kg CO2e/month. Difficulty: Easy-Medium"
                )
            else:
                recommendations.append(
                    f"**Transport** ({cat_co2:.0f} kg): Use metro/bus 2-3 days/week instead of ride-sharing. "
                    f"Expected reduction: 15-25 kg CO2e/month. Difficulty: Easy"
                )
        
        elif cat == 'food_and_groceries' and cat_co2 > 30:
            if cat_co2 > 60:
                recommendations.append(
                    f"**Food & Groceries** ({cat_co2:.0f} kg): Reduce meat by 50% and choose local/seasonal produce. "
                    f"Expected reduction: 15-25 kg CO2e/month. Difficulty: Medium"
                )
            else:
                recommendations.append(
                    f"**Food & Groceries** ({cat_co2:.0f} kg): Plan meals to reduce food delivery by 30%. "
                    f"Expected reduction: 8-12 kg CO2e/month. Difficulty: Easy"
                )
        
        elif cat == 'household_goods_and_appliances' and cat_co2 > 15:
            recommendations.append(
                f"**Shopping** ({cat_co2:.0f} kg): Delay non-essential purchases and buy refurbished electronics. "
                f"Expected reduction: 5-10 kg CO2e/month. Difficulty: Easy"
            )
        
        elif cat == 'recreation_and_leisure' and cat_co2 > 15:
            recommendations.append(
                f"**Entertainment** ({cat_co2:.0f} kg): Choose local activities and reduce long-distance travel. "
                f"Expected reduction: 10-20 kg CO2e/month. Difficulty: Medium"
            )
        
        elif cat == 'housing_and_utilities' and cat_co2 > 15:
            recommendations.append(
                f"**Housing & Utilities** ({cat_co2:.0f} kg): Switch to LED bulbs and optimize AC usage. "
                f"Expected reduction: 5-8 kg CO2e/month. Difficulty: Easy"
            )
    
    # General tracking recommendation
    if total_carbon > 200:
        recommendations.append(
            f"**Track Progress**: Analyze your statement monthly to measure improvement. "
            f"Target: Reduce by 10-15% in 3 months ({total_carbon*0.1:.0f}-{total_carbon*0.15:.0f} kg reduction). Difficulty: Easy"
        )
    else:
        recommendations.append(
            f"**Maintain Habits**: Continue tracking monthly to stay within sustainable range. "
            f"Target: Keep below 150 kg CO2e/month. Difficulty: Easy"
        )
    
    return recommendations[:5]  # Limit to 5 recommendations
