"""Node 9: Enhanced Insights and Recommendations Generation

Generates data-driven insights and recommendations using LLM-based generation
with rule-based fallback. All benchmark thresholds are centralized in
utils/benchmarks.py to prevent drift.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from core.benchmarks import (
    KG_CO2_PER_TREE_PER_YEAR,
    MONTHLY_HIGH_FOOTPRINT_KG,
    MONTHLY_TYPICAL_RANGE_HIGH_KG,
    MONTHLY_TYPICAL_RANGE_LOW_KG,
)
from core.llm_factory import get_llm
from core.state import GraphState

logger = logging.getLogger(__name__)


@traceable(name="generate_insights", run_type="chain")
def generate_insights_node(state: GraphState) -> GraphState:
    """
    Node 9: Generate specific, data-driven insights and recommendations
    with benchmark comparisons and actionable advice.
    """

    # Extract key metrics
    total_carbon = state.get("total_carbon_kg_avg", 0)
    category_breakdown = state.get("category_breakdown", {})
    transactions = state.get("carbon_estimates", [])
    high_value_count = state.get("high_value_count", 0)

    # Analyze spending patterns
    insights_data = analyze_spending_patterns(
        total_carbon, category_breakdown, transactions, high_value_count
    )

    # Try LLM-based generation first
    try:
        llm = get_llm(
            provider=state.get("llm_provider", "groq"),
            model=state.get("llm_model", "llama-3.3-70b-versatile"),
            temperature=0.3,
            max_tokens=2000,
        )

        # Dynamically format the benchmark text from constants (no hardcoding drift possible)
        benchmark_text = f"""Benchmarks for Urban India (monthly):
- Average household: {MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg CO2e
- Low footprint: <{MONTHLY_TYPICAL_RANGE_LOW_KG} kg CO2e
- High footprint: >{MONTHLY_HIGH_FOOTPRINT_KG} kg CO2e

Category-wise red flags:
- Transport >100 kg: High emissions
- Food >60 kg: Consider diet changes
- Shopping >40 kg: Overconsumption"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""You are a carbon footprint analyst providing specific, actionable insights.

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

{benchmark_text}""",
                ),
                (
                    "human",
                    """Analyze this carbon footprint data:

SUMMARY:
- Total Carbon: {{total_carbon:.1f}} kg CO2e
- Period: Monthly
- Benchmark: Urban India average is {}-{} kg/month

TOP CATEGORIES:
{{category_summary}}

SPENDING PATTERNS:
{{pattern_analysis}}

HIGH-VALUE TRANSACTIONS:
- Count: {{high_value_count}}
{{high_value_note}}

Generate specific insights and actionable recommendations based on this data.
Be honest about the footprint level - use exact numbers in comparisons.""".format(
                        MONTHLY_TYPICAL_RANGE_LOW_KG, MONTHLY_TYPICAL_RANGE_HIGH_KG
                    ),
                ),
            ]
        )

        chain = prompt | llm

        high_value_note = (
            "- These may need activity-based calculation for accuracy"
            if high_value_count > 0
            else "- None detected"
        )

        result = chain.invoke(
            {
                "total_carbon": total_carbon,
                "category_summary": insights_data["category_summary"],
                "pattern_analysis": insights_data["pattern_analysis"],
                "high_value_count": high_value_count,
                "high_value_note": high_value_note,
            }
        )

        response_text = result.content if hasattr(result, "content") else str(result)
        insights, recommendations = parse_llm_response(response_text)
        logger.debug(
            "LLM insights generation: %d insights, %d recommendations",
            len(insights),
            len(recommendations),
        )

    except Exception as e:
        logger.warning("LLM insights generation failed: %s", str(e), exc_info=True)
        insights, recommendations = [], []

    # Fallback to rule-based if LLM fails or returns empty
    if not insights or len(insights) < 2:
        logger.debug("Falling back to rule-based insights generation")
        insights = generate_rule_based_insights(insights_data)

    if not recommendations or len(recommendations) < 2:
        logger.debug("Falling back to rule-based recommendations generation")
        recommendations = generate_rule_based_recommendations(insights_data)

    state["insights"] = insights
    state["recommendations"] = recommendations

    state["messages"] = state.get("messages", []) + [
        AIMessage(
            content=f"✅ Generated {len(insights)} insights and {len(recommendations)} recommendations"
        ),
        AIMessage(content="🎯 Analysis complete! Check your personalized carbon footprint report."),
    ]

    return state


def analyze_spending_patterns(total_carbon, category_breakdown, transactions, high_value_count):
    """Analyze spending patterns and calculate insights data"""

    # Sort categories by carbon impact
    sorted_categories = sorted(
        category_breakdown.items(),
        key=lambda x: x[1].get("total_co2_kg_avg", 0),
        reverse=True,
    )

    # Top 3 categories
    top_3 = sorted_categories[:3]

    # Category summary with details
    category_lines = []
    for i, (cat, data) in enumerate(top_3, 1):
        cat_name = cat.replace("_", " ").title()
        co2 = data.get("total_co2_kg_avg", 0)
        spend = data.get("total_spend", 0)
        txn_count = data.get("count", 0)

        category_lines.append(
            f"{i}. {cat_name}: {co2:.1f} kg CO2e (₹{spend:,.0f} spent, {txn_count} transactions)"
        )

    category_summary = "\n".join(category_lines) if category_lines else "No significant categories"

    # Pattern analysis with benchmark constants (centralized, no hardcoding drift)
    patterns = []

    # Overall assessment - BE HONEST
    if total_carbon > MONTHLY_HIGH_FOOTPRINT_KG:
        patterns.append(
            f"⚠️ Total {total_carbon:.1f} kg is SIGNIFICANTLY ABOVE AVERAGE "
            f"(benchmark: {MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg)"
        )
    elif total_carbon > MONTHLY_TYPICAL_RANGE_HIGH_KG:
        patterns.append(
            f"⚠️ Total {total_carbon:.1f} kg is ABOVE AVERAGE "
            f"(benchmark: {MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg)"
        )
    elif total_carbon >= MONTHLY_TYPICAL_RANGE_LOW_KG:
        patterns.append(
            f"📊 Total {total_carbon:.1f} kg is WITHIN AVERAGE RANGE "
            f"(benchmark: {MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg)"
        )
    elif total_carbon >= MONTHLY_TYPICAL_RANGE_LOW_KG * 0.75:  # e.g., 112.5 for 150
        patterns.append(
            f"✅ Total {total_carbon:.1f} kg is BELOW AVERAGE "
            f"(benchmark: {MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg)"
        )
    else:
        patterns.append(
            f"✅ Total {total_carbon:.1f} kg is WELL BELOW AVERAGE - Great job! "
            f"(benchmark: {MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg)"
        )

    # Check for high transport emissions
    transport_co2 = category_breakdown.get("transport", {}).get("total_co2_kg_avg", 0)
    if transport_co2 > 100:
        patterns.append(f"⚠️ Transport emissions are VERY HIGH at {transport_co2:.1f} kg (benchmark: <100 kg)")
    elif transport_co2 > 50:
        patterns.append(
            f"⚠️ Transport emissions are MODERATE-HIGH at {transport_co2:.1f} kg (benchmark: <100 kg)"
        )
    elif transport_co2 > 0:
        patterns.append(f"✅ Transport emissions are LOW at {transport_co2:.1f} kg (benchmark: <100 kg)")

    # Check for high food emissions
    food_co2 = category_breakdown.get("food_and_groceries", {}).get("total_co2_kg_avg", 0)
    if food_co2 > 60:
        patterns.append(f"⚠️ Food emissions are HIGH at {food_co2:.1f} kg (benchmark: <60 kg)")
    elif food_co2 > 40:
        patterns.append(f"📊 Food emissions are MODERATE at {food_co2:.1f} kg (benchmark: <60 kg)")
    elif food_co2 > 0:
        patterns.append(f"✅ Food emissions are LOW at {food_co2:.1f} kg (benchmark: <60 kg)")

    # Check for shopping patterns
    shopping_cats = ["household_goods_and_appliances", "clothing_and_footwear"]
    shopping_co2 = sum(
        category_breakdown.get(cat, {}).get("total_co2_kg_avg", 0) for cat in shopping_cats
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
        "shopping_co2": shopping_co2,
    }


def parse_llm_response(response_text):
    """Parse insights and recommendations from LLM response"""

    insights = []
    recommendations = []

    lines = response_text.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect sections
        line_lower = line.lower()
        if "insight" in line_lower and ":" in line:
            current_section = "insights"
            continue
        elif "recommendation" in line_lower and ":" in line:
            current_section = "recommendations"
            continue

        # Parse content lines (bullet points and numbered)
        if line.startswith(("-", "•", "*", "✓", "⚠️", "📊", "✅")):
            item = line.lstrip("-•*✓⚠️📊✅ ").strip()
            if item:
                if current_section == "insights":
                    insights.append(item)
                elif current_section == "recommendations":
                    recommendations.append(item)
        # Parse numbered items
        elif len(line) > 2 and line[0].isdigit() and line[1] in ".):"  :
            item = line[2:].strip()
            if item:
                if current_section == "insights":
                    insights.append(item)
                elif current_section == "recommendations":
                    recommendations.append(item)

    return insights, recommendations


def generate_rule_based_insights(insights_data):
    """Generate rule-based insights using actual data"""

    insights = []
    total_carbon = insights_data["total_carbon"]
    top_categories = insights_data["top_categories"]

    # Overall assessment - BE HONEST
    if total_carbon > MONTHLY_HIGH_FOOTPRINT_KG:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is significantly above the urban India "
            f"average of {MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg/month. "
            f"This equals approximately {total_carbon/KG_CO2_PER_TREE_PER_YEAR:.0f} trees needed to offset annually."
        )
    elif total_carbon > MONTHLY_TYPICAL_RANGE_HIGH_KG:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is above the urban India average of "
            f"{MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg/month. "
            f"Small changes can help reduce this to within average range."
        )
    elif total_carbon >= MONTHLY_TYPICAL_RANGE_LOW_KG:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is within the average range for urban India "
            f"({MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg/month). "
            f"You're on track! Focus on optimizing high-impact categories."
        )
    else:
        insights.append(
            f"Your carbon footprint of {total_carbon:.1f} kg CO2e is below the urban India average "
            f"({MONTHLY_TYPICAL_RANGE_LOW_KG}-{MONTHLY_TYPICAL_RANGE_HIGH_KG} kg/month). Excellent work!"
        )

    # Top category insight
    if top_categories:
        top_cat = top_categories[0][0].replace("_", " ").title()
        top_co2 = top_categories[0][1].get("total_co2_kg_avg", 0)
        pct = (top_co2 / total_carbon * 100) if total_carbon > 0 else 0
        insights.append(
            f"{top_cat} is your largest emission source at {top_co2:.1f} kg CO2e "
            f"({pct:.0f}% of total). Reducing spending here will have the biggest impact."
        )

    # Multi-category comparison
    if len(top_categories) >= 2:
        top_2_co2 = sum(cat[1].get("total_co2_kg_avg", 0) for cat in top_categories[:2])
        pct = (top_2_co2 / total_carbon * 100) if total_carbon > 0 else 0
        insights.append(
            f"Your top 2 categories account for {pct:.0f}% of emissions. "
            f"Targeting these will maximize reduction efforts."
        )

    return insights[:5]  # Cap at 5 insights


def generate_rule_based_recommendations(insights_data):
    """Generate rule-based recommendations using actual data"""

    recommendations = []
    category_breakdown = insights_data.get("top_categories", {})

    # Transport recommendations
    transport_co2 = insights_data.get("transport_co2", 0)
    if transport_co2 > 100:
        recommendations.append(
            "**Transport** (High): Consider carpooling, public transit, or reducing flight frequency. "
            "Expected reduction: 20-40 kg CO2e/month. Difficulty: Medium"
        )
    elif transport_co2 > 50:
        recommendations.append(
            "**Transport** (Moderate): Switch to public transport for commute or take fewer cab rides. "
            "Expected reduction: 10-20 kg CO2e/month. Difficulty: Easy"
        )

    # Food recommendations
    food_co2 = insights_data.get("food_co2", 0)
    if food_co2 > 60:
        recommendations.append(
            "**Food & Groceries** (High): Reduce meat consumption, cook at home more, "
            "avoid food delivery. Expected reduction: 15-25 kg CO2e/month. Difficulty: Medium"
        )
    elif food_co2 > 40:
        recommendations.append(
            "**Food & Groceries**: Reduce food delivery frequency by 50%. "
            "Expected reduction: 5-10 kg CO2e/month. Difficulty: Easy"
        )

    # Shopping recommendations
    shopping_co2 = insights_data.get("shopping_co2", 0)
    if shopping_co2 > 40:
        recommendations.append(
            "**Shopping** (High): Buy secondhand when possible, reduce impulse purchases. "
            "Expected reduction: 10-20 kg CO2e/month. Difficulty: Easy"
        )

    # General high-footprint recommendation
    total_carbon = insights_data.get("total_carbon", 0)
    if total_carbon > MONTHLY_HIGH_FOOTPRINT_KG:
        recommendations.append(
            "**Overall**: Your footprint is significantly above average. "
            "Focus on the highest-impact category first (usually transport or food). "
            "Expected reduction: 30-50 kg CO2e/month for combined actions. Difficulty: Hard"
        )

    # Energy recommendation (if not already mentioned)
    if len(recommendations) < 3:
        recommendations.append(
            "**Housing & Utilities**: Switch to LED bulbs, use less AC/heating, "
            "and unplug devices when not in use. Expected reduction: 5-15 kg CO2e/month. Difficulty: Easy"
        )

    return recommendations[:5]  # Cap at 5 recommendations
