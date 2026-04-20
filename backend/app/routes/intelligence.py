"""
Intelligence Endpoints — Government Decision Support Intelligence

GET /api/intelligence/national       — National state rankings, gaps & recommendations
GET /api/intelligence/state/{state}  — State-specific health score
GET /api/intelligence/trends         — System-wide governance trends
"""

from fastapi import APIRouter, HTTPException, Path
from app.services.intelligence_service import (
    compute_national_intelligence,
    compute_state_intelligence,
    compute_trends_intelligence,
)
from app.utils.logger import get_logger
from app.utils.response_formatter import build_intelligence_response

router = APIRouter()
logger = get_logger(__name__)


@router.get("/intelligence/national", tags=["Intelligence"])
async def national_intelligence():
    """
    National-level governance intelligence.

    Returns:
    - Full state ranking (score 0-10, status, breakdown)
    - Gap analysis (missing initiatives, weak areas, underperforming sectors)
    - Actionable recommendations (governance-relevant, data-grounded)
    - Top/bottom performing states
    - Risk alerts
    - Emerging scheme adoption trends
    - Confidence explanation

    Use case: Government oversight dashboard, resource allocation decisions
    """
    try:
        result = compute_national_intelligence()

        if result.get("status") == "error" or result.get("status") == "no_data":
            raise HTTPException(
                status_code=503,
                detail=result.get("message", "Intelligence unavailable"),
            )

        top_performers = result.get("top_performers", [])
        risk_alerts = result.get("risk_alerts", [])
        emerging = result.get("emerging_trends", [])
        gap_analysis = result.get("gap_analysis", [])
        recommendations = result.get("recommendations", [])
        confidence_reason = result.get("confidence_reason", "")
        confidence = result.get("confidence", 0.85)

        top_state = top_performers[0]["state"] if top_performers else "Unknown"

        # Build top_insights from computed intelligence
        top_insights = [
            f"Top performing state: {top_state} (Score: {top_performers[0]['score']}/10)" if top_performers else "Insufficient data",
            f"{len(risk_alerts)} governance risk alert(s) detected requiring attention",
            f"Most widely adopted scheme: {emerging[0]['scheme']} ({emerging[0]['states_mentioning']} states)" if emerging else "Scheme adoption data pending",
            f"{len(gap_analysis)} governance gap(s) identified across states",
            f"Emerging priority: {recommendations[0]['area']}" if recommendations else "No recommendations generated",
        ]

        ranking = result.get("all_states_scores", [])

        return build_intelligence_response(
            answer=(
                f"National governance intelligence: {result.get('total_states', 0)} states analyzed. "
                f"Top performer: {top_state}. "
                f"Risk alerts: {len(risk_alerts)}. "
                f"{len(gap_analysis)} gap(s) identified. "
                f"{len(recommendations)} recommendation(s) generated."
            ),
            top_insights=top_insights,
            gaps=gap_analysis,
            recommendations=recommendations,
            ranking=ranking,
            confidence_reason=confidence_reason,
            structured={
                "summary": "National governance health scorecard",
                "key_insights": top_insights,
                "changes_detected": [
                    "Active scheme adoption tracking",
                    "State performance benchmarking",
                    "Risk pattern detection",
                ],
                "risks": [
                    f"{a.get('state')}: {a.get('risk')}" for a in risk_alerts[:5]
                ],
                "status": "stable",
                "confidence": confidence,
                "sources": [],
            },
            sources=[],
            metadata={
                "route": "intelligence",
                "type": "national",
                "states_analyzed": result.get("total_states", 0),
                "risk_count": len(risk_alerts),
                "gap_count": len(gap_analysis),
                "recommendation_count": len(recommendations),
                "confidence": confidence,
                "confidence_reason": confidence_reason,
                "latency": 0.0,
            },
            data=result,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("National intelligence error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal intelligence error")


@router.get("/intelligence/state/{state_name}", tags=["Intelligence"])
async def state_intelligence(
    state_name: str = Path(..., description="State name e.g., 'Delhi', 'Maharashtra'"),
):
    """
    State-specific governance health assessment.

    Returns:
    - Overall health score (0-10) with dimensional breakdown
    - Schemes covered
    - Gap analysis for this state
    - Actionable recommendations
    - Confidence explanation

    Use case: State-level performance review, targeted interventions
    """
    try:
        result = compute_state_intelligence(state_name)

        if result.get("status") == "no_data":
            return build_intelligence_response(
                answer=f"No data available for {state_name}. Ensure reports have been ingested.",
                structured={
                    "summary": f"Insufficient data for {state_name}",
                    "key_insights": [],
                    "changes_detected": [],
                    "risks": ["No indexed data"],
                    "status": "no_data",
                    "confidence": 0.0,
                    "sources": [],
                },
                gaps=[],
                recommendations=[],
                confidence_reason="No reports indexed for this state.",
                sources=[],
                metadata={
                    "route": "intelligence",
                    "type": "state",
                    "state": state_name,
                    "status": "no_data",
                    "confidence": 0.0,
                },
                data=result,
            )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Error computing intelligence"),
            )

        score_dict = result.get("score", {})
        gap_analysis = result.get("gap_analysis", [])
        recommendations = result.get("recommendations", [])
        confidence_reason = result.get("confidence_reason", "")

        top_insights = [
            f"Overall Score: {score_dict.get('score', 0)}/10 ({score_dict.get('status', 'Unknown')})",
            f"Activity Level: {score_dict.get('breakdown', {}).get('activity_level', 0)}/10",
            f"Initiative Diversity: {score_dict.get('breakdown', {}).get('initiative_diversity', 0)}/10",
            f"Innovation Signal: {score_dict.get('breakdown', {}).get('innovation_signal', 0)}/10",
        ]

        return build_intelligence_response(
            answer=(
                f"{state_name} governance health score: {score_dict.get('score', 0)}/10 "
                f"({score_dict.get('status', 'Unknown')}). "
                f"{score_dict.get('justification', '[Assessment unavailable]')}"
            ),
            top_insights=top_insights,
            gaps=gap_analysis,
            recommendations=recommendations,
            confidence_reason=confidence_reason,
            structured={
                "summary": f"{state_name} Governance Health Assessment",
                "key_insights": top_insights,
                "changes_detected": result.get("schemes_covered", [])[:5],
                "risks": score_dict.get("risk_factors", []),
                "status": score_dict.get("status", "Unknown").lower(),
                "confidence": 0.80,
                "sources": [],
            },
            sources=[],
            metadata={
                "route": "intelligence",
                "type": "state",
                "state": state_name,
                "score": score_dict.get("score", 0),
                "status": score_dict.get("status", "Unknown"),
                "confidence": 0.80,
                "confidence_reason": confidence_reason,
            },
            data=result,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"State intelligence error for {state_name}", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal state intelligence error")


@router.get("/intelligence/trends", tags=["Intelligence"])
async def trends_intelligence():
    """
    System-wide governance trends and adoption patterns.

    Returns:
    - Scheme adoption rankings
    - Recent reporting activity
    - Innovation signal detection
    - Emerging patterns

    Use case: Strategic planning, policy impact assessment, trend analysis
    """
    try:
        result = compute_trends_intelligence()

        if result.get("status") == "error" or result.get("status") == "no_data":
            raise HTTPException(
                status_code=503,
                detail=result.get("message", "Trends unavailable"),
            )

        top_schemes = result.get("scheme_adoption", [])[:3]
        active_periods = result.get("active_months", [])[:3]
        innovations = result.get("innovation_signals", [])[:5]

        top_insights = [
            f"Top scheme: {top_schemes[0].get('scheme', 'N/A')}" if top_schemes else "No scheme data",
            f"Most active period: {active_periods[0].get('month', 'N/A')}" if active_periods else "No period data",
            f"Innovation momentum: {len(innovations)} modernization signal(s) detected",
        ]

        return build_intelligence_response(
            answer=(
                f"Governance trends analysis. Most mentioned schemes: "
                f"{', '.join([s.get('scheme', '?') for s in top_schemes])}. "
                f"Innovation signals: {len(innovations)} detected. "
                f"Active reporting periods: {len(active_periods)}."
            ),
            top_insights=top_insights,
            confidence_reason=(
                f"Trend analysis based on {len(result.get('active_months', []))} active reporting "
                f"periods and {len(result.get('scheme_adoption', []))} scheme adoption signals."
            ),
            structured={
                "summary": "System-Wide Governance Trends",
                "key_insights": top_insights,
                "changes_detected": [s.get("scheme") for s in top_schemes],
                "risks": [],
                "status": "stable",
                "confidence": 0.75,
                "sources": [],
            },
            sources=[],
            metadata={
                "route": "intelligence",
                "type": "trends",
                "schemes_tracked": len(top_schemes),
                "innovation_signals": len(innovations),
                "confidence": 0.75,
            },
            data=result,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Trends intelligence error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal trends intelligence error")
