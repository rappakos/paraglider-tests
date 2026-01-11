

from manufacturer_data.base_loader import BaseGliderDataLoader
import pandas as pd
from typing import Optional


MANUFACTURER_CONFIG = {
        'Ozone': {
            'table_selector': 'div.specs-table-wrapper table',
            'transpose': True,
            'url_pattern': 'https://flyozone.com/paragliders/products/gliders/{model}'
        }
    }


class OzoneSpecsLoader(BaseGliderDataLoader):
    """Loader for Ozone paraglider specifications"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        self.config = MANUFACTURER_CONFIG['Ozone']
        
    async def load_glider_specs(self, model: str, glider_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load specifications for a specific Ozone glider model.
        
        Args:
            model: Model identifier for URL (e.g., 'alpina-4')
            glider_name: Display name of the glider (defaults to model if not provided)
        
        Returns:
            DataFrame with normalized specifications
        """
        url = self.config['url_pattern'].format(model=model)
        
        metadata = {
            'glider_name': glider_name or model,
            'manufacturer': 'Ozone',
            'scrape_date': pd.Timestamp.now()
        }
        
        df = await self.scrape_glider_data(
            url=url,
            table_selector=self.config['table_selector'],
            metadata=metadata,
            transpose=self.config['transpose']
        )
        
        # Apply Ozone-specific transformations
        df = self._normalize_ozone_data(df)
        
        return df
    
    def _normalize_ozone_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform Ozone-specific data to common schema.
        
        Handles:
        - Column name standardization
        - Unit conversions
        - Data type corrections
        """
        if df.empty:
            return df
        
        # Column name mappings (Ozone -> Standard)
        column_mapping = {
            'Sizes': 'size',
            'Number of Cells': 'cells',
            'Projected area (m2)': 'area_projected_m2',
            'Flat Area (m^2)': 'area_flat_m2',
            'Projected Span (m)': 'span_projected_m',
            'Flat Span (m)': 'span_flat_m',
            'Projected Aspect Ratio': 'aspect_ratio_projected',
            'Flat Aspect Ratio': 'aspect_ratio_flat',
            'Root Chord (m)': 'chord_root_m',
            'Glider Weight* (kg)': 'weight_kg',
            'Certified Weight Range (kg)': 'weight_range_kg',
            'Certification': 'certification'
        }
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Uppercase size values if present
        if 'size' in df.columns:
            df['size'] = df['size'].str.upper()
        
        # Convert numeric columns
        numeric_columns = [
            'cells', 'area_projected_m2', 'area_flat_m2',
            'span_projected_m', 'span_flat_m', 'aspect_ratio_projected',
            'aspect_ratio_flat', 'chord_root_m', 'weight_kg'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = self.clean_numeric_column(df, col)
        
        return df


    def model_name_to_url_slug(self, model_name: str) -> str:

        slug = super().model_name_to_url_slug(model_name)

        overrides = {
            'alta': 'alta-gt',
            'delta4': 'delta-4',
            'magnum4': 'magnum-4',
        }

        return overrides.get(slug, slug)

# Example usage
async def example_usage():
    """Example of loading Ozone glider specifications."""
    import asyncio
    
    async with OzoneSpecsLoader() as loader:
        df = await loader.load_glider_specs('alpina-4', 'Alpina 4')
        print(df)
        print(f"\nStandardized columns: {df.columns.tolist()}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(example_usage())
