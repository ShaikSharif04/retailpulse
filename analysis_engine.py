"""Core retail analytics and rule-based business diagnosis for RetailPulse."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd


CANONICAL_FIELDS = [
    "order_id", "date", "quantity", "unit_price", "sales_amount", "unit_cost",
    "cost_amount", "profit_amount", "discount_amount", "discount_pct", "refund_amount", "store",
    "region", "product", "category", "customer_id", "payment_method",
]

ALIASES = {
    "order_id": ["order_id", "orderid", "invoice_id", "invoice", "transaction_id", "transaction", "bill_no", "receipt_id"],
    "date": ["date", "order_date", "transaction_date", "invoice_date", "sales_date", "purchase_date", "business_date"],
    "quantity": ["quantity", "qty", "units", "units_sold", "item_quantity"],
    "unit_price": ["unit_price", "selling_price", "price", "retail_price", "unit_selling_price"],
    "sales_amount": ["sales", "sales_amount", "revenue", "gross_sales", "line_total", "total_sales", "total sales", "total", "total_amount", "amount", "sales_value", "net_sales", "weekly_sales", "total_retail_sales"],
    "unit_cost": ["unit_cost", "cost_price", "purchase_price", "unit_purchase_cost", "cost_per_unit"],
    "cost_amount": ["cost_amount", "total_cost", "cogs", "cost_of_goods_sold", "line_cost", "total_cogs"],
    "profit_amount": ["profit", "profit_amount", "gross_profit", "operating_profit", "profit_value", "total_profit", "gross_income"],
    "discount_amount": ["discount_amount", "discount_value", "discount_amt"],
    "discount_pct": ["discount_pct", "discountpct", "discount_percent", "discount_rate", "discount_percentage", "discount"],
    "refund_amount": ["refund_amount", "refund", "return_amount", "returned_amount", "credit_amount"],
    "store": ["store", "store_name", "store_id", "store_nbr", "branch", "branch_name", "outlet", "shop"],
    "region": ["region", "area", "zone", "city", "location", "state"],
    "product": ["product", "product_name", "product_id", "sku", "item", "item_name", "sub_category", "subcategory"],
    "category": ["category", "product_category", "department", "segment", "family", "product_family"],
    "customer_id": ["customer_id", "customer", "client_id", "buyer_id"],
    "payment_method": ["payment_method", "payment_type", "tender_type", "payment_mode"],
}


def _clean_name(value: Any) -> str:
    return "_".join(str(value).strip().lower().replace("%", "pct").replace("#", "no").replace("/", "_").replace("-", " ").split())


def _to_numeric(series: pd.Series) -> pd.Series:
    """Parse numbers that may include commas, currency symbols or a percent sign."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    text = series.astype("string").str.strip()
    negative_parentheses = text.str.match(r"^\(.*\)$", na=False)
    cleaned = text.str.replace(",", "", regex=False).str.replace(r"[^0-9.\-]", "", regex=True)
    values = pd.to_numeric(cleaned, errors="coerce")
    values.loc[negative_parentheses] = -values.loc[negative_parentheses].abs()
    return values


def auto_map_columns(columns: list[Any]) -> dict[str, str | None]:
    """Map common retail column names to the app's canonical fields."""
    lookup = {_clean_name(c): str(c) for c in columns}
    mapping: dict[str, str | None] = {}
    for field, candidates in ALIASES.items():
        mapping[field] = None
        for candidate in candidates:
            if candidate in lookup:
                mapping[field] = lookup[candidate]
                break
    return mapping


def prepare_data(raw: pd.DataFrame, mapping: dict[str, str | None], dayfirst: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Standardize a raw file and derive consistent retail metrics.

    Revenue assumptions:
    - sales_amount is treated as line sales before discounts/refunds.
    - Otherwise gross sales = quantity * unit_price.
    - discount_pct is interpreted as percentage points when values exceed 1,
      otherwise as a fraction (0.10 means 10%).
    - profit is calculated only when unit_cost or cost_amount is supplied.
    """
    if raw.empty:
        raise ValueError("The uploaded file is empty.")

    out = pd.DataFrame(index=raw.index)
    for field in CANONICAL_FIELDS:
        source = mapping.get(field)
        if source and source in raw.columns:
            out[field] = raw[source]
        else:
            out[field] = np.nan

    if out["date"].isna().all():
        raise ValueError("A date column is required. Map your order/transaction date column first.")

    raw_dates = out["date"]
    parsed_dates = pd.to_datetime(raw_dates, errors="coerce", dayfirst=dayfirst)
    # ISO dates begin with YYYY-MM-DD and must remain year-first even when the
    # user's locale option is DD/MM/YYYY.
    iso_mask = raw_dates.astype("string").str.match(r"^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}", na=False)
    if iso_mask.any():
        parsed_dates.loc[iso_mask] = pd.to_datetime(raw_dates.loc[iso_mask], errors="coerce", dayfirst=False)
    out["date"] = parsed_dates
    for numeric_col in ["quantity", "unit_price", "sales_amount", "unit_cost", "cost_amount", "profit_amount", "discount_amount", "discount_pct", "refund_amount"]:
        out[numeric_col] = _to_numeric(out[numeric_col])

    original_rows = len(out)
    invalid_dates = int(out["date"].isna().sum())
    out = out.dropna(subset=["date"]).copy()
    if out.empty:
        raise ValueError("No valid dates were found. Check the date format in your file.")

    calculated_sales = out["quantity"] * out["unit_price"]
    if out["sales_amount"].notna().any():
        out["gross_sales"] = out["sales_amount"].where(out["sales_amount"].notna(), calculated_sales)
        revenue_method = "Uploaded sales amount; missing rows fall back to quantity × unit price where available"
    elif calculated_sales.notna().any():
        out["gross_sales"] = calculated_sales
        revenue_method = "Quantity × unit price"
    else:
        raise ValueError("Provide either a sales/revenue amount column, or both quantity and unit price columns.")

    invalid_sales_rows = int(out["gross_sales"].isna().sum())
    out = out.dropna(subset=["gross_sales"]).copy()
    if out.empty:
        raise ValueError("No usable sales values were found. Provide sales_amount, or quantity and unit_price for the transaction rows.")

    out["discount_amount"] = out["discount_amount"].fillna(0)
    if out["discount_pct"].notna().any():
        pct = out["discount_pct"].fillna(0)
        pct = np.where(pct.abs() > 1, pct / 100.0, pct)
        pct_discount = out["gross_sales"] * np.clip(pct, 0, 1)
        # An explicit discount amount takes precedence; percentage is used where amount is missing/zero.
        use_pct = out["discount_amount"].eq(0)
        out.loc[use_pct, "discount_amount"] = pct_discount[use_pct]

    out["refund_amount"] = out["refund_amount"].fillna(0).clip(lower=0)
    out["net_revenue"] = out["gross_sales"].fillna(0) - out["discount_amount"].clip(lower=0) - out["refund_amount"]

    calculated_cost = out["unit_cost"] * out["quantity"]
    if out["cost_amount"].notna().any():
        out["cogs"] = out["cost_amount"].where(out["cost_amount"].notna(), calculated_cost)
        has_cost_data = bool(out["cogs"].notna().any())
        cost_method = "Uploaded total cost / COGS; missing rows fall back to quantity × unit cost where available"
    elif calculated_cost.notna().any():
        out["cogs"] = calculated_cost
        has_cost_data = True
        cost_method = "Quantity × unit cost"
    else:
        out["cogs"] = np.nan
        has_cost_data = False
        cost_method = "Not available — no complete cost/profit measure was supplied"

    # Some retail exports (for example, Superstore or Adidas reports) contain a
    # pre-calculated profit column rather than unit costs. Use direct profit for
    # those rows and calculated revenue-minus-cost for rows with complete COGS.
    calculated_profit = out["net_revenue"] - out["cogs"]
    out["gross_profit"] = out["profit_amount"].where(out["profit_amount"].notna(), calculated_profit)
    cost_coverage_pct = float(out["gross_profit"].notna().mean() * 100) if len(out) else 0.0
    has_cost = bool(len(out) and out["gross_profit"].notna().all())
    has_cost_data = bool(out["gross_profit"].notna().any())
    if out["profit_amount"].notna().all():
        cost_method = "Uploaded profit measure used directly (as defined by the source dataset)"
    elif has_cost and out["profit_amount"].notna().any():
        cost_method = "Combined uploaded profit values and calculated profit from complete row-level costs"
    elif has_cost:
        cost_method = "Calculated from net revenue minus complete cost / COGS data"
    elif has_cost_data:
        cost_method = "Partial profit / cost coverage; company-wide profit is withheld"
    else:
        cost_method = "Not available — no complete cost/profit measure was supplied"
    out["profit_margin_pct"] = np.where(out["net_revenue"] != 0, out["gross_profit"] / out["net_revenue"] * 100, np.nan)

    # Make optional dimensions usable in group-by operations.
    for col in ["store", "region", "product", "category", "customer_id", "payment_method"]:
        out[col] = out[col].fillna("Unknown").astype(str).str.strip().replace({"": "Unknown", "nan": "Unknown", "None": "Unknown"})

    if out["order_id"].notna().any():
        out["order_id"] = out["order_id"].astype(str).replace({"nan": np.nan, "None": np.nan})
        missing_order_ids = int(out["order_id"].isna().sum())
        out["transaction_key"] = out["order_id"].fillna("ROW-").astype(str) + np.where(out["order_id"].isna(), out.index.astype(str), "")
        transaction_method = "Distinct Order_ID / transaction ID"
    else:
        missing_order_ids = original_rows
        out["transaction_key"] = [f"ROW-{i}" for i in out.index]
        transaction_method = "Row count used as transaction proxy (no order ID supplied)"

    out["month"] = out["date"].dt.to_period("M").dt.to_timestamp()
    out["year_month"] = out["date"].dt.strftime("%Y-%m")
    out["discount_rate_pct"] = np.where(out["gross_sales"] > 0, out["discount_amount"] / out["gross_sales"] * 100, np.nan)

    quality = {
        "original_rows": original_rows,
        "valid_rows": len(out),
        "invalid_date_rows": invalid_dates,
        "invalid_sales_rows": invalid_sales_rows,
        "has_cost": has_cost,
        "has_cost_data": has_cost_data,
        "cost_coverage_pct": cost_coverage_pct,
        "revenue_method": revenue_method,
        "cost_method": cost_method,
        "profit_source": ("direct uploaded profit" if out["profit_amount"].notna().all() else ("mixed direct profit and calculated cost" if has_cost and out["profit_amount"].notna().any() else ("calculated from cost" if has_cost else "unavailable"))),
        "transaction_method": transaction_method,
        "missing_order_ids": missing_order_ids,
        "has_customer_id": bool((out["customer_id"] != "Unknown").any()),
        "has_region": bool((out["region"] != "Unknown").any()),
        "has_store": bool((out["store"] != "Unknown").any()),
        "has_category": bool((out["category"] != "Unknown").any()),
        "has_refunds": bool(out["refund_amount"].sum() > 0),
    }
    return out.sort_values("date"), quality


def _metrics(df: pd.DataFrame, has_cost: bool) -> dict[str, float | int]:
    orders = int(df["transaction_key"].nunique()) if not df.empty else 0
    revenue = float(df["net_revenue"].sum()) if not df.empty else 0.0
    gross_sales = float(df["gross_sales"].sum()) if not df.empty else 0.0
    discounts = float(df["discount_amount"].sum()) if not df.empty else 0.0
    refunds = float(df["refund_amount"].sum()) if not df.empty else 0.0
    cogs = float(df["cogs"].sum()) if has_cost and not df.empty and df["cogs"].notna().all() else np.nan
    profit = float(df["gross_profit"].fillna(0).sum()) if has_cost and not df.empty else np.nan
    margin = (profit / revenue * 100) if has_cost and revenue != 0 else np.nan
    return {
        "revenue": revenue,
        "gross_sales": gross_sales,
        "profit": profit,
        "cogs": cogs,
        "transactions": orders,
        "aov": revenue / orders if orders else 0.0,
        "margin_pct": margin,
        "discounts": discounts,
        "discount_rate_pct": discounts / gross_sales * 100 if gross_sales else 0.0,
        "refunds": refunds,
        "refund_rate_pct": refunds / gross_sales * 100 if gross_sales else 0.0,
        "loss_rows": int((df["gross_profit"] < 0).sum()) if has_cost and not df.empty else 0,
        "loss_amount": float(abs(df.loc[df["gross_profit"] < 0, "gross_profit"].sum())) if has_cost and not df.empty else np.nan,
    }


def _delta(current: float, previous: float) -> tuple[float, float]:
    change = current - previous
    pct = (change / abs(previous) * 100) if previous not in (0, 0.0) else np.nan
    return change, pct


def _dimension_comparison(df: pd.DataFrame, dimension: str, current_start: pd.Timestamp, current_end: pd.Timestamp,
                          previous_start: pd.Timestamp, previous_end: pd.Timestamp, metric: str) -> pd.DataFrame:
    current = df[(df.date >= current_start) & (df.date <= current_end)].groupby(dimension, dropna=False)[metric].sum().rename("current")
    previous = df[(df.date >= previous_start) & (df.date <= previous_end)].groupby(dimension, dropna=False)[metric].sum().rename("previous")
    result = pd.concat([current, previous], axis=1).fillna(0).reset_index()
    result["change"] = result["current"] - result["previous"]
    result["change_pct"] = np.where(result["previous"].abs() > 0, result["change"] / result["previous"].abs() * 100, np.nan)
    return result.sort_values("change")


def run_analysis(df: pd.DataFrame, has_cost: bool, current_start: date | pd.Timestamp,
                 current_end: date | pd.Timestamp) -> dict[str, Any]:
    """Compare selected period to immediately preceding equal-length period."""
    start = pd.Timestamp(current_start).normalize()
    end = pd.Timestamp(current_end).normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    if end < start:
        raise ValueError("The selected end date must be on or after the start date.")
    days = max(1, (end.normalize() - start.normalize()).days + 1)
    previous_end = start - pd.Timedelta(microseconds=1)
    previous_start = start - pd.Timedelta(days=days)

    current_df = df[(df.date >= start) & (df.date <= end)].copy()
    previous_df = df[(df.date >= previous_start) & (df.date <= previous_end)].copy()
    current = _metrics(current_df, has_cost)
    previous = _metrics(previous_df, has_cost)
    overall = _metrics(df, has_cost)

    changes: dict[str, dict[str, float]] = {}
    for key in ["revenue", "profit", "transactions", "aov", "margin_pct", "discount_rate_pct", "refund_rate_pct"]:
        c = current[key]
        p = previous[key]
        if pd.isna(c) or pd.isna(p):
            changes[key] = {"absolute": np.nan, "pct": np.nan}
        else:
            absolute, pct = _delta(float(c), float(p))
            changes[key] = {"absolute": absolute, "pct": pct}

    current_cogs_ratio = (current["cogs"] / current["revenue"] * 100) if has_cost and current["revenue"] else np.nan
    previous_cogs_ratio = (previous["cogs"] / previous["revenue"] * 100) if has_cost and previous["revenue"] else np.nan
    changes["cogs_ratio_pct"] = {"absolute": current_cogs_ratio - previous_cogs_ratio if pd.notna(current_cogs_ratio) and pd.notna(previous_cogs_ratio) else np.nan,
                                  "pct": np.nan}

    monthly = df.groupby("month", as_index=False).agg(
        revenue=("net_revenue", "sum"),
        transactions=("transaction_key", "nunique"),
        gross_sales=("gross_sales", "sum"),
        discounts=("discount_amount", "sum"),
    )
    if has_cost:
        profit_monthly = df.groupby("month", as_index=False).agg(profit=("gross_profit", "sum"), cogs=("cogs", "sum"))
        monthly = monthly.merge(profit_monthly, on="month", how="left")
        monthly["margin_pct"] = np.where(monthly.revenue != 0, monthly.profit / monthly.revenue * 100, np.nan)

    dimension_results = {}
    for dimension in ["region", "store", "category", "product"]:
        dimension_results[dimension] = _dimension_comparison(df, dimension, start, end, previous_start, previous_end,
                                                              "gross_profit" if has_cost else "net_revenue")

    findings: list[dict[str, str]] = []
    recommendations: list[dict[str, str]] = []

    def add_finding(severity: str, title: str, detail: str) -> None:
        findings.append({"severity": severity, "title": title, "detail": detail})

    def add_recommendation(priority: str, action: str, reason: str) -> None:
        recommendations.append({"priority": priority, "action": action, "reason": reason})

    if previous_df.empty:
        add_finding("info", "No previous-period baseline", "The immediately preceding comparison window contains no transactions. Upload a longer date range or select a later analysis period to compare performance.")
    if current_df.empty:
        add_finding("warning", "No transactions in selected period", "There are no valid rows in the selected date range. Change the analysis period.")

    rev_change = changes["revenue"]["pct"]
    txn_change = changes["transactions"]["pct"]
    profit_change = changes["profit"]["pct"]
    margin_change = changes["margin_pct"]["absolute"]

    if pd.notna(rev_change) and rev_change < -5:
        add_finding("high", "Revenue has declined", f"Net revenue is down {abs(rev_change):.1f}% versus the previous {days}-day period.")
        add_recommendation("High", "Inspect the regions, stores, categories and products with the largest revenue decline.", "These segments show where revenue weakened; validate stock availability, pricing, footfall and campaign activity with store teams.")
    if has_cost and pd.notna(profit_change) and profit_change < -5:
        add_finding("high", "Profit has declined", f"Gross profit is down {abs(profit_change):.1f}% versus the previous comparison period.")
        add_recommendation("High", "Run a margin review on the most negative product and category movements.", "Prioritize products where cost, discounting or product mix may be eroding gross profit.")
    if pd.notna(txn_change) and txn_change > 0 and has_cost and pd.notna(profit_change) and profit_change < 0:
        add_finding("high", "Transactions increased while profit decreased", f"Transactions rose {txn_change:.1f}% while gross profit fell {abs(profit_change):.1f}%. More orders are not translating into more profit.")
        add_recommendation("High", "Review average selling price, discounts, product mix and unit costs—not just order volume.", "Higher transaction volume alongside lower profit can signal lower-value baskets or weaker margins.")
    if has_cost and pd.notna(margin_change) and margin_change < -1:
        add_finding("medium", "Profit margin has weakened", f"Gross margin declined by {abs(margin_change):.1f} percentage points.")
        add_recommendation("High", "Set minimum margin guardrails by category and review exceptions before approving discounts.", "Protecting margin can improve profitability even when sales volume remains stable.")
    cogs_ratio_change = changes["cogs_ratio_pct"]["absolute"]
    if has_cost and pd.notna(cogs_ratio_change) and cogs_ratio_change > 1.5:
        add_finding("medium", "Product costs consume a larger share of revenue", f"COGS as a share of net revenue increased by {cogs_ratio_change:.1f} percentage points.")
        add_recommendation("High", "Review supplier price changes, purchase terms, wastage and product mix for the affected categories.", "An increasing cost-to-revenue ratio can compress gross profit even when orders are rising.")

    aov_change = changes["aov"]["pct"]
    if pd.notna(aov_change) and aov_change < -5:
        add_finding("medium", "Average order value has declined", f"Average order value is down {abs(aov_change):.1f}% versus the previous period.")
        add_recommendation("Medium", "Review basket composition, product bundles and cross-sell opportunities without relying on margin-eroding discounts.", "A falling average basket value may help explain why higher order counts are not producing enough revenue.")

    discount_delta = changes["discount_rate_pct"]["absolute"]
    if pd.notna(discount_delta) and discount_delta > 1:
        add_finding("medium", "Discount rate increased", f"Average discount rate increased by {discount_delta:.1f} percentage points.")
        add_recommendation("Medium", "Measure incremental units and profit generated by each promotion; stop promotions that destroy margin.", "A higher discount rate may reduce net revenue if the added volume does not compensate.")

    if has_cost and not current_df.empty:
        loss_df = current_df[current_df.gross_profit < 0]
        if not loss_df.empty:
            loss_products = loss_df.groupby("product").gross_profit.sum().sort_values().head(3)
            names = ", ".join([f"{name} ({value:,.0f})" for name, value in loss_products.items()])
            negative_line_loss = abs(float(loss_df.gross_profit.sum()))
            add_finding("high", "Loss-making transactions detected", f"{len(loss_df):,} line items have negative gross profit, totalling {negative_line_loss:,.2f} in negative line-level gross profit. Largest product-level losses: {names}.")
            add_recommendation("High", "Audit selling price, supplier cost, discount and data-entry accuracy for loss-making items.", "These rows have negative calculated gross profit and deserve immediate review.")

    if current["refund_rate_pct"] > previous["refund_rate_pct"] + 1 and current["gross_sales"] > 0 and previous["gross_sales"] > 0:
        add_finding("medium", "Refund rate increased", f"Refunds are {current['refund_rate_pct']:.1f}% of gross sales versus {previous['refund_rate_pct']:.1f}% previously.")
        add_recommendation("Medium", "Break down returns by product, store and reason code; review quality and fulfilment issues.", "A higher refund rate reduces realized revenue and may indicate an operational or product-quality issue.")

    # Highest negative movement by dimensions. Values are absolute currency movements.
    for dim, label in [("region", "region"), ("store", "store"), ("category", "category"), ("product", "product")]:
        comp = dimension_results[dim]
        if not comp.empty and not comp[dim].astype(str).eq("Unknown").all():
            declining = comp[comp.change < 0].head(1)
            if not declining.empty:
                row = declining.iloc[0]
                metric_label = "profit" if has_cost else "net revenue"
                add_finding("medium", f"Largest {label} decline: {row[dim]}", f"{metric_label.title()} changed by {row.change:,.2f} in this {label} compared with the previous period.")

    if current_df.empty or previous_df.empty:
        add_recommendation("Medium", "Load at least two comparable periods of data before drawing trend conclusions.", "Trend diagnosis requires a valid baseline and consistent date coverage.")
    if not has_cost:
        if current_df.empty:
            cost_reason = "Cost coverage is incomplete or unavailable, so company-wide profit, loss and margin are withheld."
        else:
            cost_reason = "Cost is missing for some or all transaction rows, so company-wide profit, loss and margin are withheld to avoid overstating profit."
        add_finding("warning", "Complete cost data is required", cost_reason)
        add_recommendation("High", "Provide unit_cost for every row or a complete cost_amount/COGS column.", "Profit and margin are only reliable when costs are available for every included transaction line.")
    if not findings:
        add_finding("positive", "No major deterioration detected by current rules", "The selected period did not cross the configured decline thresholds. Continue monitoring segment-level trends.")
        add_recommendation("Low", "Monitor the monthly trend and compare stores and product categories regularly.", "Early monitoring helps detect emerging issues before they materially affect profit.")

    # Business driver bridge: change in revenue and cost explains gross-profit movement.
    bridge = None
    if has_cost:
        bridge = {
            "revenue_change": current["revenue"] - previous["revenue"],
            "cogs_change": current["cogs"] - previous["cogs"],
            "profit_change": current["profit"] - previous["profit"],
        }

    # Customer statistics for selected period.
    customer_summary = {}
    if (current_df.customer_id != "Unknown").any():
        cust_orders = current_df.groupby("customer_id").transaction_key.nunique()
        customer_summary = {
            "unique_customers": int(cust_orders.index.nunique()),
            "repeat_customers": int((cust_orders > 1).sum()),
            "repeat_customer_pct": float((cust_orders > 1).mean() * 100) if len(cust_orders) else 0.0,
        }

    return {
        "current": current,
        "previous": previous,
        "overall": overall,
        "changes": changes,
        "current_df": current_df,
        "previous_df": previous_df,
        "monthly": monthly,
        "dimensions": dimension_results,
        "findings": findings,
        "recommendations": recommendations,
        "bridge": bridge,
        "customer_summary": customer_summary,
        "period": {"start": start, "end": end, "previous_start": previous_start, "previous_end": previous_end, "days": days},
    }
