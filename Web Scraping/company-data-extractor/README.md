🔍 Company Data Extractor
=========================

This project is a **data extraction and analysis tool** that:

-   Finds company domains & LinkedIn profiles via **SerpAPI**

-   Scrapes company websites for content

-   Analyzes the content with **OpenAI GPT models** to extract key business information

-   Stores results in a **SQLite database**

-   Provides a **Streamlit web app** for easy interaction and visualization

* * * * *

✨ Features
----------

-   ✅ **Search via SerpAPI** → Finds company websites & LinkedIn pages

-   ✅ **Web scraping** → Extracts text content from company websites

-   ✅ **AI-powered analysis** → Uses OpenAI to identify pricing models, free trials, enterprise plans, API availability, and target market (B2B/B2C)

-   ✅ **SQLite storage** → Stores company name, domain, LinkedIn, analysis, and timestamp locally

-   ✅ **Streamlit dashboard** → User-friendly UI for searching and exploring results

* * * * *

📂 Project Structure
--------------------

`.
├── app.py                 # Main application (Streamlit + Prefect flow)
├── company_data.db        # SQLite database (auto-created)
├── requirements.txt       # Dependencies
├── .env                   # API keys (not committed)
└── README.md              # Documentation`

* * * * *

⚙️ Installation
---------------

1.  **Clone the repository**

`git clone https://github.com/your-username/company-data-extractor.git
cd company-data-extractor`

1.  **Create a virtual environment**

`python3 -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows`

1.  **Install dependencies**

`pip install -r requirements.txt`

* * * * *

🔑 Environment Variables
------------------------

Create a `.env` file in the project root with the following:

`SERP_API_KEY=your_serpapi_key
OPENAI_API_KEY=your_openai_key`

-   Get a **SerpAPI key**: https://serpapi.com/

-   Get an **OpenAI API key**: <https://platform.openai.com/>

* * * * *

🗃 Database
-----------

The app uses a **SQLite database** (`company_data.db`) stored in the project directory.

**Table schema (`companies`)**:

| Column | Type | Description |
| --- | --- | --- |
| `id` | INTEGER | Auto-increment primary key |
| `company_name` | TEXT | Company name entered by the user |
| `domain` | TEXT | Company website domain |
| `linkedin_url` | TEXT | Company LinkedIn page (if found) |
| `analysis` | TEXT | JSON analysis result from OpenAI |
| `timestamp` | REAL | UNIX timestamp of when the record was created |

* * * * *

🚀 Usage
--------

### Run the Streamlit app

`streamlit run app.py`

### Workflow

1.  Enter a company name (e.g., **Stripe**) in the search box

2.  The app will:

    -   Search SerpAPI for the company's domain & LinkedIn

    -   Scrape the website content

    -   Analyze with OpenAI GPT

    -   Store the results in SQLite

3.  Results are displayed in the UI, and you can view previously processed companies

* * * * *

📊 Example Output
-----------------

**Input**:

`Stripe`

**Output (JSON analysis):**

`{
  "cheapest_plan": "$0/month (Starter)",
  "free_trial": "Not mentioned",
  "enterprise_plan": "Yes",
  "api_availability": "Yes",
  "market_type": "B2B"
}`

* * * * *

🛠 Tech Stack
-------------

-   [**Python**](https://www.python.org/)

-   **Streamlit** -- UI

-   **Prefect** -- Workflow orchestration

-   **SerpAPI** -- Search API

-   **BeautifulSoup4** -- Web scraping

-   [**OpenAI API**](https://platform.openai.com/) -- AI analysis

-   **SQLite** -- Database
