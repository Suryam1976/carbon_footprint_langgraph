"""Node 8: Insights and Recommendations Generation"""

from langchain_core.messages import AIMessage
from core.state import GraphState

def generate_insights_node(state: GraphState) -> GraphState:
    """
    Node 8: Generate actionable insights and recommendations
    """
    category_breakdown = state.get("category_breakdown", {})
    total_carbon = state.get("total_carbon_kg_avg", 0)
    sorted_categories = state.get("sorted_categories", [])
    
    recommendations = []
    insights = []
    
    # Generate category-specific recommendations
    for category, data in sorted_categories[:5]:  # Top 5 categories
        carbon_kg = data["avg"]
        count = data["count"]
        amount = data["amount_spent"]
        
        if carbon_kg < 1:
            continue  # Skip very low emission categories
        
        if category == "transport_ride_sharing" and carbon_kg > 5:
            recommendations.append(
                f"🚌 Switch to metro/public transport to reduce ride-sharing emissions by 30% "
                f"(currently {carbon_kg:.1f} kg CO2e from {count} trips)"
            )
        
        elif category == "food_delivery" and carbon_kg > 3:
            recommendations.append(
                f"🍳 Consider meal planning to reduce food delivery frequency by 25% "
                f"(currently {carbon_kg:.1f} kg CO2e from {count} orders)"
            )
        
        elif category == "transport_fuel" and carbon_kg > 10:
            recommendations.append(
                f"🚗 Consider carpooling or electric vehicle to reduce fuel emissions by 40% "
                f"(currently {carbon_kg:.1f} kg CO2e from fuel purchases)"
            )
        
        elif category == "housing_utilities" and carbon_kg > 8:
            recommendations.append(
                f"💡 Use energy-efficient appliances to lower utility emissions by 15% "
                f"(currently {carbon_kg:.1f} kg CO2e from utilities)"
            )
        
        elif category == "shopping_online" and carbon_kg > 5:
            recommendations.append(
                f"📦 Buy local products when possible to reduce shopping emissions by 10% "
                f"(currently {carbon_kg:.1f} kg CO2e from {count} purchases)"
            )
        
        elif category == "food_groceries" and carbon_kg > 4:
            recommendations.append(
                f"🥬 Choose local/seasonal produce to reduce grocery emissions by 20% "
                f"(currently {carbon_kg:.1f} kg CO2e from groceries)"
            )
    
    # Generate general insights
    if total_carbon > 50:
        insights.append(f"📈 Your monthly carbon footprint of {total_carbon:.1f} kg CO2e is above average for urban India")
    elif total_carbon > 25:
        insights.append(f"📊 Your monthly carbon footprint of {total_carbon:.1f} kg CO2e is moderate")
    else:
        insights.append(f"🌱 Your monthly carbon footprint of {total_carbon:.1f} kg CO2e is relatively low")
    
    # Category distribution insights
    if len(sorted_categories) > 0:
        top_category = sorted_categories[0]
        top_percentage = (top_category[1]["avg"] / total_carbon) * 100 if total_carbon > 0 else 0
        
        if top_percentage > 40:
            insights.append(
                f"⚠️ {top_category[1]['display_name']} accounts for {top_percentage:.0f}% of your emissions - "
                f"focus here for maximum impact"
            )
    
    # Transport vs other categories
    transport_categories = ["transport_ride_sharing", "transport_fuel", "transport_public"]
    transport_total = sum(
        data["avg"] for cat, data in category_breakdown.items() 
        if cat in transport_categories
    )
    
    if transport_total > total_carbon * 0.5:
        insights.append(
            f"🚗 Transport accounts for {(transport_total/total_carbon)*100:.0f}% of your emissions - "
            f"consider sustainable mobility options"
        )
    
    # Add default recommendations if none generated
    if not recommendations:
        recommendations = [
            "🌱 Great job! Your carbon footprint is relatively low",
            "♻️ Continue making sustainable choices in your daily spending",
            "📱 Track your progress monthly to maintain awareness"
        ]
    
    # Limit recommendations to top 4
    recommendations = recommendations[:4]
    
    state["recommendations"] = recommendations
    state["insights"] = insights
    
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"✅ Generated {len(insights)} insights and {len(recommendations)} recommendations"),
        AIMessage(content="🎯 Analysis complete! Check your personalized carbon footprint report.")
    ]
    
    return state

