

from manufacturer_data.base_loader import BaseGliderDataLoader
import pandas as pd
from typing import Optional


MANUFACTURER_CONFIG = {
        'Ozone': {
            'table_selector': 'div.specs-table-wrapper table',
            'skip_header_rows': 0,
            'skip_body_columns': 0,  # Only parameter name in first column            
            'url_pattern': 'https://flyozone.com/paragliders/products/gliders/{model}'
        },
        'Advance': {
            'table_selector': '#s-technical-data table',
            'skip_header_rows': 0,
            'skip_body_columns': 1,  # Parameter name + unit column            
            'url_pattern': 'https://www.advance.swiss/en/products/paragliders/{model}'
        },
        'Niviuk': {
            'table_selector': '#tabla_especificaciones',
            'skip_header_rows': 0,
            'skip_body_columns': 2,          
            'url_pattern': 'https://niviuk.com/en/{model}'
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
            'manufacturer': 'Ozone'
        }
        
        df = await self.scrape_glider_data(
            url=url,
            table_selector=self.config['table_selector'],
            skip_header_rows=self.config['skip_header_rows'],
            skip_body_columns=self.config['skip_body_columns'],            
            metadata=metadata
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


class AdvanceSpecsLoader(BaseGliderDataLoader):
    """Loader for Advance paraglider specifications"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        self.config = MANUFACTURER_CONFIG['Advance']
    
    async def load_glider_specs(self, model: str, glider_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load specifications for a specific Advance glider model.
        
        Args:
            model: Model identifier for URL (e.g., 'iota-dls')
            glider_name: Display name of the glider (defaults to model if not provided)
        
        Returns:
            DataFrame with normalized specifications
        """
        url = self.config['url_pattern'].format(model=model)
        
        metadata = {
            'glider_name': glider_name or model,
            'manufacturer': 'Advance'
        }
        
        df = await self.scrape_glider_data(
            url=url,
            table_selector=self.config['table_selector'],
            skip_header_rows=self.config['skip_header_rows'],
            skip_body_columns=self.config['skip_body_columns'],
            metadata=metadata
        )
        
        # Apply Advance-specific transformations
        df = self._normalize_advance_data(df, metadata)
        
        return df
    
    def _normalize_advance_data(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Transform Advance-specific data to common schema.
        """
        if df.empty:
            return df
        
        result_df = df.copy()

        # Column name mappings (Advance -> Standard)
        column_mapping = {
            'Size': 'size',
            'Flat surface': 'area_flat_m2',
            'Projected surface': 'area_projected_m2',
            #'Ideal weight range': 'weight_range_ideal_kg',
            'Certified takeoff weight': 'weight_range_kg',
            'Glider weight': 'weight_kg',
            #'Glider weight with light risers': 'weight_light_kg',
            'Span': 'span_flat_m',
            'Projected span': 'span_projected_m',
            'Aspect ratio': 'aspect_ratio_flat',
            'Projected aspect ratio': 'aspect_ratio_projected',
            'Max. chord': 'chord_root_m',
            'Number of cells': 'cells',
            'Certification': 'certification'
        }

        result_df = result_df.rename(columns=column_mapping)

        # Convert numeric columns
        numeric_columns = [
            'cells', 'area_projected_m2', 'area_flat_m2',
            'span_projected_m', 'span_flat_m', 'aspect_ratio_projected',
            'aspect_ratio_flat', 'chord_root_m', 'weight_kg'
        ]

        for col in numeric_columns:
            if col in result_df.columns:
                result_df[col] = self.clean_numeric_column(result_df, col)

        return result_df    


    def model_name_to_url_slug(self, model_name: str) -> str:
        """Convert Advance model names to URL slugs."""
        slug = super().model_name_to_url_slug(model_name)
        
        overrides = {
            # Add Advance-specific overrides here
        }
        
        return overrides.get(slug, slug)


class NiviukSpecsLoader(BaseGliderDataLoader):
    """Loader for Niviuk paraglider specifications"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        self.config = MANUFACTURER_CONFIG['Niviuk']
        
    async def load_glider_specs(self, model: str, glider_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load specifications for a specific Niviuk glider model.
        
        Args:
            model: Model identifier for URL (e.g., 'ikuma-3')
            glider_name: Display name of the glider (defaults to model if not provided)"""
        
        url = self.config['url_pattern'].format(model=model)
        
        metadata = {
            'glider_name': glider_name or model,
            'manufacturer': 'Niviuk'
        }
        
        df = await self.scrape_glider_data(
            url=url,
            table_selector=self.config['table_selector'],
            skip_header_rows=self.config['skip_header_rows'],
            skip_body_columns=self.config['skip_body_columns'],            
            metadata=metadata
        )
        
        # Apply Niviuk-specific transformations
        df = self._normalize_niviuk_data(df)
        
        return df

    def _normalize_niviuk_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform Niviuk-specific data to common schema.
        """
        if df.empty:
            return df
        
        # Column name mappings (Niviuk -> Standard)
        column_mapping = {
            'Size': 'size',
            'AREA': 'area_flat_m2',
            'AREA*': 'area_projected_m2',  # empty header cell ?!
            'SPAN': 'span_flat_m',
            'SPAN*': 'span_projected_m',  # empty header cell ?!
            'ASPECT RATIO': 'aspect_ratio_flat',
            'ASPECT RATIO*': 'aspect_ratio_projected', # empty header cell ?!
            'CHORD': 'chord_root_m',
            'GLIDER WEIGHT': 'weight_kg',
            'TOTAL WEIGHT IN FLIGHT': 'weight_range_kg',
            'CELLS': 'cells',
            'CERTIFICATION': 'certification'
        }
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
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
    
    def model_name_to_url_slug(self, model_name):
        slug = super().model_name_to_url_slug(model_name) 

        overrides = {
            'artik-r': 'not-found', # redirects to artik-r-2, cannot use
            'artik-6': 'not-found', # redirects to artik-7-p, cannot use
            'artik-r2': 'artik-r-2'
        }

        return overrides.get(slug, slug)

# Example usage
async def example_usage():
    """Example of loading Ozone glider specifications."""
    
    #async with OzoneSpecsLoader() as loader:
    #    df = await loader.load_glider_specs('alpina-4', 'Alpina 4')
    #    print(df)
    #    print(f"\nStandardized columns: {df.columns.tolist()}")

    #async with AdvanceSpecsLoader() as loader:
    #    df = await loader.load_glider_specs('iota-dls', 'Iota DLS')
    #    print(df)
    #    print(f"\nStandardized columns: {df.columns.tolist()}")

    async with NiviukSpecsLoader() as loader:       
        df = await loader.load_glider_specs('ikuma-3', 'Ikuma 3')
        print(df)
        print(f"\nStandardized columns: {df.columns.tolist()}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(example_usage())
