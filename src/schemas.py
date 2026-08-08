"""
src/schemas.py — Pydantic models for structured output.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class InvestmentReport(BaseModel):
    """Structured investment research report.

    Only used when the agent is specifically asked to *produce a report*,
    not for every reply.
    """

    company_overview: str = Field(
        description="Brief overview of the company, its history, and market position."
    )
    industry: str = Field(
        description="The industry or sector the company operates in."
    )
    business_model: str = Field(
        description="How the company generates revenue."
    )
    latest_news: list[str] = Field(
        default_factory=list,
        description="Recent news headlines or developments.",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Key competitive strengths.",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Notable weaknesses or concerns.",
    )
    financial_highlights: list[str] = Field(
        default_factory=list,
        description="Key financial metrics and highlights.",
    )
    growth_opportunities: list[str] = Field(
        default_factory=list,
        description="Potential areas for future growth.",
    )
    potential_risks: list[str] = Field(
        default_factory=list,
        description="Risks that could affect the investment.",
    )
    investment_summary: str = Field(
        description="Overall investment recommendation and rationale."
    )

    def to_text(self) -> str:
        """Render the report as plain text for .txt export."""
        sections = [
            f"COMPANY OVERVIEW\n{self.company_overview}",
            f"INDUSTRY\n{self.industry}",
            f"BUSINESS MODEL\n{self.business_model}",
            f"LATEST NEWS\n" + "\n".join(f"  • {n}" for n in self.latest_news),
            f"STRENGTHS\n" + "\n".join(f"  • {s}" for s in self.strengths),
            f"WEAKNESSES\n" + "\n".join(f"  • {w}" for w in self.weaknesses),
            f"FINANCIAL HIGHLIGHTS\n" + "\n".join(f"  • {f}" for f in self.financial_highlights),
            f"GROWTH OPPORTUNITIES\n" + "\n".join(f"  • {g}" for g in self.growth_opportunities),
            f"POTENTIAL RISKS\n" + "\n".join(f"  • {r}" for r in self.potential_risks),
            f"INVESTMENT SUMMARY\n{self.investment_summary}",
        ]
        return "\n\n" + ("\n\n".join(sections)) + "\n"
