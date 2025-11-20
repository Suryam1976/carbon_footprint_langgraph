"""Report generation utilities"""

import json
from datetime import datetime
from typing import Dict, Any, List

def generate_report(result: Dict[str, Any]) -> str:
    """
    Generate a comprehensive text report from analysis results
    """
    report = []
    
    # Header
    report.append("=" * 70)
    report.append("🌱 CARBON FOOTPRINT ANALYSIS REPORT")
    report.append("=" * 70)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary
    total_min = result.get("total_carbon_kg_min", 0)
    total_max = result.get("total_carbon_kg_max", 0)
    total_avg = result.get("total_carbon_kg_avg", 0)
    
    report.append("📊 CARBON FOOTPRINT SUMMARY")
    report.append("-" * 30)
    report.append(f"Total Emissions (Min): {total_min:.2f} kg CO2e")
    report.append(f"Total Emissions (Max): {total_max:.2f} kg CO2e")
    report.append(f"Total Emissions (Avg): {total_avg:.2f} kg CO2e")
    report.append("")
    
    # Processing stats
    rule_count = result.get("rule_based_count", 0)
    llm_count = result.get("llm_based_count", 0)
    total_txns = rule_count + llm_count
    
    report.append("⚙️ PROCESSING EFFICIENCY")
    report.append("-" * 25)
    report.append(f"Total Transactions: {total_txns}")
    report.append(f"Rule-based Categorization: {rule_count} ({(rule_count/total_txns*100):.1f}%)")
    report.append(f"LLM-based Categorization: {llm_count} ({(llm_count/total_txns*100):.1f}%)")
    report.append("")
    
    # Category breakdown
    category_breakdown = result.get("category_breakdown", {})
    if category_breakdown:
        report.append("🏷️ CATEGORY BREAKDOWN")
        report.append("-" * 20)
        
        # Sort by emissions
        sorted_categories = sorted(
            category_breakdown.items(),
            key=lambda x: x[1].get("avg", 0),
            reverse=True
        )
        
        for category, data in sorted_categories:
            avg_emissions = data.get("avg", 0)
            count = data.get("count", 0)
            amount = data.get("amount_spent", 0)
            percentage = (avg_emissions / total_avg * 100) if total_avg > 0 else 0
            
            display_name = data.get("display_name", category.replace("_", " ").title())
            report.append(f"{display_name}:")
            report.append(f"  Emissions: {avg_emissions:.2f} kg CO2e ({percentage:.1f}%)")
            report.append(f"  Transactions: {count}")
            report.append(f"  Amount Spent: ₹{amount:,.0f}")
            report.append("")
    
    # Insights
    insights = result.get("insights", [])
    if insights:
        report.append("💡 KEY INSIGHTS")
        report.append("-" * 15)
        for insight in insights:
            report.append(f"• {insight}")
        report.append("")
    
    # Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        report.append("🎯 RECOMMENDATIONS")
        report.append("-" * 18)
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")
        report.append("")
    
    # Monthly breakdown if available
    monthly_breakdown = result.get("monthly_breakdown", {})
    if monthly_breakdown:
        report.append("📅 MONTHLY BREAKDOWN")
        report.append("-" * 20)
        for month, data in monthly_breakdown.items():
            report.append(f"{month}: {data.get('total_carbon', 0):.2f} kg CO2e")
        report.append("")
    
    # Footer
    report.append("=" * 70)
    report.append("Privacy: PII redacted per DPDP Act 2023 | Powered by LangGraph")
    report.append("=" * 70)
    
    return "\n".join(report)

def generate_json_report(result: Dict[str, Any]) -> str:
    """
    Generate JSON report for download
    """
    json_result = {
        "timestamp": datetime.now().isoformat(),
        "total_carbon_kg_min": result.get("total_carbon_kg_min", 0),
        "total_carbon_kg_max": result.get("total_carbon_kg_max", 0),
        "total_carbon_kg_avg": result.get("total_carbon_kg_avg", 0),
        "rule_based_count": result.get("rule_based_count", 0),
        "llm_based_count": result.get("llm_based_count", 0),
        "category_breakdown": result.get("category_breakdown", {}),
        "monthly_breakdown": result.get("monthly_breakdown", {}),
        "insights": result.get("insights", []),
        "recommendations": result.get("recommendations", []),
        "processing_summary": result.get("processing_summary", {}),
        "carbon_estimates": result.get("carbon_estimates", [])
    }
    
    return json.dumps(json_result, indent=2, ensure_ascii=False)

def generate_csv_data(result: Dict[str, Any]) -> str:
    """
    Generate CSV data for transaction-level export
    """
    csv_lines = []
    
    # Header
    csv_lines.append("Date,Description,Amount,Category,Carbon_Min,Carbon_Max,Carbon_Avg,Method")
    
    # Transaction data
    carbon_estimates = result.get("carbon_estimates", [])
    for estimate in carbon_estimates:
        date = estimate.get("date", "")
        description = estimate.get("description", "").replace(",", ";")  # Escape commas
        amount = estimate.get("amount", 0)
        category = estimate.get("category", "")
        carbon_min = estimate.get("carbon_kg_min", 0)
        carbon_max = estimate.get("carbon_kg_max", 0)
        carbon_avg = estimate.get("carbon_kg_avg", 0)
        method = estimate.get("categorization_method", "")
        
        csv_lines.append(f"{date},{description},{amount},{category},{carbon_min},{carbon_max},{carbon_avg},{method}")
    
    return "\n".join(csv_lines)