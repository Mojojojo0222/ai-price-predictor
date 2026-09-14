import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def create_price_chart(price_history: List[Dict], predictions: List[Dict] = None,
                       product_name: str = "Product", show_annotations: bool = True) -> go.Figure:
    """Create a comprehensive price chart with optional predictions overlay"""
    fig = go.Figure()

    # ---- Actual price history ----
    if price_history:
        dates = [datetime.fromisoformat(h["scraped_at"].replace("Z", "+00:00")) if "T" in str(h["scraped_at"]) else h["scraped_at"] for h in price_history]
        prices = [float(h["price"]) for h in price_history]

        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode="lines+markers",
            name="Actual Price",
            line=dict(color="#FF6B6B", width=2),
            marker=dict(size=5),
            hovertemplate="₹%{y:,.0f}<extra></extra>"
        ))

        if show_annotations and prices:
            # Min price annotation
            min_price = min(prices)
            min_idx = prices.index(min_price)
            fig.add_annotation(
                x=dates[min_idx],
                y=min_price,
                text=f"Lowest: ₹{min_price:,.0f}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowcolor="#2ECC71",
                font=dict(color="#2ECC71", size=11),
                bgcolor="rgba(46,204,113,0.15)",
                bordercolor="#2ECC71",
                borderwidth=1,
                borderpad=4
            )

            # Max price annotation
            max_price = max(prices)
            max_idx = prices.index(max_price)
            if max_price != min_price:
                fig.add_annotation(
                    x=dates[max_idx],
                    y=max_price,
                    text=f"Highest: ₹{max_price:,.0f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowcolor="#FF6B6B",
                    font=dict(color="#FF6B6B", size=11),
                    bgcolor="rgba(255,107,107,0.15)",
                    bordercolor="#FF6B6B",
                    borderwidth=1,
                    borderpad=4
                )

            # Current price annotation
            fig.add_annotation(
                x=dates[-1],
                y=prices[-1],
                text=f"Current: ₹{prices[-1]:,.0f}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowcolor="#3498DB",
                font=dict(color="#3498DB", size=11),
                bgcolor="rgba(52,152,219,0.15)",
                bordercolor="#3498DB",
                borderwidth=1,
                borderpad=4,
                ax=40,
                ay=-30
            )

    # ---- Prediction trend ----
    if predictions and len(predictions) > 0:
        pred_dates = [p["date"] for p in predictions]
        pred_prices = [p["predicted_price"] for p in predictions]
        pred_bands = [p.get("confidence_band", 0) for p in predictions]

        # Upper and lower confidence bands
        upper = [p + b for p, b in zip(pred_prices, pred_bands)]
        lower = [p - b for p, b in zip(pred_prices, pred_bands)]

        # Lower bound fill
        fig.add_trace(go.Scatter(
            x=pred_dates,
            y=lower,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        ))

        # Upper bound fill
        fig.add_trace(go.Scatter(
            x=pred_dates,
            y=upper,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(52,152,219,0.1)",
            name="Confidence Band",
            hoverinfo="skip"
        ))

        # Predicted price line
        fig.add_trace(go.Scatter(
            x=pred_dates,
            y=pred_prices,
            mode="lines",
            name="Predicted Price",
            line=dict(color="#3498DB", width=2, dash="dash"),
            hovertemplate="₹%{y:,.0f}<extra>Predicted</extra>"
        ))

        # Annotate predicted lowest
        if pred_prices:
            min_pred = min(pred_prices)
            min_pred_idx = pred_prices.index(min_pred)
            fig.add_annotation(
                x=pred_dates[min_pred_idx],
                y=min_pred,
                text=f"Predicted Low: ₹{min_pred:,.0f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="#2ECC71",
                font=dict(color="#FFF", size=12),
                bgcolor="rgba(46,204,113,0.8)",
                bordercolor="#2ECC71",
                borderwidth=1,
                borderpad=4
            )

    # ---- Layout ----
    fig.update_layout(
        title=dict(
            text=f"Price History: {product_name}",
            font=dict(size=16, color="#FFFFFF")
        ),
        xaxis=dict(
            title="Date",
            gridcolor="#2A2D3E",
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            title="Price (₹)",
            gridcolor="#2A2D3E",
            showgrid=True,
            zeroline=False,
            tickformat="₹%{d:,.0f}"
        ),
        plot_bgcolor="#1E2130",
        paper_bgcolor="#0E1117",
        font=dict(color="#AAAAAA"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=20, t=40, b=40)
    )

    fig.update_xaxes(gridwidth=1, gridcolor="#2A2D3E")
    fig.update_yaxes(gridwidth=1, gridcolor="#2A2D3E")

    return fig


def create_savings_gauge(savings_percent: float) -> go.Figure:
    """Create a gauge chart showing savings percentage"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=savings_percent,
        number={"suffix": "%", "font": {"size": 28, "color": "#FFFFFF"}},
        gauge={
            "axis": {"range": [0, 50], "tickwidth": 1, "tickcolor": "#2A2D3E"},
            "bar": {"color": "#FF6B6B"},
            "bgcolor": "#1E2130",
            "borderwidth": 2,
            "bordercolor": "#2A2D3E",
            "steps": [
                {"range": [0, 5], "color": "#2ECC71"},
                {"range": [5, 15], "color": "#F39C12"},
                {"range": [15, 50], "color": "#E74C3C"}
            ],
            "threshold": {
                "line": {"color": "#FFFFFF", "width": 3},
                "thickness": 0.75,
                "value": savings_percent
            }
        },
        title={"text": "Potential Savings", "font": {"size": 16, "color": "#AAAAAA"}}
    ))

    fig.update_layout(
        paper_bgcolor="#0E1117",
        font=dict(color="#FFFFFF"),
        height=250,
        margin=dict(l=30, r=30, t=60, b=30)
    )
    return fig


def create_recommendation_card(recommendation: str, confidence: float) -> str:
    """Create a styled HTML recommendation card"""
    if recommendation == "BUY_NOW":
        color = "#2ECC71"
        emoji = "🟢"
        label = "BUY NOW"
    elif recommendation == "WAIT":
        color = "#F39C12"
        emoji = "🟡"
        label = "WAIT"
    else:
        color = "#888888"
        emoji = "⚪"
        label = "NO DATA"

    html = f"""
    <div style="
        background: #1E2130;
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 16px 20px;
        margin: 10px 0;
    ">
        <div style="font-size: 20px; font-weight: 700; color: {color};">
            {emoji} {label}
        </div>
        <div style="color: #AAAAAA; margin-top: 4px;">
            Confidence: {confidence:.0f}%
        </div>
    </div>
    """
    return html


def create_product_card(product_data: Dict, analysis: Dict = None) -> str:
    """Create a styled HTML product card"""
    name = product_data.get("name", "Unknown Product")
    url = product_data.get("url", "#")
    image = product_data.get("image_url", "")

    if analysis and analysis.get("status") == "ANALYZED":
        current = analysis["current_price"]
        pred_low = analysis.get("predicted_low", current)
        rec = analysis.get("recommendation", "NO_DATA")
        conf = analysis.get("confidence", 0)
        savings = current - pred_low
        savings_pct = (savings / current) * 100 if current > 0 else 0

        rec_color = "#2ECC71" if rec == "BUY_NOW" else "#F39C12" if rec == "WAIT" else "#888"
        rec_label = "BUY NOW" if rec == "BUY_NOW" else "WAIT" if rec == "WAIT" else "NO DATA"
        rec_emoji = "🟢" if rec == "BUY_NOW" else "🟡" if rec == "WAIT" else "⚪"

        html = f"""
        <div style="
            background: #1E2130;
            border: 1px solid #2A2D3E;
            border-radius: 12px;
            padding: 20px;
            margin: 12px 0;
        ">
            <div style="display: flex; align-items: flex-start; gap: 16px;">
                {"<img src='" + image + "' style='width:80px;height:80px;object-fit:cover;border-radius:8px;' />" if image else ""}
                <div style="flex: 1;">
                    <a href="{url}" target="_blank" style="
                        color: #FFFFFF;
                        font-size: 16px;
                        font-weight: 600;
                        text-decoration: none;
                    ">{name}</a>

                    <div style="margin-top: 8px;">
                        <span style="font-size: 14px; color: #888;">Current:</span>
                        <span style="font-size: 20px; font-weight: 700; color: #FF6B6B;">
                            ₹{current:,.0f}
                        </span>
                    </div>

                    <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 13px;">
                        <div style="color: #2ECC71;">
                            🎯 Predicted Low: ₹{pred_low:,.0f}
                        </div>
                        <div style="color: #888;">
                            Potential savings: ₹{savings:,.0f} ({savings_pct:.0f}%)
                        </div>
                    </div>

                    <div style="
                        display: inline-block;
                        margin-top: 10px;
                        padding: 4px 12px;
                        border-radius: 16px;
                        background: {rec_color}22;
                        color: {rec_color};
                        font-size: 13px;
                        font-weight: 600;
                    ">{rec_emoji} {rec_label} (Confidence: {conf:.0f}%)</div>
                </div>
            </div>
        </div>
        """
    else:
        html = f"""
        <div style="
            background: #1E2130;
            border: 1px solid #2A2D3E;
            border-radius: 12px;
            padding: 20px;
            margin: 12px 0;
        ">
            <a href="{url}" target="_blank" style="
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 600;
                text-decoration: none;
            ">{name}</a>
            <div style="color: #888; margin-top: 4px;">Waiting for price data...</div>
        </div>
        """
    return html


def create_savings_summary_chart(user_stats: Dict) -> Optional[go.Figure]:
    """Create a summary chart of buy/wait recommendations across tracked products"""
    buy = user_stats.get("buy_now_count", 0)
    wait = user_stats.get("wait_count", 0)
    total = user_stats.get("total_tracked", 0)

    if total == 0:
        return None

    labels = ["Buy Now", "Wait"]
    values = [buy, wait]
    colors = ["#2ECC71", "#F39C12"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.55,
        textinfo="label+percent",
        textfont=dict(color="#FFFFFF", size=13),
        hovertemplate="%{label}: %{value} products<extra></extra>"
    )])

    fig.update_layout(
        title=dict(
            text=f"Your {total} Tracked Products",
            font=dict(size=16, color="#FFFFFF")
        ),
        paper_bgcolor="#0E1117",
        font=dict(color="#AAAAAA"),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig