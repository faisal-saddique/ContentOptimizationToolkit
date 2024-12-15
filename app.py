import streamlit as st
from utils.api_client import APIClient
from utils.data_processor import DataProcessor
from utils.config import Config

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    defaults = {
        "user_content": "",
        "keyword": "best laptops 2024",
        "content_input_option": "Paste Text",
        "analysis_result": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def sidebar_configuration():
    """Create sidebar with application configuration and information."""
    with st.sidebar:

        st.title("🔧 Configuration")
        
        st.markdown("### Search Settings")
        Config.NUMBER_OF_SEARCHES = st.slider(
            "Number of Competitor URLs", 
            min_value=1, 
            max_value=50, 
            value=10,
            help="Select the number of top-ranking URLs to analyze for your keyword"
        )
        
        st.markdown("---")
        
        st.markdown("### About the Tool")
        st.info(
            "**Content Optimization Toolkit**\n\n"
            "- Analyze your content against top-ranking pages\n"
            "- Get AI-powered optimization suggestions\n"
            "- Improve SEO and readability"
        )

def content_input_section():
    """Handle different methods of content input."""
    st.subheader("📝 Content Input")
    
    # Keyword input with validation
    st.session_state.keyword = st.text_input(
        "Enter Target Keyword", 
        value=st.session_state.keyword,
        help="The keyword you want to optimize your content for"
    )
    
    st.session_state.content_input_option = st.radio(
        "Choose content input method", 
        ["Paste Text", "Enter URL", "Upload File"],
        index=["Paste Text", "Enter URL", "Upload File"].index(st.session_state.content_input_option)
    )

    if st.session_state.content_input_option == "Paste Text":
        st.session_state.user_content = st.text_area(
            "Paste your content here:", 
            value=st.session_state.user_content, 
            height=300,
            help="Enter the text you want to optimize"
        )
    elif st.session_state.content_input_option == "Enter URL":
        content_url = st.text_input(
            "Enter webpage URL:", 
            help="Provide a URL to fetch content from"
        )
        if st.button("Fetch Content"):
            with st.status("Fetching webpage content...", expanded=True) as status:
                try:
                    fetched_content = APIClient.fetch_webpage_content(content_url)
                    if fetched_content:
                        st.session_state.user_content = fetched_content
                        st.success("Content fetched successfully!")
                        status.update(label="Content Fetched", state="complete")
                    else:
                        st.warning("Could not fetch content from the provided URL.")
                        status.update(label="Fetching Failed", state="error")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    status.update(label="Fetching Failed", state="error")
    elif st.session_state.content_input_option == "Upload File":
        uploaded_file = st.file_uploader(
            "Choose a text file", 
            type=["txt"], 
            help="Upload a text file to optimize"
        )
        if uploaded_file is not None:
            with st.status("Processing uploaded file...", expanded=True) as status:
                try:
                    content = uploaded_file.read().decode("utf-8")
                    st.session_state.user_content = content
                    st.success("File uploaded successfully!")
                    with st.expander("Uploaded Content Preview"):
                        st.write(content)
                    status.update(label="File Processed", state="complete")
                except Exception as e:
                    st.error(f"An error occurred while processing the file: {e}")
                    status.update(label="File Processing Failed", state="error")

def run_content_analysis():
    """Perform content analysis with improved error handling and user feedback."""
    if not st.session_state.user_content:
        st.warning("Please provide content before running analysis.")
        return

    with st.status("Running Content Analysis", expanded=True) as status:
        try:
            status.update(label="Fetching Top URLs", state="running")
            # Fetch top URLs
            urls = APIClient.fetch_top_urls(st.session_state.keyword,Config.NUMBER_OF_SEARCHES)
            
            if not urls:
                st.warning("No URLs found for the given keyword.")
                status.update(label="URL Fetching Failed", state="error")
                return

            for url in urls:
                st.write(url)

            status.update(label="Analyzing Competitor Content", state="running")
            # Get competitor summaries
            progress_bar = st.progress(0)
            competitor_summaries = DataProcessor.get_competitor_summaries(urls, progress_bar)

            status.update(label="Generating Optimization Suggestions", state="running")
            # Analyze user's content
            st.session_state['result'] = APIClient.analyze_content_with_openai(
                st.session_state.user_content, 
                st.session_state.keyword, 
                competitor_summaries
            )
            

            status.update(label="Analysis Complete", state="complete")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            status.update(label="Analysis Failed", state="error")

def main():
    """Main application workflow."""
    # Set page configuration
    st.set_page_config(
        page_title="Content Optimization Toolkit", 
        page_icon="📈", 
        layout="wide"
    )

    # Initialize session state
    initialize_session_state()

    # Sidebar configuration
    sidebar_configuration()

    # Main content area
    st.title("📈 Content Optimization Toolkit")
    st.markdown("Elevate your content with AI-powered insights and optimization suggestions.")

    # Content input section
    content_input_section()

    # Analysis button
    if st.button("🔍 Analyze Content", use_container_width=True):
        run_content_analysis()
    if "result" in st.session_state:
        st.write_stream(st.session_state.result)
        
if __name__ == "__main__":
    main()