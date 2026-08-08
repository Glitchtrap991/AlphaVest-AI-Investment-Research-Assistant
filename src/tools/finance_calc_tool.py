"""
src/tools/finance_calc_tool.py — Financial calculation tool.

Supports: CAGR, growth %, ROI, and comparison tables.
"""
from __future__ import annotations

import json

from langchain_core.tools import tool


@tool
def run_financial_calculation(calculation_json: str) -> str:
    """Perform financial calculations: CAGR, growth percentage, ROI, or comparison tables.

    Use this when the user asks for specific financial calculations or when
    you need to compute metrics for a comparison.

    Args:
        calculation_json: A JSON string with the following structure:
            For CAGR:
                {"type": "cagr", "beginning_value": 100, "ending_value": 200, "years": 5}
            For growth percentage:
                {"type": "growth_pct", "old_value": 100, "new_value": 150}
            For ROI:
                {"type": "roi", "gain": 50, "cost": 200}
            For comparison table:
                {"type": "comparison_table", "companies": [
                    {"name": "Company A", "metric1": "value1", "metric2": "value2"},
                    {"name": "Company B", "metric1": "value1", "metric2": "value2"}
                ]}

    Returns:
        The calculation result as a formatted string or markdown table.
    """
    try:
        data = json.loads(calculation_json)
    except json.JSONDecodeError:
        return "Error: Invalid JSON input. Please provide a valid JSON string."

    calc_type = data.get("type", "").lower()

    if calc_type == "cagr":
        return _calc_cagr(data)
    elif calc_type == "growth_pct":
        return _calc_growth_pct(data)
    elif calc_type == "roi":
        return _calc_roi(data)
    elif calc_type == "comparison_table":
        return _build_comparison_table(data)
    else:
        return f"Error: Unknown calculation type '{calc_type}'. Supported: cagr, growth_pct, roi, comparison_table."


# ── Private helpers ──────────────────────────────────────────────────────────

def _calc_cagr(data: dict) -> str:
    try:
        bv = float(data["beginning_value"])
        ev = float(data["ending_value"])
        years = float(data["years"])
        if bv <= 0 or years <= 0:
            return "Error: beginning_value and years must be positive."
        cagr = (ev / bv) ** (1 / years) - 1
        return f"CAGR = {cagr:.2%} (from {bv:,.2f} to {ev:,.2f} over {years:.1f} years)"
    except (KeyError, ValueError, ZeroDivisionError) as e:
        return f"Error calculating CAGR: {e}"


def _calc_growth_pct(data: dict) -> str:
    try:
        old = float(data["old_value"])
        new = float(data["new_value"])
        if old == 0:
            return "Error: old_value cannot be zero."
        growth = (new - old) / old * 100
        return f"Growth = {growth:+.2f}% (from {old:,.2f} to {new:,.2f})"
    except (KeyError, ValueError) as e:
        return f"Error calculating growth %: {e}"


def _calc_roi(data: dict) -> str:
    try:
        gain = float(data["gain"])
        cost = float(data["cost"])
        if cost == 0:
            return "Error: cost cannot be zero."
        roi = gain / cost * 100
        return f"ROI = {roi:.2f}% (gain {gain:,.2f} on cost {cost:,.2f})"
    except (KeyError, ValueError) as e:
        return f"Error calculating ROI: {e}"


def _build_comparison_table(data: dict) -> str:
    companies = data.get("companies", [])
    if not companies:
        return "Error: No companies provided for comparison table."

    # Gather all metric keys (preserve order)
    all_keys: list[str] = []
    for co in companies:
        for k in co:
            if k != "name" and k not in all_keys:
                all_keys.append(k)

    # Build markdown table
    header = "| Metric | " + " | ".join(co.get("name", "?") for co in companies) + " |"
    separator = "|---|" + "|".join("---" for _ in companies) + "|"
    rows: list[str] = []
    for key in all_keys:
        row = f"| {key} | " + " | ".join(str(co.get(key, "N/A")) for co in companies) + " |"
        rows.append(row)

    return "\n".join([header, separator, *rows])
