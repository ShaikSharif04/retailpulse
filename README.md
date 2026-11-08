# RetailPulse — AI-Powered Retail Business Intelligence System

RetailPulse is a local, upload-driven retail analytics web application built with Python and Streamlit. Its interface follows the two reference screens supplied for this project:

1. **Welcome & Upload page:** branded welcome page, multiple-file upload, and clearly labelled illustrative dashboard preview.
2. **Business Intelligence dashboard:** after upload and analysis, the application opens an interactive dashboard with Overview, Sales, Profit, Stores, Customers, Products and Reports sections.

The dashboard calculates results from the uploaded data. The numbers and charts on the first page are only an illustrative preview; they are not presented as the user's company results.

## Features

- Upload one or multiple CSV, XLSX or XLS files.
- Automatically detect common retail fields and provide an optional column-mapping editor.
- Combine compatible transaction exports into a single analysis dataset.
- Validate dates and sales values and report rows excluded from analysis.
- Calculate net revenue, transaction count, average order value and—when reliable data is available—profit and profit margin.
- Accept profit columns supplied by the source dataset, or calculate profit from complete cost data.
- Explore monthly trends, category performance, store / region performance, customer patterns and product performance.
- Generate rule-based diagnostic signals and evidence-linked recommended actions.
- Download a PDF management report, an Excel workbook and cleaned standardized CSV data.

## Windows setup (recommended)

1. Extract `RetailPulse_Project.zip` to a normal folder such as `C:\Users\YourName\Downloads\RetailPulse_Project`.
2. Open the extracted folder and open the **retailpulse** folder.
3. Double-click `run_windows.bat`. The script creates a virtual environment, installs the required packages, and starts the application.
4. Open the local address Streamlit prints in the terminal. Usually it is `http://localhost:8501`.

### Alternative: VS Code / PowerShell

Open the `retailpulse` folder in VS Code, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

When PowerShell blocks virtual-environment activation, run this once in the same terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## How to use

1. Open RetailPulse. The Welcome & Upload page is the first screen.
2. Select one or more retail transaction CSV / Excel files, or drag them into the upload area.
3. Optionally open **Review automatic column detection** and correct any field mappings.
4. If your source Sales / Revenue field already includes discounts or refunds, enable the checkbox for net sales so RetailPulse does not subtract them again.
5. Click **Analyze Uploaded Dataset**.
5. The dashboard opens with metrics and charts computed from the uploaded rows.
6. Use the top navigation buttons to move between Overview, Sales, Profit, Stores, Customers, Products and Reports.
7. Select an analysis date range. The period-comparison findings compare the selected period with the immediately preceding period of equal length.
8. Use Reports to download PDF, Excel or cleaned CSV outputs.

The **Explore Demo Dashboard** button loads the synthetic sample data included in the project. This is useful for testing the dashboard before using a real company dataset.

## Supported data fields

The app automatically recognizes common variants of these fields. The mapping editor lets you override the automatic selection.

| Canonical field | Examples / purpose |
|---|---|
| `order_id` | Order ID, Invoice, Invoice ID, Transaction ID |
| `date` | Date, Order Date, Invoice Date, Transaction Date |
| `quantity` | Quantity, Qty, Units Sold |
| `unit_price` | Unit Price, Selling Price, Price |
| `sales_amount` | Sales, Revenue, Total Sales, Total, Weekly Sales |
| `unit_cost` | Unit Cost, Cost Price, Purchase Price |
| `cost_amount` | Total Cost, COGS, Cost of Goods Sold |
| `profit_amount` | Profit, Gross Profit, Operating Profit, Gross Income |
| `discount_amount` / `discount_pct` | Discount Amount, Discount, Discount Percent |
| `refund_amount` | Refund, Return Amount, Refund Amount |
| `store` / `region` | Store, Store Number, Branch, City, Region, Area |
| `product` / `category` | Product Name, SKU, Item, Category, Department, Family |
| `customer_id` | Customer ID, Client ID, Buyer ID |
| `payment_method` | Payment Mode, Payment Type, Tender Type |

A transaction file needs a usable date field and either a sales / revenue amount or both quantity and unit price. Other fields activate additional analyses. If a dataset contains no cost or profit field, RetailPulse will still show revenue and sales views, but it will not invent profit or margin values.

## Multiple files: important scope

In this MVP, multiple files are combined as **compatible transaction exports** after each file's columns are mapped to the common retail fields. The app does not automatically join unrelated lookup tables (for example, a separate product master, store master or inventory table) using foreign keys. Those relational joins require a future data-integration layer and explicit key relationships. Files that do not contain the required transaction date and sales fields are skipped and reported.

## Calculation assumptions and limitations

- If `sales_amount` is mapped, it is treated as the line's sales value before separately supplied discounts and refunds. Otherwise revenue starts from `quantity × unit_price`.
- Discount and refund fields are subtracted from gross sales when mapped. If the source Sales field is already net of discounts or refunds, enable the checkbox on the upload page so those fields are not subtracted again.
- If a complete source `profit` field is supplied, RetailPulse uses that value as the source-defined profit measure. Some datasets label this Operating Profit or Gross Income; the source's accounting definition should be checked.
- Otherwise, calculated gross profit is `net revenue − COGS`, where COGS is derived from `quantity × unit_cost` or a complete `cost_amount` field.
- RetailPulse withholds company-wide calculated profit when costs are missing on any included row. Missing costs are not treated as zero.
- Profit margin is profit divided by net revenue. Net profit is not calculated unless operating expenses (rent, salaries, utilities, logistics, tax, etc.) are included in a future version.
- AOV is net revenue divided by distinct order IDs. If no order ID is supplied, row count is used as a clearly labelled transaction proxy.
- Diagnostic findings are rule-based signals and recommendations, not proof of business causation. To establish causes, management may need inventory, pricing, promotion, supplier, staffing, footfall and return-reason data.
- CSV / Excel data is processed in the running local app session; this MVP does not have persistent cloud storage, user accounts or multi-tenant security.

## Dataset examples that can work

RetailPulse is designed to be schema-flexible, not tied to one fixed file. Retail transaction datasets like Global Superstore, Adidas sales, Supermarket Sales, Online Retail transactions, Rossmann and Walmart weekly sales can work when the selected file contains the required date and revenue/sales fields. Additional metrics depend on the columns supplied. Forecasting or behavioral datasets without transaction dates and revenue values (for example, product-only order behavior data) are not directly analyzable as revenue dashboards without an additional data-preparation step.

## Project structure

```text
RetailPulse_Project/
└── retailpulse/
    ├── app.py
    ├── analysis_engine.py
    ├── sample_retail_transactions.csv
    ├── generate_demo_data.py
    ├── requirements.txt
    ├── run_windows.bat
    ├── README.md
    └── tests/
        └── test_analysis_engine.py
```

## Run tests

```powershell
pytest -q
```

## Next steps for a production release

Add authentication and roles, company workspaces, secure storage, audit logs, larger-file processing (DuckDB / database), explicit multi-table joins, a mapping-profile library, inventory/returns integration, forecast models and a governed AI explanation layer. Do not upload confidential company data to a public deployment until appropriate access controls and security measures are implemented.
