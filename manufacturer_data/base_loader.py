"""
Base class for scraping technical data for paragliders from manufacturer websites.
Manufacturer-specific implementations should extend this class.
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any
from playwright.async_api import async_playwright, Browser, Page, Playwright
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseGliderDataLoader:
    """
    Base class for scraping paraglider technical specifications from manufacturer websites.
    
    Handles Playwright initialization and provides common table extraction functionality.
    Subclasses should implement manufacturer-specific navigation and parsing logic.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the loader.
        
        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Page load timeout in milliseconds (default: 30000)
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
        metadata: Optional[Dict[str, Any]] = None,
        transpose: bool = False
    ) -> pd.DataFrame:
        """
        Extract a table from the current page.
        
        Args:
            selector: CSS selector for the table element
            metadata: Optional metadata to add to the extracted data
                     (e.g., {'glider_name': 'XXX', 'manufacturer': 'YYY'})
            transpose: If True, transpose the table (useful when sizes are in columns)
        
        Returns:
            DataFrame with extracted table data and optional metadata columns
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        
        logger.info(f"Extracting table with selector: {selector}")
        
        # Wait for table to be present
        await self.page.wait_for_selector(selector, state="visible")
        
        # Extract table data using JavaScript
        table_data = await self.page.evaluate("""
            (selector) => {
                const table = document.querySelector(selector);
                if (!table) return null;
                
                // Try to find rows in thead and tbody separately
                const theadRows = Array.from(table.querySelectorAll('thead tr'));
                const tbodyRows = Array.from(table.querySelectorAll('tbody tr'));
                const rows = theadRows.length > 0 || tbodyRows.length > 0 
                    ? [...theadRows, ...tbodyRows]
                    : Array.from(table.querySelectorAll('tr'));
                
                if (rows.length === 0) return null;
                
                const data = [];
                
                // Check if first row contains headers
                const firstRow = rows[0];
                const hasHeaders = firstRow.querySelector('th') !== null;
                
                let headers = [];
                let dataStartIndex = 0;
                
                if (hasHeaders) {
                    headers = Array.from(firstRow.querySelectorAll('th, td'))
                        .map(cell => cell.textContent.trim());
                    dataStartIndex = 1;
                } else {
                    // Generate generic headers if no headers found
                    const cellCount = firstRow.querySelectorAll('td').length;
                    headers = Array.from({length: cellCount}, (_, i) => `Column_${i + 1}`);
                }
                
                // Extract data rows
                for (let i = dataStartIndex; i < rows.length; i++) {
                    const cells = Array.from(rows[i].querySelectorAll('td, th'));
                    if (cells.length > 0) {
                        const rowData = {};
                        cells.forEach((cell, index) => {
                            if (index < headers.length) {
                                rowData[headers[index]] = cell.textContent.trim();
                            }
                        });
                        data.push(rowData);
                    }
                }
                
                return {headers, data};
            }
        """, selector)
        
        if not table_data or not table_data['data']:
            logger.warning(f"No table found with selector: {selector}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(table_data['data'])
        
        # Transpose if requested (for tables where sizes are columns)
        if transpose:
            # First column becomes the index (parameter names)
            first_col = df.columns[0]
            df = df.set_index(first_col).T
            df.index.name = 'Size'
            df = df.reset_index()
        
        # Add metadata columns if provided
        if metadata:
            for key, value in metadata.items():
                df[key] = value
        
        logger.info(f"Extracted {len(df)} rows with {len(df.columns)} columns")
        return df
        
    async def extract_multiple_tables(
        self,
        selectors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[pd.DataFrame]:
        """
        Extract multiple tables from the current page.
        
        Args:
            selectors: List of CSS selectors for table elements
            metadata: Optional metadata to add to all extracted tables
        
        Returns:
            List of DataFrames, one for each table
        """
        tables = []
        for selector in selectors:
            try:
                df = await self.extract_table(selector, metadata)
                if not df.empty:
                    tables.append(df)
            except Exception as e:
                logger.warning(f"Failed to extract table with selector {selector}: {e}")
        
        return tables
        
    async def scrape_glider_data(
        self,
        url: str,
        table_selector: str,
        metadata: Optional[Dict[str, Any]] = None,
        transpose: bool = False
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
        return await self.extract_table(table_selector, metadata, transpose)
        
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
