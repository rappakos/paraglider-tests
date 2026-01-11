"""
Base class for scraping technical data for paragliders from manufacturer websites.
Manufacturer-specific implementations should extend this class.
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any
from playwright.async_api import async_playwright, Browser, Page, Playwright
import pandas as pd
from io import StringIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseGliderDataLoader:
    """
    Base class for scraping paraglider technical specifications from manufacturer websites.
    
    Handles Playwright initialization and provides common table extraction functionality.
    Subclasses should implement manufacturer-specific navigation and parsing logic.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 10000):
        """
        Initialize the loader.
        
        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Page load timeout in milliseconds (default: 10000)
        """
        self.headless = headless
        self.timeout = timeout
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        """Async context manager entry - initializes Playwright."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes browser."""
        await self.close()
        
    async def initialize(self):
        """Initialize Playwright and browser instance."""
        logger.info("Initializing Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(self.timeout)
        logger.info("Browser initialized successfully.")
        
    async def close(self):
        """Close browser and Playwright instance."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed.")
        
    async def navigate_to(self, url: str):
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        logger.info(f"Navigating to {url}")
        await self.page.goto(url, wait_until="networkidle")
        
    async def extract_table(
        self,
        selector: str,
        skip_header_rows: int = 0,
        skip_body_columns: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Extract table data where sizes are in columns.
        
        This handles the common manufacturer pattern where:
        - Header row contains size names (21, 23, XS, S, etc.)
        - First column(s) contain parameter names
        - Optional unit column after parameter name
        - Data cells contain the values for each size
        
        Args:
            selector: CSS selector for the table
            skip_header_rows: Number of header rows to skip (default: 0)
            skip_body_columns: Number of leftmost columns to skip in body rows (0=parameter name, 1=parameter+unit, etc.)
            metadata: Optional metadata to add
        
        Returns:
            DataFrame where each row is a size with columns for each parameter
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        logger.info(f"Extracting structured table with selector: {selector}")
        await self.page.wait_for_selector(selector, state="visible")
   
        # Get the table HTML
        table_html = await self.page.locator(selector).first.evaluate('el => el.outerHTML')
        
        # Use pandas to read the HTML table
        dfs = pd.read_html(StringIO(table_html))
        if not dfs:
            logger.warning(f"No table found with selector: {selector}")
            return pd.DataFrame()
        
        df = dfs[0]
        
        # Header: skip first (skip_body_columns + 1) columns, rest are sizes
        sizes = df.columns[skip_body_columns + 1:]
        
        # Body: first column is parameter name
        param_col = df.columns[0]

        # some values might be left empty for design reasons, we copy the previous row's parameter name and append a suffix
        for idx, param_name in enumerate(df[param_col]):
            if pd.isna(param_name) or str(param_name).strip() == '':
                if idx > 0:
                    df.at[idx, param_col] = f"{df.at[idx - 1, param_col]}*"
                else:
                    df.at[idx, param_col] = "unknown_param"

        #print(f"Parameter column: {df[param_col].tolist()}")
        
        # Transpose: each size becomes a row
        rows = []
        for size in sizes:
            row = {'size': str(size)}
            for idx, param_name in enumerate(df[param_col]):
                if pd.notna(param_name) and str(param_name).strip():
                    row[str(param_name)] = df[size].iloc[idx]
            rows.append(row)        


        result_df = pd.DataFrame(rows)
        
        # Add metadata columns if provided
        if metadata:
            for key, value in metadata.items():
                result_df[key] = value
        
        logger.info(f"Extracted {len(result_df)} rows with {len(result_df.columns)} columns")
        return result_df
        
    async def scrape_glider_data(
        self,
        url: str,
        table_selector: str,
        skip_header_rows: int = 0,
        skip_body_columns: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """
        Convenience method to navigate to a page and extract table data.
        
        Args:
            url: URL of the page containing the glider data
            table_selector: CSS selector for the table
            metadata: Optional metadata to add (e.g., glider name, manufacturer)
            transpose: If True, transpose the table (useful when sizes are in columns)
        
        Returns:
            DataFrame with extracted data
        """
        await self.navigate_to(url)
        return await self.extract_table(table_selector, metadata=metadata, skip_header_rows=skip_header_rows, skip_body_columns=skip_body_columns)
        
    def clean_numeric_column(self, df: pd.DataFrame, column: str) -> pd.Series:
        """
        Helper method to clean and convert a column to numeric values.
        
        Args:
            df: DataFrame containing the column
            column: Name of the column to clean
        
        Returns:
            Cleaned numeric Series
        """
        if column not in df.columns:
            return pd.Series()
        
        # Remove common units and convert to numeric
        cleaned = df[column].astype(str).str.replace(r'[^\d.-]', '', regex=True)
        return pd.to_numeric(cleaned, errors='coerce')

    def model_name_to_url_slug(self,model_name: str) -> str:
        """
        Convert model name to URL slug format.
        
        Args:
            model_name: Model name (e.g., "Alpina 4")
        
        Returns:
            URL slug (e.g., "alpina-4")
        """
        return model_name.lower().replace(' ', '-')

# Example usage
async def example_usage():
    """Example of how to use the BaseGliderDataLoader."""
    async with BaseGliderDataLoader() as loader:

        url = "https://flyozone.com/paragliders/products/gliders/alpina-4"
        # Use the specs-table-wrapper to target the specific technical data table
        table_selector = "div.specs-table-wrapper table"
        metadata = {
            "glider_name": "Alpina 4",
            "manufacturer": "Ozone",
            "scrape_date": pd.Timestamp.now()
        }
        
        # Transpose=True because Ozone tables have sizes as columns
        df = await loader.scrape_glider_data(url, table_selector, metadata, transpose=True)
        print(df)
        print(f"\nShape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")


if __name__ == '__main__':
    asyncio.run(example_usage())
