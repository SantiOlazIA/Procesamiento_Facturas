import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import os
import locale
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = os.path.join(os.path.dirname(__file__), "data", "output", "Analytical_Sales_Reports.xlsx")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "output")
HOME_HTML = os.path.join(OUTPUT_DIR, "Sales_Dashboard_Home.html")

# Ensure Spanish formatting for numbers
try:
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Spanish_Argentina.1252')
    except locale.Error:
        pass

def format_currency(value):
    try:
        return f"${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "$0,00"

def extract_safe_float(val):
    if pd.isna(val): return 0.0
    try: return float(val)
    except: return 0.0

# ==========================================
# CORE CSS TEMPLATE
# ==========================================
CSS_TEMPLATE = """
    <style>
        :root {
            --primary: #1F4E78;
            --secondary: #0563C1;
            --light-bg: #F8F9FA;
            --border: #E0E0E0;
            --text-dark: #2C3E50;
        }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--light-bg);
            color: var(--text-dark);
            margin: 0;
            padding: 0;
        }
        .header {
            background-color: var(--primary);
            color: white;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { margin: 0; font-weight: 800; letter-spacing: -0.5px; }
        .header p { margin: 5px 0 0 0; opacity: 0.8; font-size: 0.9em; }
        .container { padding: 30px 40px; max-width: 1600px; margin: auto; }
        
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .kpi-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-top: 4px solid var(--primary);
            transition: transform 0.2s;
        }
        .kpi-card:hover { transform: translateY(-3px); }
        .kpi-title { font-size: 0.9em; color: #7F8C8D; text-transform: uppercase; font-weight: 600; margin-bottom: 10px; }
        .kpi-value { font-size: 2.2em; font-weight: 800; color: var(--primary); margin: 0; }
        
        .charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px; }
        .single-chart-grid { display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 30px; }
        .chart-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        
        .clients-section { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .clients-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; margin-top: 15px; }
        
        .client-pill {
            background: #F1F4F8; padding: 12px 15px; border-radius: 8px; font-size: 0.9em; 
            border-left: 3px solid var(--secondary); font-weight: 600; text-decoration: none; color: inherit; display: block; transition: background 0.2s;
        }
        .client-pill:hover { background: #E2E8F0; text-decoration: none; color: var(--primary); }
        
        .nav-link { color: rgba(255,255,255,0.8); text-decoration: none; font-size: 0.9em; display: inline-flex; align-items: center; }
        .nav-link:hover { color: white; text-decoration: underline; }
        
        @media (max-width: 1024px) { .charts-grid { grid-template-columns: 1fr; } }
    </style>
"""

# ==========================================
# HOME DASHBOARD GENERATION
# ==========================================
def build_home_dashboard():
    print("Extracting KPI Data from Home Dashboard...")
    home_df = pd.read_excel(INPUT_FILE, sheet_name="Home Dashboard", header=None)

    total_gross = extract_safe_float(home_df.iloc[3, 1])
    total_net = extract_safe_float(home_df.iloc[4, 1])

    top_clients = []
    for idx in range(3, 18):
        if len(home_df) > idx and pd.notna(home_df.iloc[idx, 3]):
            client_name = str(home_df.iloc[idx, 3]).strip()
            if "." in client_name[:4]:
                client_name = client_name.split(".", 1)[1].strip()
            top_clients.append(client_name)

    print("Extracting Analytical Data...")
    data_df = pd.read_excel(INPUT_FILE, sheet_name="Analytical Data", header=None)

    start_row = 2
    years, company_totals, top15_totals = [], [], []

    for idx in range(start_row, len(data_df)):
        if pd.isna(data_df.iloc[idx, 0]) or data_df.iloc[idx, 0] == "Total": break
        year_val = data_df.iloc[idx, 0]
        if year_val == 0: continue
        years.append(int(year_val))
        company_totals.append(extract_safe_float(data_df.iloc[idx, 1]))
        top15_totals.append(extract_safe_float(data_df.iloc[idx, 2]))

    growth_df = pd.DataFrame({"Year": years, "CompanyTotal": company_totals, "Top15Total": top15_totals})
    growth_df["OthersTotal"] = growth_df["CompanyTotal"] - growth_df["Top15Total"]

    total_top15_sum = sum(top15_totals)
    total_others_sum = sum(company_totals) - total_top15_sum
    top15_perc = (total_top15_sum / sum(company_totals)) * 100 if sum(company_totals) > 0 else 0

    print("Generating Home Interactive Charts...")
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=growth_df["Year"], y=growth_df["Top15Total"], mode='lines+markers', name='Top 15 Clients', stackgroup='one', line=dict(width=2, color='#1F4E78'), fillcolor='rgba(31, 78, 120, 0.7)'))
    fig_area.add_trace(go.Scatter(x=growth_df["Year"], y=growth_df["OthersTotal"], mode='lines+markers', name='Other Clients', stackgroup='one', line=dict(width=2, color='#BFBFBF'), fillcolor='rgba(191, 191, 191, 0.5)'))
    fig_area.update_layout(title='Market Concentration Evolution (2000-2026)', xaxis_title='Financial Year', yaxis_title='Revenue ($)', hovermode='x unified', plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Inter, Roboto, sans-serif", color="#333333"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig_area.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig_area.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', tickformat="$,.0f")

    fig_donut = go.Figure(data=[go.Pie(labels=['Top 15 Clients', 'All Other Clients'], values=[total_top15_sum, total_others_sum], hole=.6, marker=dict(colors=['#1F4E78', '#BFBFBF']))])
    fig_donut.update_layout(title_text="Historical Market Share", annotations=[dict(text='Share', x=0.5, y=0.5, font_size=20, showarrow=False)], paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Inter, Roboto, sans-serif", color="#333333"))

    config_opts = {'displayModeBar': False}
    html_area_chart = pio.to_html(fig_area, full_html=False, include_plotlyjs='cdn', config=config_opts)
    html_donut_chart = pio.to_html(fig_donut, full_html=False, include_plotlyjs=False, config=config_opts)

    print("Building Home HTML...")
    html_template = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Caterwest S.A. | Executive Sales Dashboard</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">{CSS_TEMPLATE}</head><body>
    <div class="header"><div><h1>CATERWEST S.A.</h1><p>Executive Sales Dashboard | Historical Consolidation</p></div><div><span>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</span></div></div>
    <div class="container">
        <div class="kpi-grid">
            <div class="kpi-card"><div class="kpi-title">All-Time Total Revenue (Gross)</div><div class="kpi-value">{format_currency(total_gross)}</div></div>
            <div class="kpi-card"><div class="kpi-title">All-Time Net Revenue</div><div class="kpi-value">{format_currency(total_net)}</div></div>
            <div class="kpi-card"><div class="kpi-title">Top 15 Historical Weight</div><div class="kpi-value">{top15_perc:.1f}%</div></div>
        </div>
        <div class="charts-grid"><div class="chart-card">{html_area_chart}</div><div class="chart-card">{html_donut_chart}</div></div>
        <div class="clients-section"><h3 style="margin-top: 0; color: var(--primary);">Top 15 Corporate Portfolios</h3><div class="clients-grid">
            {''.join([f'<a href="Client_{i+1}.html" class="client-pill">{i+1}. {client} &rarr;</a>' for i, client in enumerate(top_clients)])}
        </div></div>
    </div></body></html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(HOME_HTML, "w", encoding="utf-8") as f: f.write(html_template)
    print(f"-> Home Dashboard generated: {os.path.basename(HOME_HTML)}")
    return top_clients

# ==========================================
# CLIENT DASHBOARD GENERATION
# ==========================================
def build_client_dashboards(top_clients):
    xls = pd.ExcelFile(INPUT_FILE)
    
    for i, client_name in enumerate(top_clients):
        sheet_name = f"Client_{i+1}"
        if sheet_name not in xls.sheet_names:
            print(f"[Warning] {sheet_name} not found in Excel file.")
            continue
            
        print(f"Building {sheet_name} ({client_name})...")
        client_df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name, header=None)
        
        gross_kpi = extract_safe_float(client_df.iloc[3, 1])
        net_kpi = extract_safe_float(client_df.iloc[4, 1])
        
        years, gross_arr, net_arr = [], [], []
        # Timeline data historically starts around row 45 (or whenever year numbers start)
        for idx in range(30, len(client_df)):
            y_val = client_df.iloc[idx, 0]
            if pd.isna(y_val) or str(y_val).strip() == "Total" or str(y_val).strip().isalpha(): 
                continue # Header row or empty
            
            # Look for 4 digit years
            try:
                yr = int(y_val)
                if yr > 1990 and yr < 2100:
                    years.append(yr)
                    gross_arr.append(extract_safe_float(client_df.iloc[idx, 1]))
                    net_arr.append(extract_safe_float(client_df.iloc[idx, 2]))
            except ValueError:
                continue

        # Build Bar/Line Chart
        fig_client = go.Figure()
        fig_client.add_trace(go.Bar(x=years, y=gross_arr, name='Total Revenue (Gross)', marker_color='#BFBFBF'))
        fig_client.add_trace(go.Scatter(x=years, y=net_arr, mode='lines+markers', name='Net Revenue (Excl. IVA)', line=dict(color='#1F4E78', width=3)))
        
        fig_client.update_layout(title=f'Historical Performance: {client_name}', xaxis_title='Financial Year', yaxis_title='Revenue ($)', hovermode='x unified', plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Inter, Roboto, sans-serif", color="#333333"))
        fig_client.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig_client.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', tickformat="$,.0f")
        
        config_opts = {'displayModeBar': False}
        html_chart = pio.to_html(fig_client, full_html=False, include_plotlyjs='cdn', config=config_opts)

        html_template = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{client_name} | Portfolio</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">{CSS_TEMPLATE}</head><body>
        <div class="header"><div><h1>PORTFOLIO: {client_name}</h1><p>Client Historical Performance</p></div>
        <div><a href="Sales_Dashboard_Home.html" class="nav-link">&larr; Back to Home Dashboard</a></div></div>
        <div class="container">
            <div class="kpi-grid">
                <div class="kpi-card"><div class="kpi-title">Client Lifetime Revenue (Gross)</div><div class="kpi-value">{format_currency(gross_kpi)}</div></div>
                <div class="kpi-card" style="border-color: var(--secondary);"><div class="kpi-title">Client Lifetime Net (Excl. IVA)</div><div class="kpi-value" style="color: var(--secondary);">{format_currency(net_kpi)}</div></div>
            </div>
            <div class="single-chart-grid"><div class="chart-card">{html_chart}</div></div>
        </div></body></html>"""

        client_html = os.path.join(OUTPUT_DIR, f"{sheet_name}.html")
        with open(client_html, "w", encoding="utf-8") as f: f.write(html_template)
        
# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    print(f"Starting Multi-Page HTML Generation...\n{'-'*40}")
    top_clients = build_home_dashboard()
    print(f"{'-'*40}\nStarting Client Dashboards...")
    build_client_dashboards(top_clients)
    print(f"{'-'*40}\nSUCCESS: All dashboards generated natively.")
