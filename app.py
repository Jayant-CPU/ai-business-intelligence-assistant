from dotenv import load_dotenv
import streamlit as st
import os
import sqlite3
import pandas as pd
import plotly.express as px
import time
from google import genai
import io

# ==========================================
# Install FPDF for Feature 6
# ==========================================
try:
    from fpdf import FPDF
except ImportError:
    st.error("Please install FPDF to use the PDF generator: pip install fpdf")

# ==========================================
# Initialize Session States 
# ==========================================
if "history" not in st.session_state:
    st.session_state.history = []

if "app_state" not in st.session_state:
    st.session_state.app_state = {
        "mode": None,  
        "question": None,
        "sql": None,
        "result_df": None,
        "insights": None,
        "elapsed": 0
    }

# ==========================================
# Load API Key
# ==========================================
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# ==========================================
# Gemini Function
# ==========================================
def get_gemini_response(question, prompt):
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=f"{prompt}\n\nQuestion: {question}"
    )
    return response.text.strip()

# ==========================================
# Execute SQL (Supports Custom DB)
# ==========================================
def run_sql_query(sql, db_path="business.db"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

# ==========================================
# AI Business Insights
# ==========================================
def get_business_insights(df):
    prompt = f"""
You are a Senior Data Analyst.
Analyze the following query result.
Return your response in Markdown.
Use exactly this format:

## 📌 Key Insights
- Insight 1
- Insight 2
- Insight 3

## 💡 Recommendation
One actionable recommendation based on the data.

Keep the response concise (under 120 words).
Data:
{df.head(20).to_markdown(index=False)}
"""
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )
    return response.text

# ==========================================
# KPI Function
# ==========================================
def get_kpis():
    conn = sqlite3.connect("business.db")
    try:
        revenue = pd.read_sql_query("SELECT ROUND(SUM(sales),2) AS revenue FROM Orders", conn).iloc[0,0]
        orders = pd.read_sql_query("SELECT COUNT(*) AS orders FROM Orders", conn).iloc[0,0]
        customers = pd.read_sql_query("SELECT COUNT(*) AS customers FROM Customers", conn).iloc[0,0]
        products = pd.read_sql_query("SELECT COUNT(*) AS products FROM Products", conn).iloc[0,0]
    except:
        revenue, orders, customers, products = 0, 0, 0, 0
    conn.close()
    return revenue, orders, customers, products

# ==========================================
# PDF Generator Function
# ==========================================
def generate_pdf_report(question, sql, insights):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Executive Data Report", ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Data Question: {question}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="AI Insights & Recommendations:", ln=1)
    pdf.set_font("Arial", size=11)
    clean_insights = insights.replace("📌", "*").replace("💡", "*").encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_insights)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Generated SQL Query:", ln=1)
    pdf.set_font("Courier", size=10)
    clean_sql = sql.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, txt=clean_sql)
    
    try:
        return pdf.output(dest='S').encode('latin-1')
    except:
        return bytes(pdf.output())

# ==========================================
# Dynamic Gemini Prompts
# ==========================================
DEFAULT_PROMPT = """
You are an expert SQLite developer.
Convert the user's question into a valid SQLite query.

Database Schema:
Customers(customer_id, state, country)
Categories(category_id, category_name)
Products(product_id, product_name, category_id)
Orders(order_id, order_date, customer_id, product_id, quantity, unit_price, sales, payment_method, delivery_status, rating, review)

Rules:
1. Return ONLY SQL.
2. Do not explain.
3. Do not use markdown.
4. Never use ```sql.
5. Use SQLite syntax only.
6. Use JOIN whenever required.
7. Revenue = SUM(sales)
8. Use GROUP BY for aggregations and ORDER BY DESC for ranking.
9. Use LIMIT whenever user asks Top N.
"""

def get_custom_prompt(columns_list):
    return f"""
You are an expert SQLite developer.
Convert the user's question into a valid SQLite query.

Database Schema:
Table Name: custom_table
Columns: {', '.join(columns_list)}

Rules:
1. Return ONLY SQL.
2. Do not explain.
3. Do not use markdown.
4. Never use ```sql.
5. Use SQLite syntax only.
6. ONLY query the 'custom_table' table.
"""

# ==========================================
# Streamlit Page & CSS
# ==========================================
st.set_page_config(page_title="AI Data Assistant", page_icon="📊", layout="wide")
st.markdown("""
<style>
/* ===============================
   MAIN APP BACKGROUND & SIDEBAR
==================================*/
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; }
.main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
[data-testid="stSidebar"] { background-color: #0b0f19 !important; border-right: 1px solid rgba(255, 255, 255, 0.05); }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
h1, h2, h3, h4, h5, h6, p, label, span { color: #f8fafc !important; }

/* ===============================
   METRIC CARDS
==================================*/
div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: all 0.3s ease; }
div[data-testid="stMetric"]:hover { transform: translateY(-3px); border: 1px solid rgba(255, 255, 255, 0.2); }
div[data-testid="stMetric"] label, div[data-testid="stMetric"] div { color: #f8fafc !important; }

/* ===============================
   INLINE CODE (SIDEBAR TEXT)
==================================*/
code {
    color: #60a5fa !important;
    background-color: rgba(255, 255, 255, 0.1) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}

/* ===============================
   EXPANDERS (DATABASE SCHEMA)
==================================*/
[data-testid="stExpander"] { background-color: transparent !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 8px !important; }
[data-testid="stExpander"] summary { background-color: rgba(255, 255, 255, 0.05) !important; border-radius: 8px !important; }
[data-testid="stExpander"] summary:hover { background-color: rgba(255, 255, 255, 0.1) !important; }
[data-testid="stExpander"] summary p { color: #ffffff !important; font-weight: 600 !important; }
[data-testid="stExpander"] div[role="region"] { background-color: transparent !important; }

/* ===============================
   FIX: FILE UPLOADER (CSV)
==================================*/
[data-testid="stFileUploader"] { background-color: transparent !important; }
[data-testid="stFileUploaderDropzone"] { 
    background-color: #0f172a !important; 
    border: 1px dashed #3b82f6 !important; 
    border-radius: 8px !important; 
}
[data-testid="stFileUploaderDropzone"]:hover {
    background-color: rgba(59, 130, 246, 0.1) !important;
}
[data-testid="stFileUploaderDropzone"] * { 
    color: #f8fafc !important; 
}
[data-testid="stFileUploaderDropzone"] button {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

/* ===============================
   BUTTONS
==================================*/
.stButton > button { width: 100% !important; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; color: white !important; border: none !important; border-radius: 8px !important; padding: 0.5rem 1rem !important; font-weight: 600 !important; transition: all 0.3s ease !important; }
.stButton > button:hover { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; transform: translateY(-1px) !important; }

/* ===============================
   DOWNLOAD BUTTONS
==================================*/
.stDownloadButton > button { width: 100% !important; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; padding: 0.5rem 1rem !important; font-weight: 600 !important; transition: all 0.3s ease !important; }
.stDownloadButton > button * { color: #ffffff !important; }
.stDownloadButton > button:hover { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; transform: translateY(-1px) !important; }

/* ===============================
   INSIGHTS/ALERT BOXES
==================================*/
[data-testid="stAlert"] { background-color: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
[data-testid="stAlert"] * { color: #ffffff !important; }

/* ===============================
   TEXT INPUT
==================================*/
.stTextInput input { background-color: #0f172a !important; color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 8px !important; }
.stTextInput input:focus { border-color: #3b82f6 !important; box-shadow: 0 0 0 1px #3b82f6 !important; }
.stTextInput input::placeholder { color: #94a3b8 !important; }

/* ===============================
   MISC FIXES
==================================*/
[data-testid="stHeader"] { background-color: transparent !important; }
[data-testid="stDataFrame"], [data-testid="stChart"] { background: rgba(255, 255, 255, 0.02); border-radius: 12px; padding: 10px; border: 1px solid rgba(255, 255, 255, 0.05); }
.stSelectbox { color: black; }
hr { border: 1px solid rgba(255, 255, 255, 0.1); margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# Sidebar 
# ==========================================
with st.sidebar:
    st.header("📊 AI Data Assistant")
    st.divider()
    
    # --- NEW FEATURE: CSV UPLOAD ---
    st.markdown("### 💾 Use Your Own Data")
    uploaded_file = st.file_uploader("Upload a CSV file to analyze:", type=["csv"])
    
    is_custom_data = False
    custom_columns = []
    custom_row_count = 0
    
    if uploaded_file is not None:
        try:
            # Read CSV and create a temporary SQLite Database
            df_custom = pd.read_csv(uploaded_file)
            conn_temp = sqlite3.connect("temp_upload.db")
            df_custom.to_sql("custom_table", conn_temp, if_exists="replace", index=False)
            conn_temp.close()
            
            is_custom_data = True
            custom_columns = df_custom.columns.tolist()
            custom_row_count = len(df_custom)
            st.success("✅ File loaded successfully!")
        except Exception as e:
            st.error(f"Error loading file: {e}")
    
    st.divider()

    with st.expander("📂 Database Schema"):
        if is_custom_data:
            st.markdown(f"**📑 custom_table**\n`{'`, `'.join(custom_columns)}`")
        else:
            st.markdown("""
            **📦 Orders**
            `order_id`, `order_date`, `quantity`, `sales`, `payment_method`, `rating`, `delivery_status`
            **👥 Customers**
            `customer_id`, `state`, `country`
            **🛍 Products**
            `product_id`, `product_name`, `category_id`
            **📑 Categories**
            `category_id`, `category_name`
            """)

    with st.expander("⚙️ Preferences"):
        show_sql_pref = st.checkbox("Show SQL Queries", value=True)
        enable_insights_pref = st.checkbox("Enable AI Insights", value=True)

    st.divider()
    st.markdown("### Recent Queries")
    if st.button("🗑 Clear History", use_container_width=True):
        st.session_state.history = []
        st.session_state.app_state["mode"] = None
        st.rerun()

    for q in st.session_state.history[-5:]:
        st.caption(f"• {q}")

# ==========================================
# Main UI
# ==========================================
if is_custom_data:
    st.title(f"📊 AI Data Assistant: {uploaded_file.name}")
else:
    st.title("📊 AI Business Intelligence Assistant")

st.markdown("Analyze your data using natural language. Just ask a question and let the AI generate queries, charts, and insights.")

# --- DYNAMIC METRICS ---
col1, col2, col3, col4 = st.columns(4)

if is_custom_data:
    # Custom File Metrics
    col1.metric("📄 Total Rows", f"{custom_row_count:,}")
    col2.metric("🔢 Total Columns", f"{len(custom_columns)}")
    col3.metric("🗂 Active Table", "custom_table")
    col4.metric("💾 File Type", "CSV")
else:
    # Standard DB Metrics
    revenue, orders, customers, products = get_kpis()
    col1.metric("💰 Revenue", f"₹{revenue:,.2f}")
    col2.metric("📦 Orders", f"{orders:,}")
    col3.metric("👥 Customers", f"{customers:,}")
    col4.metric("🛍 Products", f"{products:,}")

question = st.text_input(
    "Data Question",
    placeholder="What would you like to know about the data?"
)

# ==========================================
# Data Fetching Logic 
# ==========================================
if st.button("Generate Insights"):
    if question == "":
        st.warning("Please enter a question.")
    elif question.lower().strip() == "build me a sales dashboard" and not is_custom_data:
        st.session_state.history.append(question)
        st.session_state.app_state["mode"] = "dashboard"
    elif question.lower().strip() == "build me a sales dashboard" and is_custom_data:
        st.warning("Dashboard Builder is only configured for the default Business Database.")
    else:
        try:
            active_prompt = get_custom_prompt(custom_columns) if is_custom_data else DEFAULT_PROMPT
            db_target = "temp_upload.db" if is_custom_data else "business.db"

            with st.spinner("🤖 Generating SQL using Gemini..."):
                sql = get_gemini_response(question, active_prompt).replace("```sql", "").replace("```", "").strip()

            start = time.time()
            with st.spinner("📊 Running SQL Query..."):
                result = run_sql_query(sql, db_target)
            elapsed = time.time() - start
            
            insights = None
            if enable_insights_pref:
                try:
                    with st.spinner("🧠 Analyzing business data..."):
                        insights = get_business_insights(result)
                except Exception:
                    insights = "⚠️ Could not generate AI insights due to Gemini API limits."

            # Save to session state
            st.session_state.history.append(question)
            st.session_state.app_state = {
                "mode": "query",
                "question": question,
                "sql": sql,
                "result_df": result,
                "insights": insights,
                "elapsed": elapsed
            }
        except Exception as e:
            if "no such table" in str(e).lower():
                st.error("Error: The AI generated an incorrect table name. Try rephrasing your question.")
            elif "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                st.error("⚠️ Gemini API quota exceeded. Please try again later or use a different API key.")
            else:
                st.error(f"Error executing query: {e}")

# ==========================================
# Display Logic
# ==========================================
state = st.session_state.app_state

if state["mode"] == "dashboard":
    st.success("✅ Automatically generated Sales Dashboard.")
    try:
        df_states = run_sql_query("SELECT state, SUM(sales) as Revenue FROM Customers c JOIN Orders o ON c.customer_id = o.customer_id GROUP BY state ORDER BY Revenue DESC LIMIT 5")
        df_cats = run_sql_query("SELECT category_name, SUM(sales) as Revenue FROM Categories c JOIN Products p ON c.category_id = p.category_id JOIN Orders o ON p.product_id = o.product_id GROUP BY category_name ORDER BY Revenue DESC LIMIT 5")
        df_monthly = run_sql_query("SELECT SUBSTR(order_date, 1, 7) as Month, SUM(sales) as Revenue FROM Orders GROUP BY Month ORDER BY Month")
        df_payment = run_sql_query("SELECT payment_method, COUNT(*) as Count FROM Orders GROUP BY payment_method")

        dash_col1, dash_col2 = st.columns(2)
        with dash_col1:
            st.plotly_chart(px.bar(df_states, x="state", y="Revenue", title="Top States by Revenue", color="state"), use_container_width=True)
            st.plotly_chart(px.line(df_monthly, x="Month", y="Revenue", title="Monthly Sales", markers=True), use_container_width=True)
        with dash_col2:
            st.plotly_chart(px.pie(df_cats, names="category_name", values="Revenue", title="Top Categories by Revenue", hole=0.4), use_container_width=True)
            st.plotly_chart(px.pie(df_payment, names="payment_method", values="Count", title="Payment Method Breakdown"), use_container_width=True)
    except Exception as e:
        st.error(f"Error generating dashboard: {e}")

elif state["mode"] == "query":
    result = state["result_df"]
    
    if show_sql_pref:
        with st.expander("📝 View Generated SQL"):
            st.code(state["sql"], language="sql")

    st.subheader("Query Result")
    st.dataframe(result, width="stretch")

    # --- Chart Selector ---
    numeric_cols = result.select_dtypes(include="number").columns.tolist()

    if len(numeric_cols) > 0 and len(result.columns) > 1:
        y = numeric_cols[-1]
        categorical_cols = [c for c in result.columns if c != y]
        
        chart_type = st.selectbox(
            "📊 Choose Visualization Style", 
            ["Auto (Default)", "Bar", "Pie", "Line", "Treemap", "Heatmap"]
        )

        if chart_type == "Auto (Default)":
            if len(result.columns) == 2:
                x = categorical_cols[0]
                is_date = ("date" in x.lower() or "month" in x.lower() or "year" in x.lower())
                if is_date:
                    fig = px.line(result, x=x, y=y, markers=True, title=f"{y.title()} over {x.title()}")
                elif len(result) > 10:
                    fig = px.bar(result, x=y, y=x, orientation="h", title=f"{y.title()} by {x.title()}")
                else:
                    fig = px.bar(result, x=x, y=y, title=f"{y.title()} by {x.title()}")
                st.plotly_chart(fig, use_container_width=True)
                
                if len(result) <= 12 and (result[y] >= 0).all():
                    st.plotly_chart(px.pie(result, names=x, values=y, hole=0.45), use_container_width=True)

            elif len(result.columns) == 3:
                x = categorical_cols[1]
                color = categorical_cols[0]
                st.plotly_chart(px.bar(result, x=x, y=y, color=color, barmode="group", title=f"{y.title()} by {x.title()}"), use_container_width=True)
                
                heat = result.pivot_table(values=y, index=color, columns=x, aggfunc="sum").fillna(0)
                st.plotly_chart(px.imshow(heat, text_auto=True, aspect="auto", title="Heatmap"), use_container_width=True)

            elif len(result.columns) > 3:
                st.info("Multiple columns detected.")
                st.plotly_chart(px.scatter_matrix(result, dimensions=numeric_cols, title="Relationship Between Numeric Columns"), use_container_width=True)
        else:
            x_col = categorical_cols[0] if categorical_cols else result.columns[0]
            if chart_type == "Bar":
                fig = px.bar(result, x=x_col, y=y, title=f"{y.title()} by {x_col.title()}")
            elif chart_type == "Pie":
                if (result[y] >= 0).all():
                    fig = px.pie(result, names=x_col, values=y, title=f"{y.title()} Distribution", hole=0.3)
                else:
                    st.warning("Pie charts cannot display negative values.")
                    fig = px.bar(result, x=x_col, y=y, title=f"{y.title()} by {x_col.title()}")
            elif chart_type == "Line":
                fig = px.line(result, x=x_col, y=y, title=f"{y.title()} Trend", markers=True)
            elif chart_type == "Treemap":
                if (result[y] >= 0).all():
                    fig = px.treemap(result, path=[x_col], values=y, title=f"{y.title()} Hierarchy")
                else:
                    st.warning("Treemaps cannot display negative values.")
                    fig = px.bar(result, x=x_col, y=y, title=f"{y.title()} by {x_col.title()}")
            elif chart_type == "Heatmap":
                fig = px.density_heatmap(result, x=x_col, y=y, title=f"{y.title()} Heatmap")
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough categorical/numeric columns available for visualization.")

    st.caption(f"⏱️ Execution Time: {state['elapsed']:.3f} sec")
    st.success(f"{len(result)} rows returned.")
    
    if state["insights"]:
        st.markdown("## 🤖 AI Business Insights")
        if "⚠️" in state["insights"]:
            st.warning(state["insights"])
        else:
            st.info(state["insights"])

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(label="📥 Download Result as CSV", data=result.to_csv(index=False), file_name="query_result.csv", mime="text/csv")
        
    with dl_col2:
        try:
            pdf_bytes = generate_pdf_report(
                state["question"], 
                state["sql"], 
                state["insights"] if state["insights"] else "AI Insights disabled by user."
            )
            st.download_button(label="📄 Download Executive Report", data=pdf_bytes, file_name="Executive_Report.pdf", mime="application/pdf")
        except Exception as e:
            st.error("Report generation failed. Ensure FPDF is installed.")

st.divider()
st.caption("Built with ❤️ using Streamlit • Gemini • SQLite • Plotly")
