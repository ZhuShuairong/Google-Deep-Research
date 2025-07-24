import streamlit as st
from reagent import DeepResearchAgent, get_google_urls, fetch_web_content, save_to_csv
import pandas as pd
import time
from datetime import datetime
import os
from urllib.parse import urlparse
import json # Import json for saving data

# --- Create directories if they don't exist ---
# Only research_history is needed now
os.makedirs("research_history", exist_ok=True)
# os.makedirs("scraped_content", exist_ok=True) # Removed

# Set page config
st.set_page_config(
    page_title="Deep Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
        .main {
            max-width: 1200px;
            padding: 2rem;
        }
        .stTextInput input {
            font-size: 18px;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        .report-box {
            background-color: black;
            border-radius: 8px;
            padding: 2rem;
            margin-top: 1rem;
            border-left: 5px solid #4CAF50;
        }
        .url-box {
            background-color: #f0f2f6;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        }
        .search-result {
            margin-bottom: 1rem;
            padding: 1rem;
            border-radius: 8px;
            background-color: white;
            border: 1px solid #e0e0e0;
        }
        .search-result-title {
            color: #1a0dab;
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 0.2rem;
        }
        .search-result-url {
            color: #006621;
            font-size: 0.9rem;
            margin-bottom: 0.3rem;
            word-break: break-all;
        }
        .search-result-desc {
            color: #545454;
            font-size: 0.95rem;
        }
        .progress-container {
            margin: 2rem 0;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'research_history' not in st.session_state:
    st.session_state.research_history = []
if 'current_research' not in st.session_state:
    st.session_state.current_research = None
if 'selected_urls' not in st.session_state:
    st.session_state.selected_urls = []
if 'urls' not in st.session_state:
    st.session_state.urls = []
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'url_titles' not in st.session_state:
    st.session_state.url_titles = {}

# Initialize the research agent
@st.cache_resource
def get_researcher():
    return DeepResearchAgent()

researcher = get_researcher()

# Sidebar
with st.sidebar:
    st.title("🔍 Research Settings")
    st.markdown("Configure your research parameters")
    num_urls = st.slider("Number of URLs to fetch", 5, 20, 10)
    max_selection = st.slider("Maximum URLs to analyze", 1, 5, 3)
    save_csv = st.checkbox("Save results to CSV", value=True)
    st.markdown("---")
    st.markdown("### Research History")
    for i, item in enumerate(st.session_state.research_history):
        if st.button(f"{i+1}. {item['query'][:30]}...", key=f"history_{i}"):
            st.session_state.current_research = item

# Main content
st.title("🔍 Deep Research Agent")
st.markdown("Enter your research question below and get a comprehensive report synthesized from multiple web sources.")

# Research form
with st.form("research_form"):
    query = st.text_input("Research question", placeholder="Enter your research question here...", value=st.session_state.query)
    col1, col2 = st.columns([1, 3])
    with col1:
        submit_button = st.form_submit_button("Start Research")
    with col2:
        if st.form_submit_button("Clear Results"):
            st.session_state.current_research = None
            st.session_state.selected_urls = []
            st.session_state.urls = []
            st.session_state.query = ""
            st.session_state.url_titles = {}
            st.rerun()  # Updated from experimental_rerun

if submit_button and query:
    st.session_state.query = query
    with st.spinner("Searching for relevant sources..."):
        # Get URLs from Google
        st.session_state.urls = get_google_urls(query, num_results=num_urls)
        if not st.session_state.urls:
            st.error("No search results found for the query.")
            st.stop()
        # Reset selections
        st.session_state.selected_urls = []
        st.session_state.url_titles = {}
        # Extract simple titles (just domain name if no title)
        for url in st.session_state.urls:
            try:
                # Extract domain as simple title
                domain = urlparse(url).netloc
                st.session_state.url_titles[url] = domain if domain else url
            except:
                st.session_state.url_titles[url] = url

# Display URLs for selection (outside the form)
if st.session_state.urls:
    st.subheader("Select URLs to analyze")
    st.markdown(f"Choose up to {max_selection} sources to include in your research (click the checkboxes)")
    # Display search results with checkboxes
    for i, url in enumerate(st.session_state.urls[:num_urls], 1):
        title = st.session_state.url_titles.get(url, url)
        col1, col2 = st.columns([1, 15])
        with col1:
            selected = st.checkbox(
                f"Select {i}",
                key=f"select_{i}",
                value=url in st.session_state.selected_urls,
                label_visibility="collapsed"
            )
            if selected:
                if url not in st.session_state.selected_urls:
                    st.session_state.selected_urls.append(url)
            else:
                if url in st.session_state.selected_urls:
                    st.session_state.selected_urls.remove(url)
        with col2:
            st.markdown(f"""
                <div class="search-result">
                    <div class="search-result-title">{title}</div>
                    <div class="search-result-url">{url}</div>
                </div>
            """, unsafe_allow_html=True)

    # Analyze button
    if st.button("Analyze Selected Sources"):
        if not st.session_state.selected_urls:
            st.warning("Please select at least one source to analyze")
        elif len(st.session_state.selected_urls) > max_selection:
            st.warning(f"Please select no more than {max_selection} sources")
        else:
            # Fetch content with progress bar
            progress_text = "Analyzing selected sources..."
            progress_bar = st.progress(0, text=progress_text)
            contexts = []
            for i, url in enumerate(st.session_state.selected_urls):
                progress = (i + 1) / len(st.session_state.selected_urls)
                progress_bar.progress(progress, text=f"Analyzing source {i+1} of {len(st.session_state.selected_urls)}...")
                contexts.append(fetch_web_content(url))
                time.sleep(0.1)  # For better progress visualization
            progress_bar.empty()

            # Generate report using the researcher agent
            with st.spinner("Synthesizing research report..."):
                full_context = "\n".join(contexts)
                prompt = f"You are a helpful research assistant, Help me synthesize the information from the context based on the query. Query: {st.session_state.query}\nContext: {full_context}"
                answer = researcher.llm.invoke(prompt)

                # Save to CSV if requested (only URLs now, not contexts)
                if save_csv:
                    now = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"research_report_{now}.csv"
                    # Pass empty strings or None for context if you don't want it in CSV
                    # Or modify save_to_csv to accept only URLs.
                    # Assuming save_to_csv expects (urls, contexts, filename)
                    # We can pass empty contexts or modify the function call.
                    # Let's assume the function needs modification or we pass minimal context.
                    # For now, let's just pass the URLs and empty strings for context.
                    save_to_csv(st.session_state.selected_urls, [""] * len(st.session_state.selected_urls), filename)


                # --- Save to Folders ---
                timestamp_for_filenames = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Prepare data for JSON (excluding scraped content files list)
                research_item_for_json = {
                    "query": st.session_state.query,
                    "urls": st.session_state.selected_urls,
                    "report": answer,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # Removed "scraped_content_files": []
                }

                # Save the main research data to JSON
                json_filename = f"research_{timestamp_for_filenames}.json"
                json_filepath = os.path.join("research_history", json_filename)
                try:
                    with open(json_filepath, 'w', encoding='utf-8') as f:
                        json.dump(research_item_for_json, f, indent=4)
                except Exception as e:
                    st.error(f"Error saving research data to JSON: {e}")
                # --- End Save to Folders ---


                # Store in session state (original functionality)
                research_item = {
                    "query": st.session_state.query,
                    "urls": st.session_state.selected_urls,
                    "contexts": contexts, # Keep contexts in session state for UI display
                    "report": answer,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.research_history.insert(0, research_item)
                st.session_state.current_research = research_item
                st.rerun()  # Updated from experimental_rerun

# Display current research if available
if st.session_state.current_research:
    research = st.session_state.current_research
    st.subheader("Research Report")
    st.markdown(f"**Query:** {research['query']}")
    st.markdown(f"**Generated on:** {research['timestamp']}")

    with st.expander("📄 View Full Report", expanded=True):
        st.markdown(f'<div class="report-box">{research["report"]}</div>', unsafe_allow_html=True)

    with st.expander("🔗 View Sources", expanded=False):
        # Check if contexts are in session state or need to be read from files
        # For simplicity here, we'll use the session state contexts if available
        contexts_to_display = research.get('contexts', [])
        if contexts_to_display:
             for i, (url, context) in enumerate(zip(research['urls'], contexts_to_display), 1):
                # Get title for display
                title = st.session_state.url_titles.get(url, url)
                st.markdown(f"""
                    <div class="search-result">
                        <div class="search-result-title">Source {i}: {title}</div>
                        <div class="search-result-url">{url}</div>
                    </div>
                """, unsafe_allow_html=True)
                with st.expander(f"View content from Source {i}"):
                    st.text(context[:2000] + ("..." if len(context) > 2000 else ""))
        else:
            st.write("Source content not available in session state.")

    # Download button (downloads session state data)
    # Note: This still uses contexts from session state for the download.
    if 'contexts' in research: # Ensure contexts are available
        csv = "\n".join([f"{url}\n{context}" for url, context in zip(research['urls'], research['contexts'])])
        st.download_button(
            label="Download Research Data",
            data=csv,
            file_name=f"research_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    else:
        st.info("Download button uses session data which might not include full scraped content.")
