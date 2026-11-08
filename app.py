from __future__ import annotations

from io import BytesIO
from pathlib import Path
import hashlib

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analysis_engine import ALIASES, CANONICAL_FIELDS, auto_map_columns, prepare_data, run_analysis

BASE_DIR = Path(__file__).resolve().parent
DEMO_PATH = BASE_DIR / "sample_retail_transactions.csv"

st.set_page_config(
    page_title="RetailPulse | AI-Powered Retail Business Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# Theme and reusable UI helpers
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
      html, body, [class*="css"] { font-family: Inter, sans-serif; }
      .stApp { background: #edf5ff; color: #10213f; }
      .block-container { max-width: 1580px; padding-top: .65rem; padding-bottom: 2rem; }
      [data-testid="stHeader"] { background: transparent; }
      [data-testid="stToolbar"] { right: 1rem; }
      .rp-nav { display:flex; align-items:center; justify-content:space-between; gap:20px; padding:13px 22px;
        margin:0 0 22px 0; border-radius:16px; color:#f8fbff;
        background:linear-gradient(105deg,#071b36 0%,#0b2a4e 65%,#0b385c 100%);
        box-shadow:0 8px 22px rgba(4,24,50,.18); }
      .rp-brand { font-size:27px; font-weight:900; letter-spacing:-1px; white-space:nowrap; }
      .rp-brand span { color:#20d5ee; }
      .rp-tagline { color:#c7d8ef; font-size:13px; border-left:1px solid #55708e; padding-left:20px; margin-left:14px; }
      .rp-nav-right { color:#d8e8fb; font-weight:600; font-size:13px; white-space:nowrap; }
      .hero-panel { min-height:340px; padding:26px 28px; border-radius:22px; color:#f6fbff;
        background:radial-gradient(circle at 85% 80%,rgba(0,204,255,.22),transparent 30%),
        linear-gradient(115deg,#071c39 0%,#0b3157 62%,#11506e 100%);
        box-shadow:0 12px 28px rgba(8,39,78,.18); }
      .hero-eyebrow { color:#77e9f7; text-transform:uppercase; font-size:12px; font-weight:800; letter-spacing:2px; }
      .hero-title { color:#fff; font-size:clamp(30px,3.1vw,48px); line-height:1.12; letter-spacing:-1.7px; font-weight:900; margin:12px 0 14px; }
      .hero-title .accent { color:#20d8ed; }
      .hero-copy { color:#d5e6f7; font-size:16px; max-width:640px; line-height:1.65; }
      .feature-row { display:flex; gap:24px; flex-wrap:wrap; margin-top:28px; }
      .feature { min-width:112px; color:#e8f5ff; font-size:12px; line-height:1.35; font-weight:600; }
      .feature-icon { display:block; font-size:25px; margin-bottom:6px; }
      .upload-card { height:100%; border:2px solid #6dddf1; border-radius:22px; padding:22px 24px 16px;
        background:linear-gradient(145deg,#f7fbff,#e4f0ff); box-shadow:0 0 0 5px rgba(32,216,237,.08),0 14px 35px rgba(6,26,55,.22); }
      .upload-title { text-align:center; color:#0b2853; font-weight:900; font-size:27px; margin:0 0 6px; }
      .upload-copy { text-align:center; color:#314d71; font-size:13px; margin-bottom:12px; }
      .upload-foot { text-align:center; color:#48617e; font-size:11px; padding-top:9px; }
      .stFileUploader { background:#edf5ff; border:2px dashed #83b9fa; border-radius:15px; padding:12px; }
      .stFileUploader section { background:transparent; }
      .stFileUploader [data-testid="stFileUploaderDropzone"] { background:transparent; border:0; }
      .stButton > button, .stDownloadButton > button { border-radius:11px; border:0; font-weight:700; min-height:42px;
        background:linear-gradient(100deg,#0875ee,#0755bf); color:white; box-shadow:0 5px 12px rgba(6,91,195,.17); }
      .stButton > button:hover, .stDownloadButton > button:hover { background:linear-gradient(100deg,#0566d8,#06479e); color:#fff; }
      .section-shell { background:linear-gradient(180deg,#f7fbff,#eaf4ff); border:1px solid #c7ddf8; border-radius:20px;
        padding:18px 18px 15px; box-shadow:0 7px 20px rgba(24,77,133,.10); }
      .section-title { color:#10244a; font-size:21px; font-weight:900; letter-spacing:-.5px; margin:0 0 14px; }
      .kpi-card { border:1px solid #d9e7f8; border-radius:15px; padding:14px 13px; min-height:88px;
        background:linear-gradient(145deg,#ffffff,#f3f8ff); box-shadow:0 3px 8px rgba(30,70,120,.06); }
      .kpi-label { color:#344b6b; font-size:12px; font-weight:700; margin-bottom:7px; }
      .kpi-value { color:#071b3a; font-size:23px; font-weight:900; letter-spacing:-.8px; }
      .kpi-delta { color:#07964a; font-size:12px; font-weight:800; margin-top:4px; }
      .panel { background:#fff; border:1px solid #d8e6f6; border-radius:16px; padding:14px 16px; box-shadow:0 3px 10px rgba(22,61,105,.06); }
      .panel-title { color:#0d2346; font-size:16px; font-weight:900; margin-bottom:9px; }
      .alert-box { border:1px solid #f6cbd1; border-radius:14px; padding:13px 15px; background:#fff7f8; margin-bottom:9px; }
      .alert-box strong { color:#9a1e2d; }
      .rec-box { border:1px solid #c9ecd9; border-radius:14px; padding:13px 15px; background:#f3fff8; margin-bottom:9px; }
      .rec-box strong { color:#087344; }
      .small-note { color:#62758e; font-size:11px; line-height:1.45; }
      div[data-testid="stMetric"] { background:#fff; border:1px solid #dce8f7; border-radius:14px; padding:12px; box-shadow:0 3px 8px rgba(30,70,120,.05); }
      div[data-testid="stMetricLabel"] { color:#344b6b; font-weight:700; }
      [data-testid="stDataFrame"] { border:1px solid #dce8f7; border-radius:12px; }
      div[data-testid="stTabs"] button { font-weight:800; color:#183a61; }
      .footnote { text-align:center; color:#647b96; font-size:11px; padding:18px 0 6px; }
      @media (max-width: 900px) { .rp-tagline { display:none; } .hero-panel { min-height:auto; } .rp-nav { padding:12px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

if "page" not in st.session_state:
    st.session_state.page = "home"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Overview"
if "data" not in st.session_state:
    st.session_state.data = None
if "quality" not in st.session_state:
    st.session_state.quality = None
if "source_files" not in st.session_state:
    st.session_state.source_files = []


def fmt_money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "Not available"
    value = float(value)
    absolute = abs(value)
    if absolute >= 10_000_000:
        return f"₹{value / 10_000_000:,.2f} Cr"
    if absolute >= 100_000:
        return f"₹{value / 100_000:,.2f} L"
    return f"₹{value:,.0f}"


def fmt_pct(value: float | int | None) -> str:
    return "Not available" if value is None or pd.isna(value) else f"{float(value):.1f}%"


def fmt_delta(change: dict | None) -> str:
    if not change:
        return "No comparison baseline"
    v = change.get("pct", np.nan)
    if pd.notna(v):
        return f"{v:+.1f}% vs previous"
    absolute = change.get("absolute", np.nan)
    if pd.notna(absolute):
        return f"{absolute:+,.1f} vs previous"
    return "No comparison baseline"


def nav_bar(is_dashboard: bool = False) -> None:
    st.markdown(
        """
        <div class="rp-nav">
          <div style="display:flex;align-items:center;min-width:0;">
            <div class="rp-brand">🛒 Retail<span>Pulse</span></div>
            <div class="rp-tagline">AI-Powered Retail Business Intelligence System</div>
          </div>
          <div class="rp-nav-right">▣ &nbsp;Dashboard&nbsp;&nbsp;&nbsp;　▤ &nbsp;Reports&nbsp;&nbsp;&nbsp;　ⓘ &nbsp;Help&nbsp;&nbsp;&nbsp;　●</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def read_uploaded_file(file_obj) -> pd.DataFrame:
    name = file_obj.name.lower()
    payload = file_obj.getvalue()
    if name.endswith(".csv"):
        last_error = None
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return pd.read_csv(BytesIO(payload), encoding=enc, low_memory=False)
            except UnicodeDecodeError as exc:
                last_error = exc
        raise ValueError(f"Could not decode CSV file: {last_error}")
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(BytesIO(payload), engine="openpyxl" if name.endswith(".xlsx") else "xlrd")
    raise ValueError("Supported file types are CSV, XLSX and XLS.")


def mapping_ui(files_and_frames: list[tuple[object, pd.DataFrame]]) -> list[dict[str, str | None]]:
    mappings = []
    if not files_and_frames:
        return mappings
    with st.expander("Review automatic column detection (optional)", expanded=False):
        st.caption("RetailPulse tries to recognize common retail column names. Change any field that was detected incorrectly.")
        for file_index, (file_obj, raw) in enumerate(files_and_frames):
            detected = auto_map_columns(list(raw.columns))
            file_key = hashlib.md5(f"{file_index}-{file_obj.name}".encode()).hexdigest()[:8]
            st.markdown(f"**{file_obj.name}** · {len(raw):,} rows · {len(raw.columns)} columns")
            selected: dict[str, str | None] = {}
            columns = [str(c) for c in raw.columns]
            for field in CANONICAL_FIELDS:
                options = ["— Not mapped —"] + columns
                default = detected.get(field)
                default_index = options.index(default) if default in options else 0
                label = field.replace("_", " ").title()
                choice = st.selectbox(label, options, index=default_index, key=f"map_{file_key}_{field}")
                selected[field] = None if choice == "— Not mapped —" else choice
            mappings.append(selected)
            st.divider()
    if not mappings:
        # Keep the automatically detected mappings when the advanced panel is not opened.
        for _, raw in files_and_frames:
            mappings.append(auto_map_columns(list(raw.columns)))
    return mappings


def normalize_file(raw: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    normalized = pd.DataFrame(index=raw.index)
    for field in CANONICAL_FIELDS:
        source = mapping.get(field)
        normalized[field] = raw[source] if source and source in raw.columns else np.nan
    return normalized


def load_dataset_group(files_and_frames: list[tuple[object, pd.DataFrame]], mappings: list[dict[str, str | None]]):
    normalized_frames = []
    accepted_files, skipped_files = [], []
    for (file_obj, raw), mapping in zip(files_and_frames, mappings):
        has_date = bool(mapping.get("date"))
        has_sales = bool(mapping.get("sales_amount")) or (bool(mapping.get("quantity")) and bool(mapping.get("unit_price")))
        if not has_date or not has_sales:
            skipped_files.append(file_obj.name)
            continue
        normalized_frames.append(normalize_file(raw, mapping))
        accepted_files.append(file_obj.name)
    if not normalized_frames:
        raise ValueError("No uploaded file has both a usable date and a sales amount (or quantity plus unit price). Review the column mapping and try again.")
    combined = pd.concat(normalized_frames, ignore_index=True, sort=False)
    canonical_mapping = {field: field for field in CANONICAL_FIELDS}
    data, quality = prepare_data(combined, canonical_mapping)
    return data, quality, accepted_files, skipped_files


def make_pdf_report(result: dict, quality: dict, files: list[str]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("PDF support dependency is missing. Run pip install -r requirements.txt.") from exc
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=14*mm, bottomMargin=14*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallRP", parent=styles["BodyText"], fontSize=8.5, leading=11))
    current, previous = result["current"], result["previous"]
    story = [
        Paragraph("RetailPulse — Retail Business Intelligence Report", styles["Title"]),
        Paragraph(f"Files analyzed: {', '.join(files)}", styles["SmallRP"]),
        Paragraph(f"Selected period: {result['period']['start'].date()} to {result['period']['end'].date()}", styles["SmallRP"]),
        Spacer(1, 10),
    ]
    rows = [["Metric", "Selected period", "Previous period"],
            ["Net revenue", fmt_money(current["revenue"]), fmt_money(previous["revenue"])],
            ["Profit measure", fmt_money(current["profit"]), fmt_money(previous["profit"])],
            ["Transactions", f"{current['transactions']:,}", f"{previous['transactions']:,}"],
            ["Average order value", fmt_money(current["aov"]), fmt_money(previous["aov"])],
            ["Profit margin", fmt_pct(current["margin_pct"]), fmt_pct(previous["margin_pct"])]]
    table = Table(rows, colWidths=[55*mm, 55*mm, 55*mm])
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B2C50")),
                               ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                               ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#D0D9E6")),
                               ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                               ("PADDING", (0,0), (-1,-1), 7)]))
    story += [Paragraph("Performance summary", styles["Heading2"]), table, Spacer(1, 10), Paragraph("Detected business signals", styles["Heading2"])]
    for finding in result["findings"]:
        story += [Paragraph(f"<b>{finding['severity'].upper()} — {finding['title']}</b><br/>{finding['detail']}", styles["SmallRP"]), Spacer(1, 5)]
    story += [Spacer(1, 5), Paragraph("Recommended actions", styles["Heading2"])]
    for item in result["recommendations"]:
        story += [Paragraph(f"<b>{item['priority']} priority — {item['action']}</b><br/>{item['reason']}", styles["SmallRP"]), Spacer(1, 5)]
    story += [Spacer(1, 8), Paragraph("Interpretation note: these are data-driven diagnostic signals and suggested investigation areas, not proof of cause. Profit is based on the supplied profit column or complete cost coverage. This application does not calculate net profit unless operating expenses are provided.", styles["SmallRP"])]
    doc.build(story)
    return buffer.getvalue()


def make_excel_report(data: pd.DataFrame, result: dict, quality: dict) -> bytes:
    buffer = BytesIO()
    current = result["current"]
    metrics = pd.DataFrame([
        ["Net revenue", current["revenue"]], ["Profit", current["profit"]],
        ["Transactions", current["transactions"]], ["Average order value", current["aov"]],
        ["Profit margin (%)", current["margin_pct"]], ["Cost coverage (%)", quality["cost_coverage_pct"]],
    ], columns=["Metric", "Value"])
    findings = pd.DataFrame(result["findings"])
    recommendations = pd.DataFrame(result["recommendations"])
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        metrics.to_excel(writer, sheet_name="KPIs", index=False)
        result["monthly"].to_excel(writer, sheet_name="Monthly Trend", index=False)
        findings.to_excel(writer, sheet_name="Findings", index=False)
        recommendations.to_excel(writer, sheet_name="Recommendations", index=False)
        data.to_excel(writer, sheet_name="Cleaned Data", index=False)
    return buffer.getvalue()


def kpi_card(label: str, value: str, delta: str, icon: str = "") -> None:
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-label'>{icon} {label}</div><div class='kpi-value'>{value}</div><div class='kpi-delta'>{delta}</div></div>",
        unsafe_allow_html=True,
    )


def render_demo_preview() -> None:
    # Explicitly illustrative mock values so visitors understand the product before uploading.
    st.markdown("<div class='section-shell'><div class='section-title'>▥ &nbsp;Sample Business Insights <span style='font-size:12px;color:#6b7d95;font-weight:600'>(Illustrative preview — not your company data)</span></div>", unsafe_allow_html=True)
    cols = st.columns(5)
    demo_kpis = [
        ("Total Revenue", "₹12.48 Cr", "▲ +8.2%", "▤"),
        ("Total Profit", "₹1.86 Cr", "▲ +5.7%", "▥"),
        ("Total Transactions", "4,52,730", "▲ +9.1%", "🛒"),
        ("Avg. Order Value", "₹2,758", "▲ +3.4%", "◇"),
        ("Profit Margin", "14.9%", "▲ +1.2 pp", "%"),
    ]
    for col, item in zip(cols, demo_kpis):
        with col:
            kpi_card(item[0], item[1], item[2], item[3])
    p1, p2, p3 = st.columns([1.35, 1, 1.1])
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    trend = pd.DataFrame({"Month": months, "Revenue": [0.85, 1.02, 1.13, 1.29, 1.52, 1.41, 1.65, 1.76, 2.02, 1.72, 2.11, 2.2],
                          "Profit": [0.24, 0.27, 0.26, 0.28, 0.35, 0.29, 0.34, 0.46, 0.60, 0.52, 0.66, 0.71]})
    with p1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend.Month, y=trend.Revenue, name="Revenue", mode="lines+markers", line=dict(color="#1385f5", width=3), fill="tozeroy"))
        fig.add_trace(go.Scatter(x=trend.Month, y=trend.Profit, name="Profit", mode="lines+markers", line=dict(color="#9a4de8", width=3), fill="tozeroy"))
        fig.update_layout(title="Sales & Profit Trend", height=285, margin=dict(l=8,r=8,t=42,b=8), legend=dict(orientation="h", y=1.12),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="₹ Cr", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="preview_trend")
    with p2:
        cat = pd.DataFrame({"Category": ["Electronics", "Apparel", "Groceries", "Home & Living", "Others"], "Share": [32,24,18,14,12]})
        fig = px.pie(cat, names="Category", values="Share", hole=.58, title="Revenue by Category")
        fig.update_layout(height=285, margin=dict(l=6,r=6,t=42,b=6), legend=dict(font=dict(size=10)),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="preview_category")
    with p3:
        stores = pd.DataFrame({"Store": ["Hyderabad", "Bengaluru", "Chennai", "Pune", "Mumbai"], "Profit": [38.2,32.7,26.1,18.9,16.4]})
        fig = px.bar(stores, x="Profit", y="Store", orientation="h", title="Store Performance (Profit)", text="Profit")
        fig.update_traces(marker_color="#19b78f", texttemplate="%{text:.1f} L", textposition="outside")
        fig.update_layout(height=285, margin=dict(l=8,r=35,t=42,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis_title="₹ L", yaxis_title=None, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="preview_stores")
    st.markdown("</div>", unsafe_allow_html=True)


def render_home() -> None:
    nav_bar()
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown(
            """
            <div class="hero-panel">
              <div class="hero-eyebrow">Retail intelligence, made actionable</div>
              <div class="hero-title">Welcome to Our<br><span class="accent">AI-Powered Retail</span><br>Business Intelligence System</div>
              <div class="hero-copy">Upload your retail data, analyze business performance, identify issues, and get data-driven recommendations to grow your business.</div>
              <div class="feature-row">
                <div class="feature"><span class="feature-icon">📊</span>Analyze Sales<br>&amp; Profit</div>
                <div class="feature"><span class="feature-icon">🏬</span>Track Store<br>Performance</div>
                <div class="feature"><span class="feature-icon">🔎</span>Identify<br>Business Issues</div>
                <div class="feature"><span class="feature-icon">💡</span>Get Smart<br>Recommendations</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown("<div class='upload-card'><div class='upload-title'>☁️ Upload Your Dataset</div><div class='upload-copy'>Upload CSV or Excel files (single or multiple)</div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Drag and drop your files here", type=["csv", "xlsx", "xls"], accept_multiple_files=True,
                                          label_visibility="collapsed", key="dataset_uploader")
        st.markdown("<div class='upload-foot'>Supported formats: .csv, .xlsx, .xls &nbsp; | &nbsp; Multiple compatible transaction files allowed</div></div>", unsafe_allow_html=True)

        files_and_frames: list[tuple[object, pd.DataFrame]] = []
        file_errors = []
        for file_obj in uploaded_files or []:
            try:
                raw = read_uploaded_file(file_obj)
                if raw.empty:
                    file_errors.append(f"{file_obj.name}: file is empty")
                else:
                    files_and_frames.append((file_obj, raw))
            except Exception as exc:
                file_errors.append(f"{file_obj.name}: {exc}")
        for msg in file_errors:
            st.error(msg)

        mappings = mapping_ui(files_and_frames)
        sales_already_net = st.checkbox(
            "My Sales / Revenue field is already net of discounts and refunds",
            value=False,
            help="Enable this for exports where Sales already includes discounts/returns (for example, some POS or Superstore exports). RetailPulse will not subtract the mapped discount/refund fields a second time.",
            key="sales_already_net",
        )
        if files_and_frames:
            st.success(f"{len(files_and_frames)} file(s) loaded. Review the automatic column mapping if needed, then analyze.")
        b1, b2 = st.columns([1.25, 1])
        with b1:
            analyze_clicked = st.button("⚡ Analyze Uploaded Dataset", type="primary", use_container_width=True, disabled=not bool(files_and_frames))
        with b2:
            demo_clicked = st.button("Explore Demo Dashboard", use_container_width=True)

        if analyze_clicked:
            try:
                effective_mappings = mappings
                if sales_already_net:
                    effective_mappings = [dict(m, discount_amount=None, discount_pct=None, refund_amount=None) for m in mappings]
                data, quality, accepted, skipped = load_dataset_group(files_and_frames, effective_mappings)
                st.session_state.data = data
                st.session_state.quality = quality
                st.session_state.source_files = accepted
                st.session_state.skipped_files = skipped
                st.session_state.page = "dashboard"
                st.session_state.active_tab = "Overview"
                st.rerun()
            except Exception as exc:
                st.error(f"Could not analyze the uploaded data: {exc}")
        if demo_clicked:
            try:
                demo_raw = pd.read_csv(DEMO_PATH)
                demo_mapping = auto_map_columns(list(demo_raw.columns))
                data, quality = prepare_data(demo_raw, demo_mapping)
                st.session_state.data = data
                st.session_state.quality = quality
                st.session_state.source_files = ["sample_retail_transactions.csv (synthetic demo)"]
                st.session_state.skipped_files = []
                st.session_state.page = "dashboard"
                st.session_state.active_tab = "Overview"
                st.rerun()
            except Exception as exc:
                st.error(f"Demo data could not be loaded: {exc}")

    st.write("")
    render_demo_preview()
    st.markdown("<div class='footnote'>RetailPulse preview values are illustrative only. Upload your own data to generate company-specific results.</div>", unsafe_allow_html=True)


def render_dashboard() -> None:
    data: pd.DataFrame = st.session_state.data
    quality: dict = st.session_state.quality
    if data is None or data.empty:
        st.session_state.page = "home"
        st.rerun()

    nav_bar(is_dashboard=True)
    tabs = ["Overview", "Sales", "Profit", "Stores", "Customers", "Products", "Reports"]
    tab_cols = st.columns([1.15, .75, .75, .75, .95, .85, .85, .7])
    with tab_cols[0]:
        if st.button("← Upload another dataset", key="back_upload", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    for col, label in zip(tab_cols[1:], tabs):
        with col:
            button_type = "primary" if st.session_state.active_tab == label else "secondary"
            if st.button(label, key=f"nav_{label}", type=button_type, use_container_width=True):
                st.session_state.active_tab = label
                st.rerun()

    st.markdown("<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin:16px 0 10px'><div style='font-size:25px;font-weight:900;color:#10244a'>Company Performance Overview</div><div style='font-size:12px;color:#536b87'>Live analysis of uploaded data</div></div>", unsafe_allow_html=True)
    min_date = data["date"].min().date()
    max_date = data["date"].max().date()
    start_end = st.date_input("Analysis date range", value=(min_date, max_date), min_value=min_date, max_value=max_date,
                              key="analysis_date_range", help="The KPI cards use this period. Period-change findings compare it with the immediately preceding period of equal length.")
    if isinstance(start_end, (tuple, list)) and len(start_end) == 2:
        start_date, end_date = start_end
    else:
        start_date = end_date = start_end
    try:
        result = run_analysis(data, quality["has_cost"], start_date, end_date)
    except Exception as exc:
        st.error(f"Date range could not be analyzed: {exc}")
        return
    current, changes = result["current"], result["changes"]

    kpis = st.columns(5)
    with kpis[0]: kpi_card("Total Revenue", fmt_money(current["revenue"]), fmt_delta(changes["revenue"]), "▤")
    with kpis[1]: kpi_card("Total Profit", fmt_money(current["profit"]) if quality["has_cost"] else "Not available", fmt_delta(changes["profit"]) if quality["has_cost"] else "Cost / profit data needed", "▥")
    with kpis[2]: kpi_card("Total Transactions", f"{current['transactions']:,}", fmt_delta(changes["transactions"]), "🛒")
    with kpis[3]: kpi_card("Avg. Order Value", fmt_money(current["aov"]), fmt_delta(changes["aov"]), "◇")
    with kpis[4]: kpi_card("Profit Margin", fmt_pct(current["margin_pct"]) if quality["has_cost"] else "Not available", fmt_delta(changes["margin_pct"]) if quality["has_cost"] else "Cost / profit data needed", "%")

    st.caption(f"Analyzed {quality['valid_rows']:,} valid transaction rows from {len(st.session_state.source_files)} accepted file(s). Revenue method: {quality['revenue_method']}. Profit source: {quality.get('profit_source','unavailable')}.")
    if getattr(st.session_state, "skipped_files", []):
        st.warning("Skipped files without a usable date and sales field: " + ", ".join(st.session_state.skipped_files))
    if not quality["has_cost"]:
        st.info("Your dataset does not contain complete cost or profit information. Revenue and sales analysis are available; profit and margin are hidden rather than estimated as zero.")

    active_tab = st.session_state.active_tab
    if active_tab == "Overview":
        render_overview(data, quality, result)
    elif active_tab == "Sales":
        render_sales(data, quality, result)
    elif active_tab == "Profit":
        render_profit(data, quality, result)
    elif active_tab == "Stores":
        render_stores(data, quality, result)
    elif active_tab == "Customers":
        render_customers(data, quality, result)
    elif active_tab == "Products":
        render_products(data, quality, result)
    elif active_tab == "Reports":
        render_reports(data, quality, result)
    st.markdown("<div class='footnote'>RetailPulse MVP · Upload-driven retail analytics · Diagnostic signals are not proof of cause. No uploaded file is permanently stored by this local Streamlit session.</div>", unsafe_allow_html=True)


def render_overview(data: pd.DataFrame, quality: dict, result: dict) -> None:
    monthly = result["monthly"].copy()
    left, right = st.columns([1.35, 1])
    with left:
        if not monthly.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly.month, y=monthly.revenue, mode="lines+markers", name="Revenue", line=dict(color="#1385f5", width=3), fill="tozeroy"))
            if quality["has_cost"] and "profit" in monthly:
                fig.add_trace(go.Scatter(x=monthly.month, y=monthly.profit, mode="lines+markers", name="Profit", line=dict(color="#9a4de8", width=3)))
            fig.update_layout(title="Sales & Profit Trend", height=315, margin=dict(l=8,r=8,t=45,b=8), legend=dict(orientation="h", y=1.12),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="Amount (₹)", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("A date-based trend cannot be created from this data.")
    with right:
        category_data = result["current_df"].groupby("category", as_index=False).agg(revenue=("net_revenue", "sum"))
        category_data = category_data[category_data.category != "Unknown"].sort_values("revenue", ascending=False).head(8)
        if not category_data.empty:
            fig = px.pie(category_data, names="category", values="revenue", hole=.58, title="Revenue by Category")
            fig.update_layout(height=315, margin=dict(l=8,r=8,t=45,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Map a category / department field to view revenue mix.")

    a, b = st.columns([1, 1])
    with a:
        st.markdown("<div class='panel'><div class='panel-title'>Store Performance</div>", unsafe_allow_html=True)
        cur = result["current_df"]
        if (cur.store != "Unknown").any():
            metric = "gross_profit" if quality["has_cost"] else "net_revenue"
            label = "Profit" if quality["has_cost"] else "Revenue"
            stores = cur.groupby("store", as_index=False)[metric].sum().sort_values(metric, ascending=False).head(8)
            fig = px.bar(stores, x=metric, y="store", orientation="h", text=metric, title=None)
            fig.update_traces(marker_color="#16b88b", texttemplate="%{text:,.0f}", textposition="outside")
            fig.update_layout(height=300, margin=dict(l=4,r=25,t=5,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis_title=label, yaxis_title=None, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No store / branch field was detected in the uploaded dataset.")
        st.markdown("</div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='panel'><div class='panel-title'>Why might performance be changing?</div>", unsafe_allow_html=True)
        for item in result["findings"][:5]:
            st.markdown(f"<div class='alert-box'><strong>⚠ {item['title']}</strong><br><span style='color:#52657d;font-size:12px'>{item['detail']}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel'><div class='panel-title'>Recommended Business Actions</div>", unsafe_allow_html=True)
    rec_cols = st.columns(2)
    for idx, item in enumerate(result["recommendations"][:6]):
        with rec_cols[idx % 2]:
            st.markdown(f"<div class='rec-box'><strong>✓ {item['priority']} priority · {item['action']}</strong><br><span style='color:#526b62;font-size:12px'>{item['reason']}</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("Signals and recommendations are generated from observed data patterns. They highlight where to investigate and do not establish causation by themselves.")


def render_sales(data: pd.DataFrame, quality: dict, result: dict) -> None:
    st.subheader("Sales Performance Analysis")
    monthly = result["monthly"]
    fig = px.area(monthly, x="month", y="revenue", title="Monthly Net Revenue")
    fig.update_traces(line_color="#1686f5", fillcolor="rgba(22,134,245,.18)")
    fig.update_layout(height=330, margin=dict(l=8,r=8,t=45,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="Net revenue (₹)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    cur = result["current_df"]
    dim_cols = st.columns(2)
    for col, field, title in [(dim_cols[0], "category", "Revenue by Category"), (dim_cols[1], "region", "Revenue by Region")]:
        with col:
            if (cur[field] != "Unknown").any():
                grouped = cur.groupby(field, as_index=False).net_revenue.sum().sort_values("net_revenue", ascending=False).head(12)
                fig = px.bar(grouped, x=field, y="net_revenue", title=title)
                fig.update_layout(height=300, margin=dict(l=8,r=8,t=45,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="Revenue (₹)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info(f"{title}: map the relevant field during upload to enable this view.")
    st.markdown("#### Monthly sales summary")
    st.dataframe(monthly.rename(columns={"month":"Month", "revenue":"Revenue", "transactions":"Transactions", "profit":"Profit", "margin_pct":"Margin %"}), use_container_width=True, hide_index=True)


def render_profit(data: pd.DataFrame, quality: dict, result: dict) -> None:
    st.subheader("Profitability & Margin Analysis")
    if not quality["has_cost"]:
        st.warning("Profit cannot be calculated reliably because complete cost or source-profit data is missing. Upload unit cost / COGS for every sales row, or a complete profit column.")
        st.markdown("**What to include:** `unit_cost`, `cost_amount` / `COGS`, or a source `profit` field in your transaction data.")
        st.dataframe(pd.DataFrame([{"Check": "Profit coverage", "Result": quality["cost_method"]}, {"Check": "Cost/profit coverage", "Result": f"{quality['cost_coverage_pct']:.1f}%"}]), use_container_width=True, hide_index=True)
        return
    monthly = result["monthly"]
    if "profit" in monthly:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly.month, y=monthly.profit, mode="lines+markers", name="Profit", line=dict(color="#8b4de8", width=3), fill="tozeroy"))
        fig.update_layout(title="Monthly Profit Trend", height=330, margin=dict(l=8,r=8,t=45,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="Profit (₹)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    cur = result["current_df"]
    if (cur.category != "Unknown").any():
        category_profit = cur.groupby("category", as_index=False).agg(revenue=("net_revenue", "sum"), profit=("gross_profit", "sum"))
        category_profit["margin_pct"] = np.where(category_profit.revenue != 0, category_profit.profit / category_profit.revenue * 100, np.nan)
        st.markdown("#### Profit and margin by category")
        st.dataframe(category_profit.sort_values("profit").rename(columns={"category":"Category", "revenue":"Revenue", "profit":"Profit", "margin_pct":"Margin %"}), use_container_width=True, hide_index=True)
    st.caption("Profit measure: " + quality.get("cost_method", "Not available"))


def render_stores(data: pd.DataFrame, quality: dict, result: dict) -> None:
    st.subheader("Store & Regional Performance")
    cur = result["current_df"]
    if (cur.store != "Unknown").any():
        metrics = {"transactions": ("transaction_key", "nunique"), "revenue": ("net_revenue", "sum")}
        if quality["has_cost"]:
            metrics["profit"] = ("gross_profit", "sum")
        stores = cur.groupby(["region", "store"], as_index=False).agg(**metrics).sort_values("revenue", ascending=False)
        metric = "profit" if quality["has_cost"] else "revenue"
        fig = px.bar(stores.sort_values(metric).tail(15), x=metric, y="store", color="region", orientation="h", title=f"Top Stores by {'Profit' if quality['has_cost'] else 'Revenue'}")
        fig.update_layout(height=380, margin=dict(l=8,r=8,t=45,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.dataframe(stores, use_container_width=True, hide_index=True)
    elif (cur.region != "Unknown").any():
        regions = cur.groupby("region", as_index=False).net_revenue.sum().sort_values("net_revenue", ascending=False)
        st.plotly_chart(px.bar(regions, x="region", y="net_revenue", title="Revenue by Region"), use_container_width=True)
        st.dataframe(regions, use_container_width=True, hide_index=True)
    else:
        st.info("Store and regional analysis requires a store, branch, city or region field in the uploaded data.")


def render_customers(data: pd.DataFrame, quality: dict, result: dict) -> None:
    st.subheader("Customer Intelligence")
    cur = result["current_df"]
    if not (cur.customer_id != "Unknown").any():
        st.info("Customer analysis is unavailable because no customer identifier was detected. Upload a Customer ID / Client ID field to explore repeat purchases and customer value.")
        return
    orders = cur.groupby("customer_id").agg(transactions=("transaction_key", "nunique"), revenue=("net_revenue", "sum")).reset_index()
    unique = len(orders)
    repeat = int((orders.transactions > 1).sum())
    c1,c2,c3 = st.columns(3)
    c1.metric("Unique Customers", f"{unique:,}")
    c2.metric("Repeat Customers", f"{repeat:,}")
    c3.metric("Repeat Customer Share", fmt_pct(repeat / unique * 100 if unique else np.nan))
    top = orders.sort_values("revenue", ascending=False).head(20)
    fig = px.bar(top.head(10).sort_values("revenue"), x="revenue", y="customer_id", orientation="h", title="Top Customers by Revenue")
    fig.update_layout(height=340, margin=dict(l=8,r=8,t=45,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.dataframe(orders.sort_values("revenue", ascending=False), use_container_width=True, hide_index=True)


def render_products(data: pd.DataFrame, quality: dict, result: dict) -> None:
    st.subheader("Product & Category Performance")
    cur = result["current_df"]
    if not (cur.product != "Unknown").any() and not (cur.category != "Unknown").any():
        st.info("Product analysis requires a product, SKU or category field. Map one during upload to enable this section.")
        return
    group = "product" if (cur.product != "Unknown").any() else "category"
    agg = {"revenue": ("net_revenue", "sum"), "transactions": ("transaction_key", "nunique")}
    if quality["has_cost"]:
        agg["profit"] = ("gross_profit", "sum")
    product_table = cur.groupby(group, as_index=False).agg(**agg).sort_values("revenue", ascending=False)
    left, right = st.columns(2)
    with left:
        fig = px.bar(product_table.head(12), x="revenue", y=group, orientation="h", title="Top Products by Revenue")
        fig.update_layout(height=380, margin=dict(l=8,r=8,t=45,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        low = product_table.sort_values("profit" if quality["has_cost"] else "revenue").head(12)
        metric = "profit" if quality["has_cost"] else "revenue"
        fig = px.bar(low, x=metric, y=group, orientation="h", title=f"Lowest {'Profit' if quality['has_cost'] else 'Revenue'} Products")
        fig.update_layout(height=380, margin=dict(l=8,r=8,t=45,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.dataframe(product_table, use_container_width=True, hide_index=True)


def render_reports(data: pd.DataFrame, quality: dict, result: dict) -> None:
    st.subheader("Reports & Data Exports")
    st.write("Download a management summary, the standardized transaction data, or an Excel workbook containing KPIs, trends, findings and recommendations.")
    files = st.session_state.source_files
    c1, c2, c3 = st.columns(3)
    with c1:
        try:
            pdf = make_pdf_report(result, quality, files)
            st.download_button("⬇ Download PDF Report", data=pdf, file_name="RetailPulse_Business_Report.pdf", mime="application/pdf", use_container_width=True)
        except Exception as exc:
            st.error(f"PDF report unavailable: {exc}")
    with c2:
        try:
            xlsx = make_excel_report(data, result, quality)
            st.download_button("⬇ Download Excel Report", data=xlsx, file_name="RetailPulse_Analytics_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except Exception as exc:
            st.error(f"Excel report unavailable: {exc}")
    with c3:
        csv_bytes = data.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Download Cleaned CSV", data=csv_bytes, file_name="RetailPulse_Cleaned_Data.csv", mime="text/csv", use_container_width=True)
    st.markdown("#### Data quality checks")
    checks = [
        ("Rows in uploaded files", f"{quality['original_rows']:,}"),
        ("Valid transaction rows", f"{quality['valid_rows']:,}"),
        ("Invalid date rows excluded", f"{quality['invalid_date_rows']:,}"),
        ("Rows missing usable sales excluded", f"{quality['invalid_sales_rows']:,}"),
        ("Cost / profit coverage", f"{quality['cost_coverage_pct']:.1f}%"),
        ("Revenue method", quality["revenue_method"]),
        ("Profit method", quality["cost_method"]),
        ("Transaction count method", quality["transaction_method"]),
    ]
    st.dataframe(pd.DataFrame(checks, columns=["Check", "Result"]), use_container_width=True, hide_index=True)
    st.markdown("#### Standardized dataset preview")
    show = [c for c in ["date", "order_id", "product", "category", "quantity", "gross_sales", "discount_amount", "refund_amount", "net_revenue", "cogs", "gross_profit", "store", "region", "customer_id"] if c in data.columns]
    st.dataframe(data[show].head(100), use_container_width=True, hide_index=True)


if st.session_state.page == "home":
    render_home()
else:
    render_dashboard()
