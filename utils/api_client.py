from typing import Dict, Optional, List
from bs4 import BeautifulSoup
import html2text
import requests
import logging
from utils.config import Config
from openai import OpenAI
import streamlit as st

class APIClient:
    """Handles API interactions for different services with enhanced error handling."""

    @staticmethod
    def fetch_top_urls(keyword: str, num_searches: int) -> List[str]:
        """
        Fetch top URLs for the target keyword using Ahrefs API.

        Args:
            keyword (str): Target keyword for search
            num_searches (int): Number of search results to retrieve

        Returns:
            List[str]: List of top URLs
        """
        if not keyword.strip():
            logging.warning("Please enter a valid keyword.")
            return []

        params = {
            "keyword": keyword,
            "top_positions": num_searches,
            "select": "url",
            "country": "us",
            "language": "en",
        }
        headers = {
            "Authorization": f"Bearer {Config.AHREFS_AUTH_TOKEN}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                Config.AHREFS_API_URL, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()
            results = response.json()

            if not results.get("positions"):
                logging.warning(f"No search results found for the keyword: {keyword}")
                return []

            urls = [item["url"] for item in results["positions"] if item.get("url")]
            return urls

        except requests.exceptions.RequestException as e:
            logging.error(f"Ahrefs API Error: {e}")
            return []

    @staticmethod
    def fetch_webpage_content(url: str) -> Optional[str]:
        """
        Fetch and clean content from the given URL.

        Args:
            url (str): URL to fetch content from

        Returns:
            Optional[str]: Cleaned text content or None
        """
        if not url or not url.strip():
            logging.warning("No URL provided.")
            return None

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            html_content = response.text

            # Enhanced HTML parsing
            soup = BeautifulSoup(html_content, "html.parser")
            body_content = soup.body

            if not body_content:
                st.warning("Extracted content is too short to be meaningful.")
                logging.warning("No body content found in the webpage.")
                return None

            # More aggressive content cleanup
            for tag in body_content(
                [
                    "script",
                    "style",
                    "img",
                    "a",
                    "noscript",
                    "nav",
                    "header",
                    "footer",
                    "form",
                ]
            ):
                tag.decompose()

            markdown_converter = html2text.HTML2Text()
            markdown_converter.ignore_links = True
            markdown_converter.ignore_images = True
            markdown_converter.ignore_emphasis = True
            markdown_converter.skip_internal_links = True
            # markdown_converter.bypass_tables = True
            text_content = markdown_converter.handle(str(body_content))

            # More robust content validation
            if len(text_content.strip()) < 200:
                logging.warning("Extracted content is too short to be meaningful.")
                st.warning("Extracted content is too short to be meaningful.")
                return None

            return text_content

        except requests.exceptions.RequestException as e:
            logging.error(f"Webpage Fetch Error: {e}")
            return None

    @staticmethod
    def summarize_content_with_openai(text: str) -> Optional[str]:
        """
        Summarize content using OpenAI API.

        Args:
            text (str): Text to summarize

        Returns:
            Optional[str]: Summarized text or None
        """
        if not text or not text.strip():
            return None

        client = OpenAI(api_key=Config.OPENAI_API_KEY)  # Set the API key

        # Comprehensive system prompt for summarization
        system_prompt = (
            "You are a highly skilled summarization assistant. Your task is to distill "
            "the essence of the provided content into a concise summary, highlighting "
            "the main points and key insights. Ensure the summary is no more than 200 words "
            "and maintains the original context and intent."
        )

        prompt = (
            f"{system_prompt}\n\n"
            "Content to summarize:\n"
            f"{text}\n\n"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            if response and response.choices:
                summary = response.choices[0].message.content.strip()
                return summary

            logging.error("Failed to generate summary from OpenAI.")
            return None

        except Exception as e:
            logging.error(f"OpenAI Summarization Error: {e}")
            return None

    @staticmethod
    def analyze_content_with_openai(
        text: str, keyword: str, competitor_summaries: List[str]
    ) -> Dict:
        """
        Analyze content using OpenAI API.

        Args:
            text (str): Content to analyze
            keyword (str): Focus keyword
            competitor_summaries (List[str]): Summaries of competitor content

        Returns:
            Dict: Analysis results or error information
        """
        if not text or not text.strip():
            return {"error": "No text provided for analysis."}

        client = OpenAI(api_key=Config.OPENAI_API_KEY)  # Set the API key

        # Comprehensive system prompt for analysis
        system_prompt = (
            "You are an expert content editor and SEO specialist. Your role is to provide "
            "a detailed analysis of the given content, offering actionable optimization "
            "suggestions. Consider the focus keyword and competitor content to enhance "
            "the analysis."
        )

        prompt = (
            "Content to analyze:\n"
            f"{text}\n\n"
            f"Focus keyword: {keyword}\n\n"
        )

        if competitor_summaries:
            prompt += "Competitor content summaries (for context):\n"
            for i, summary in enumerate(competitor_summaries, 1):
                prompt += f"Competitor {i} Summary:\n{summary}\n\n"

        prompt += (
            "Your analysis should include:\n"
            "1. Overall content strengths and weaknesses\n"
            "2. Keyword optimization suggestions\n"
            "3. Readability and structure improvements\n"
            "4. Recommended content revisions\n"
            "5. SEO enhancement strategies"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
                stream=True,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            if response: 
                return response

        except Exception as e:
            logging.error(f"OpenAI Analysis Error: {e}")
            return f"error: {str(e)}"