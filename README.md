# 📊 AI Data & Business Intelligence Assistant

An end-to-end Text-to-SQL query generator and interactive Business Intelligence dashboard. This application allows users to converse with their SQL databases or custom CSV files using natural language. 

Powered by **Google Gemini 2.5 Flash**, the app instantly translates business questions into valid SQL queries, executes them, and automatically visualizes the results with dynamic charts.

## ✨ Features

* **🗣️ Natural Language to SQL:** Ask complex business questions in plain English and let the AI write the SQLite queries.
* **📈 Dynamic Data Visualization:** Automatically generates the best Plotly charts (Bar, Pie, Line, Treemap, or Heatmap) based on the query results.
* **📂 Custom CSV Upload:** Don't want to use the default database? Upload your own CSV file to instantly generate a temporary database and chat with your own data.
* **📄 Executive PDF Reports:** Download your query results, AI-generated business insights, and recommendations in a beautifully formatted PDF report.
* **📱 Automated Dashboard Builder:** Simply type "Build me a Sales Dashboard" to instantly generate a comprehensive, multi-chart view of your key metrics.

## 🛠️ Tech Stack

* **Frontend & UI:** [Streamlit](https://streamlit.io/)
* **LLM & AI Insights:** [Google Gemini API (2.5 Flash)](https://ai.google.dev/)
* **Database:** SQLite & Pandas
* **Data Visualization:** [Plotly](https://plotly.com/python/)
* **Reporting:** FPDF

## 📁 File Structure

```text
ai-business-intelligence-assistant/
│
├── app.py                # The main Streamlit application script
├── database.py           # Script to create and populate the initial database
├── test.py               # Testing and debugging script
├── requirements.txt      # List of all required Python dependencies
├── .env.example          # Template for your environment variables
├── .gitignore            # Files and folders ignored by Git    
└── README.md             # Project documentation (you are here!)
```






## 🚀 Installation & Setup

Follow these steps to get the project running locally on your machine.

### 1. Clone the Repository
Open your terminal and run the following commands to download the code:
```bash
git clone [https://github.com/YOUR_GITHUB_USERNAME/ai-business-intelligence-assistant.git](https://github.com/YOUR_GITHUB_USERNAME/ai-business-intelligence-assistant.git)
cd ai-business-intelligence-assistant
```
*(Note: Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username).*

### 2. Install Dependencies
Install all required Python libraries using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 3. Set Up Your API Key
This application requires a free Google Gemini API key to generate SQL queries and insights.
1. Get your free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Create a new file in your main project folder named cutely **`.env`**.
3. Paste your API key into this file using the format below:
```env
GOOGLE_API_KEY="your_actual_api_key_here"
```

### 4. Initialize the Database
If you want to use the default sample database (instead of uploading your own CSV), run the setup script to generate the tables:
```bash
python database.py
```

### 5. Run the Application
Launch the Streamlit dashboard in your web browser:
```bash
streamlit run app.py
```
