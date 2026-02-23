# Directives: Vtas CW Project (Integrated Edition)

## 1. Project Objective
Consolidate 25+ years of CATERWEST S.A. sales data (2000–2026) into a validated, deduplicated, and chronologically sorted "All-Sales Report". Generate a corporate-grade interactive analytical dashboard with individual client portfolios.

---

## 2. Core Data Integrity Rules
Every data processing step MUST adhere to these technical constraints:

### Data Transformation & Filtering
- **Row Elimination**: Remove rows where `|Total| < 0.01` or Razon Social contains "ANULADO".
- **Negative N/C Policy**: Credit Notes MUST have negative signs in numeric columns and red font styling for accurate balance summation.
- **Traceability**: All rows must include a `Ref. Origen` column mapping to `File | Sheet | Row`.
- **Deduplication**: Use a composite key `[Date, CUIT, Comprobante, Total]` to prevent overlaps between consolidated and monthly files.

### Validation Audit Control
Every execution must log:
1. **Total Sum Verification**: Consolidation sum vs. original sum (delta < $0.05).
2. **Row Count Match**: Trace total row count back to original file contributions.
3. **Eliminated Rows Report**: Explicit list of every deleted row (File/Sheet/Row/Reason).

---

## 3. Premium Reporting Architecture (17-Sheet System)
The "Analytical Sales Report" must follow this strictly synchronized structure:

### Sheet 1: [Home Dashboard]
- **Executive Navigation**: Table of 15 clickable hyper-links directing to individual client sheets.
- **Global KPIs**: Centered boxes for All-time Total Revenue and All-time Net Revenue (sin IVA).
- **Market Concentration**: Area chart showing "Top 15 Share" vs. "Others" as a market evolution.

### Sheet 2: [Analytical Data Asset]
- **Storage Layer**: Centralized tables powering all charts (Concentration, Yearly Total, Yearly Net).
- **Formatting**: Must match premium aesthetics even if it's a data sheet (Borders, Headers, Centering).

### Sheets 3-17: [Individual Client Portfolios]
- **Name**: `Client_N` for navigation stability.
- **Header**: Centered title `PORTFOLIO ANALYSIS: [Full Client Name]`.
- **Navigation**: "Back to Home Dashboard" link in cell A2.
- **Visual Asset**: Large high-resolution dual-metric chart (Net vs. Gross) positioned below KPIs.

---

## 4. Visual & Aesthetic Technical Standards
To ensure professional, executive-ready presentation, these rules are **MANDATORY**:

### Geometric Alignment
- **Global Centering**: Apply `Alignment(horizontal="center", vertical="center")` to ALL data cells, headers, and KPI boxes.
- **Professional Borders**: Thin borders (`Side(style='thin')`) for every data table and KPI summary.
- **Zero Overlap**: Maintain at least a 2-row buffer between text/tables and chart borders. Charts should start below KPI boxes (~Row 8).

### Column & Row Optimization
- **Intelligent Auto-Fit**: Adjust column widths dynamically based on `max(len(content))`.
- **Width Capping**: Cap column width at **40 characters** to prevent visual outliers from breaking the layout.
- **Gridline Policy**: `ws.sheet_view.showGridLines = False` for all presentation and portfolio sheets.

---

## 5. Financial Calculation & Formatting
- **Dual Metric Policy**: Every Sales chart/table MUST show **Total Sales** and **Net Sales (sin IVA)** side-by-side.
- **Regional Formatting**: Enforce the Spanish standard: **points for thousands** (`#.##0,00`).
- **Axis Clarity**: Numerical axes must be **visible** on all charts.
- **Precision Scale**: Use a major unit of **$1,000** for chart gridlines to allow surgical data reading.

---

## 6. Corporate Color Palette
- **Primary Headers**: Deep Blue (`1F4E78`) background, White Font, Bold.
- **Borders**: Subtle Grey (`BFBFBF`) for thin internal borders.
- **Links**: Standard Web Blue (`0563C1`) with single underline for navigation.
