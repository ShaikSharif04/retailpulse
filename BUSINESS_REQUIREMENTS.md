# RetailPulse — Business Requirements

## Objective
Build an upload-driven retail intelligence application that helps a manager understand retail sales and profitability, identify areas that may need investigation, and review practical next actions.

## User journey
1. Manager opens RetailPulse and lands on the Welcome & Upload page.
2. Manager uploads one or more compatible CSV / Excel transaction files.
3. RetailPulse detects common fields and allows the manager to review / correct mappings.
4. Manager clicks Analyze Uploaded Dataset.
5. RetailPulse validates and standardizes the data, then navigates to the dashboard.
6. Manager explores Overview, Sales, Profit, Stores, Customers, Products and Reports.
7. Manager downloads the management report or standardized data.

## Functional requirements

| ID | Requirement | MVP implementation |
|---|---|---|
| FR-01 | Show welcome page on launch | Implemented |
| FR-02 | Upload CSV, XLSX and XLS | Implemented |
| FR-03 | Accept multiple compatible transaction files | Implemented |
| FR-04 | Detect common retail columns | Implemented |
| FR-05 | Allow manual field mapping | Implemented |
| FR-06 | Validate dates and sales values | Implemented |
| FR-07 | Calculate revenue and AOV | Implemented |
| FR-08 | Calculate profit from direct profit or complete cost data | Implemented |
| FR-09 | Show sales / profit trends | Implemented |
| FR-10 | Show category, store, region and product performance | Implemented when fields exist |
| FR-11 | Show customer patterns | Implemented when customer ID exists |
| FR-12 | Detect possible performance issues | Implemented with transparent rules |
| FR-13 | Recommend investigation / action areas | Implemented with rule-linked recommendations |
| FR-14 | Export PDF, Excel and cleaned CSV | Implemented |
| FR-15 | Persist company workspaces and accounts | Future scope |
| FR-16 | Join unrelated fact and dimension tables | Future scope |
| FR-17 | AI/LLM-generated explanations with evidence citations | Future scope |

## Non-functional requirements
- Explain unavailable metrics rather than showing fabricated zeros.
- Distinguish diagnostic signals from proven root causes.
- Do not infer profit when costs/profit data is incomplete.
- Keep the application usable on laptop-sized screens and responsive on smaller displays.
- Process uploaded data in the local session for the MVP; do not claim secure multi-company cloud hosting.

## Metric definitions
- Net revenue = gross line sales − mapped discounts − mapped refunds.
- Gross profit = net revenue − cost of goods sold, unless a complete source profit measure is provided.
- Profit margin = profit ÷ net revenue.
- Transactions = distinct order IDs; row count only as a labelled proxy if order ID is absent.
- AOV = net revenue ÷ transactions.
