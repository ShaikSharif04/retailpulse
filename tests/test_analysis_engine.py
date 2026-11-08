import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis_engine import auto_map_columns, prepare_data, run_analysis


def make_df():
    return pd.DataFrame([
        {"Order ID": "A1", "Order Date": "2025-01-01", "Quantity": 1, "Unit Price": 100,
         "Unit Cost": 60, "Discount %": 0, "Store": "S1", "Region": "North", "Product Name": "P1", "Customer ID": "C1"},
        {"Order ID": "A2", "Order Date": "2025-01-02", "Quantity": 1, "Unit Price": 100,
         "Unit Cost": 80, "Discount %": 0, "Store": "S1", "Region": "North", "Product Name": "P1", "Customer ID": "C2"},
        {"Order ID": "A3", "Order Date": "2025-01-31", "Quantity": 1, "Unit Price": 200,
         "Unit Cost": 100, "Discount %": 0.25, "Store": "S2", "Region": "South", "Product Name": "P2", "Customer ID": "C1"},
    ])


def test_auto_mapping_and_profit_calculation():
    raw = make_df()
    mapping = auto_map_columns(list(raw.columns))
    data, quality = prepare_data(raw, mapping)
    assert quality["has_cost"] is True
    assert quality["valid_rows"] == 3
    assert round(data["net_revenue"].sum(), 2) == 350.00
    assert round(data["gross_profit"].sum(), 2) == 110.00


def test_incomplete_cost_withholds_company_profit():
    raw = make_df()
    raw.loc[1, "Unit Cost"] = None
    mapping = auto_map_columns(list(raw.columns))
    _, quality = prepare_data(raw, mapping)
    assert quality["has_cost_data"] is True
    assert quality["has_cost"] is False
    assert quality["cost_coverage_pct"] < 100


def test_transaction_rise_and_profit_decline_finding():
    raw = pd.DataFrame([
        # Previous period: two transactions, stronger profit.
        {"order_id": "P1", "date": "2025-01-01", "quantity": 1, "unit_price": 100, "unit_cost": 50},
        {"order_id": "P2", "date": "2025-01-02", "quantity": 1, "unit_price": 100, "unit_cost": 50},
        # Current period: three transactions but each line loses money.
        {"order_id": "C1", "date": "2025-01-03", "quantity": 1, "unit_price": 100, "unit_cost": 120},
        {"order_id": "C2", "date": "2025-01-04", "quantity": 1, "unit_price": 100, "unit_cost": 120},
        {"order_id": "C3", "date": "2025-01-05", "quantity": 1, "unit_price": 100, "unit_cost": 120},
    ])
    mapping = auto_map_columns(list(raw.columns))
    data, quality = prepare_data(raw, mapping)
    result = run_analysis(data, quality["has_cost"], "2025-01-03", "2025-01-05")
    titles = [item["title"] for item in result["findings"]]
    assert "Transactions increased while profit decreased" in titles


def test_iso_dates_are_not_broken_by_dayfirst_setting():
    raw = make_df()
    mapping = auto_map_columns(list(raw.columns))
    data, quality = prepare_data(raw, mapping, dayfirst=True)
    assert quality["valid_rows"] == 3
    assert data["date"].min().date() == pd.Timestamp("2025-01-01").date()


def test_day_first_date_format_is_supported():
    raw = pd.DataFrame([
        {"Order ID": "D1", "Order Date": "07/11/2026", "Quantity": 1, "Unit Price": 100, "Unit Cost": 60},
    ])
    data, quality = prepare_data(raw, auto_map_columns(list(raw.columns)), dayfirst=True)
    assert quality["valid_rows"] == 1
    assert data["date"].iloc[0].date() == pd.Timestamp("2026-11-07").date()


def test_direct_profit_column_is_used_when_cost_column_is_not_available():
    raw = pd.DataFrame([
        {"Order ID": "A", "Order Date": "2025-02-01", "Sales": 200, "Profit": 40},
        {"Order ID": "B", "Order Date": "2025-02-02", "Sales": 300, "Profit": 75},
    ])
    data, quality = prepare_data(raw, auto_map_columns(list(raw.columns)))
    assert quality["has_cost"] is True
    assert quality["profit_source"] == "direct uploaded profit"
    assert round(data["gross_profit"].sum(), 2) == 115.00
    assert round(data["net_revenue"].sum(), 2) == 500.00


def test_mixed_direct_profit_and_cost_rows_can_produce_complete_profit():
    raw = pd.DataFrame([
        {"order_id": "A", "date": "2025-03-01", "sales": 100, "profit": 25},
        {"order_id": "B", "date": "2025-03-02", "sales": 150, "profit": None, "quantity": 1, "unit_cost": 90},
    ])
    data, quality = prepare_data(raw, auto_map_columns(list(raw.columns)))
    assert quality["has_cost"] is True
    assert quality["cost_coverage_pct"] == 100.0
    assert round(data["gross_profit"].sum(), 2) == 85.00
