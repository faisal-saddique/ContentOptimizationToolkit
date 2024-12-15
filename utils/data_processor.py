from typing import List
import streamlit as st
from utils.api_client import APIClient

class DataProcessor:
    """Enhanced data processing and analysis with robust error handling."""

    @staticmethod
    def get_competitor_summaries(urls: List[str], progress_bar) -> List[str]:
        """
        Fetch and summarize content from competitor URLs.

        Args:
            urls (List[str]): List of competitor URLs
            progress_bar: Streamlit progress bar for tracking

        Returns:
            List[str]: List of URL summaries
        """
        summaries = []
        total_urls = len(urls)
        for idx, url in enumerate(urls, 1):
            st.write(f"**Processing URL {idx}/{total_urls}:** {url}")
            try:
                # Fetch webpage content
                st.info(f"Fetching content from URL {idx}...")
                content = APIClient.fetch_webpage_content(url)
                if not content:
                    st.warning(f"URL {idx}: Content fetch failed.")
                    summaries.append("")
                    continue

                # Summarize content
                st.info(f"Summarizing content from URL {idx}...")
                summary = APIClient.summarize_content_with_openai(content)
                if summary:
                    st.success(f"URL {idx}: Summary generated successfully.")
                    st.write(f"**Summary for URL {idx}:**\n{summary}")
                    summaries.append(summary)
                else:
                    st.warning(f"URL {idx}: Summarization failed.")
                    summaries.append("")

            except Exception as e:
                st.error(f"Error processing URL {idx}: {e}")
                summaries.append("")

            # Update progress bar
            progress = 25 + int((50 / total_urls) * idx)
            progress_bar.progress(min(progress, 100))

        return summaries