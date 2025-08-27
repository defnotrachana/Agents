from prefect import flow, task
import requests
from serpapi.google_search import GoogleSearch
from bs4 import BeautifulSoup
import openai
import sqlite3
import os
import streamlit as st
from dotenv import load_dotenv
import logging
from urllib.parse import urlparse
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize SQLite database
def init_database():
    conn = sqlite3.connect('/workspace/company_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            domain TEXT,
            linkedin_url TEXT,
            analysis TEXT,
            timestamp REAL
        )
    ''')
    conn.commit()
    conn.close()

@task(retries=2, retry_delay_seconds=2)
def search_serpapi(company_name):
    """Search for company information using SerpAPI"""
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        raise ValueError("SERP_API_KEY not found in environment variables")
    
    params = {
        "q": company_name,
        "api_key": api_key,
        "num": 5
    }

    try:
        response = GoogleSearch(params).get_dict()
        results = response.get("organic_results", [])
        
        if not results:
            raise ValueError(f"No results found for: {company_name}")

        domain = None
        linkedin_url = None
        
        for result in results:
            link = result.get("link", "")
            
            if "linkedin.com/company/" in link and not linkedin_url:
                linkedin_url = link
            elif not domain:
                parsed_url = urlparse(link)
                skip_domains = ['wikipedia.org', 'facebook.com', 'twitter.com']
                if not any(skip in parsed_url.netloc for skip in skip_domains):
                    domain = link

        if not domain:
            domain = results[0].get("link", "")  # Fallback to first result

        return {
            "linkedin_url": linkedin_url, 
            "domain": domain,
            "company_name": company_name
        }

    except Exception as e:
        logger.error(f"SerpAPI error: {e}")
        raise

@task(retries=2)
def scrape_website(domain):
    """Scrape website content"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(domain, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()
            
        return soup
        
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        raise

@task
def analyze_content(soup, company_name):
    """Analyze content using OpenAI"""
    text_content = soup.get_text()
    
    # Limit content to avoid token limits
    if len(text_content) > 6000:
        text_content = text_content[:6000] + "..."
    
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    Extract these details from {company_name}'s website and return as JSON:
    
    {{
        "cheapest_plan": "price or 'Not found'",
        "free_trial": "Yes/No/Not mentioned",
        "enterprise_plan": "Yes/No/Not mentioned",
        "api_availability": "Yes/No/Not mentioned",
        "market_type": "B2B/B2C/Not clear"
    }}
    
    Content: {text_content[:3000]}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract company info as JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return f'{{"error": "Analysis failed: {str(e)}"}}'

@task
def store_to_sqlite(data):
    """Store data to SQLite"""
    try:
        conn = sqlite3.connect('/workspace/company_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO companies (company_name, domain, linkedin_url, analysis, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['company_name'],
            data['domain'],
            data.get('linkedin_url'),
            data['analysis'],
            time.time()
        ))
        
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        
        return str(row_id)
        
    except Exception as e:
        logger.error(f"SQLite error: {e}")
        raise

@flow(name="company-extraction")
def extract_company_data(company_name):
    """Main extraction workflow"""
    try:
        # Search
        search_results = search_serpapi(company_name)
        
        # Scrape
        soup = scrape_website(search_results["domain"])
        
        # Analyze
        analysis = analyze_content(soup, company_name)
        
        # Prepare data
        data = {
            "company_name": company_name,
            "domain": search_results["domain"],
            "linkedin_url": search_results.get("linkedin_url"),
            "analysis": analysis
        }
        
        # Store
        record_id = store_to_sqlite(data)
        
        return {"success": True, "data": data, "id": record_id}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_stored_companies():
    """Get all stored companies from SQLite"""
    try:
        conn = sqlite3.connect('/workspace/company_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT company_name, domain, timestamp FROM companies ORDER BY timestamp DESC')
        companies = cursor.fetchall()
        conn.close()
        return companies
    except:
        return []

def main():
    """Streamlit app"""
    st.set_page_config(page_title="Company Extractor", page_icon="🔍")
    
    # Initialize database
    init_database()
    
    st.title("🔍 Company Data Extractor")
    
    # Check environment variables
    missing_vars = []
    if not os.getenv("SERP_API_KEY"):
        missing_vars.append("SERP_API_KEY")
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
    
    if missing_vars:
        st.error(f"❌ Missing: {', '.join(missing_vars)}")
        st.info("Create a .env file with your API keys")
        st.code("""
SERP_API_KEY=your_serpapi_key
OPENAI_API_KEY=your_openai_key
        """)
        return
    
    st.success("✅ Environment configured correctly")
    st.info("💾 Using SQLite database (no MongoDB required)")
    
    # Show previously processed companies
    stored_companies = get_stored_companies()
    if stored_companies:
        with st.expander(f"📊 Previously processed ({len(stored_companies)} companies)"):
            for company, domain, timestamp in stored_companies[:5]:  # Show last 5
                st.write(f"• **{company}** - {domain}")
    
    company_name = st.text_input("Enter company name:", placeholder="e.g., Stripe, Notion, Shopify")
    
    if st.button("Extract Data", type="primary"):
        if not company_name:
            st.error("Please enter a company name")
            return
        
        with st.spinner(f"Processing {company_name}..."):
            result = extract_company_data(company_name)
            
            if result["success"]:
                st.success(f"✅ Successfully processed {company_name}")
                
                data = result["data"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Company:** {data['company_name']}")
                    st.write(f"**Domain:** {data['domain']}")
                
                with col2:
                    linkedin = data.get('linkedin_url', 'Not found')
                    if linkedin and linkedin != 'Not found':
                        st.write(f"**LinkedIn:** [View]({linkedin})")
                    else:
                        st.write("**LinkedIn:** Not found")
                
                st.subheader("Analysis Results")
                try:
                    # Try to parse as JSON for better display
                    analysis_data = json.loads(data['analysis'])
                    st.json(analysis_data)
                except:
                    # If not valid JSON, show as text
                    st.text(data['analysis'])
                
                # Refresh the page to show the new company in the list
                st.rerun()
                
            else:
                st.error(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()
