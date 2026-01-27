"""
Service layer for managing manufacturer technical specifications.
Handles extraction of models from DB and coordination with loaders.
"""

import re
import asyncio
from typing import Dict, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from glider_tests_app.db import check_specs_freshness, get_specs_for_model, save_normalized_specs, save_raw_specs, check_open_items
from manufacturer_data.specs_loader import OzoneSpecsLoader, AdvanceSpecsLoader, NiviukSpecsLoader

import logging
logger = logging.getLogger(__name__)


DB_NAME = './glider_tests.db'


# Manufacturer to test organization mapping
MANUFACTURER_ORG_MAP = {
    'Ozone': 'air-turquoise',
    'Advance': 'air-turquoise',
    'Niviuk': 'air-turquoise'
}

# Manufacturer name variations in the database
MANUFACTURER_VARIANTS = {
    'Ozone': ['ozone', 'ozone gliders', 'ozone gliders ltd', 'ozone power ltd'],
    'Advance': ['advance', 'advance thun ag', 'advance thun'],
    'Niviuk': ['niviuk', 'niviuk gliders', 'niviuk gliders / air games s.l.', 'air games'],
}

def normalize_manufacturer_name(item_name: str) -> Optional[str]:
    """
    Detect and normalize manufacturer name from item_name.
    
    Args:
        item_name: Full item name from database
    
    Returns:
        Normalized manufacturer name or None if not found
    """
    item_lower = item_name.lower()
    
    for canonical_name, variants in MANUFACTURER_VARIANTS.items():
        for variant in variants:
            if item_lower.startswith(variant):
                return canonical_name
    
    return None

def extract_model_from_item_name(item_name: str, manufacturer: Optional[str] = None) -> Dict[str, str]:
    """
    Parse item_name to extract manufacturer, model, and size.
    
    Args:
        item_name: Full item name (e.g., "Ozone Alpina 4 XS")
        manufacturer: Known manufacturer name (optional, helps with parsing)
    
    Returns:
        Dict with keys: 'manufacturer', 'model', 'size', 'item_name'
    """
    # Size patterns: XS, S, M, L, XL, XXL or numeric (10-40 range for m²)
    size_pattern = r'\b(XXS|XS|S|MS|ML|M|L|XL|XXL|[1-4]\d)\b$'
    
    # Try to extract size (last token)
    size_match = re.search(size_pattern, item_name, re.IGNORECASE)
    size = size_match.group(1) if size_match else None
    
    # Remove size from item_name to get manufacturer + model
    if size:
        base_name = item_name[:size_match.start()].strip()
    else:
        base_name = item_name
    
    # If manufacturer is known, remove the actual variant from beginning
    if manufacturer:
        # Find which variant is actually used in the item_name
        # Sort by length descending to match longest variant first
        variants = MANUFACTURER_VARIANTS.get(manufacturer, [manufacturer.lower()])
        variants_sorted = sorted(variants, key=len, reverse=True)
        base_lower = base_name.lower()
        
        model = base_name  # default if no match
        for variant in variants_sorted:
            if base_lower.startswith(variant):
                # Remove the variant (not just canonical name)
                model = base_name[len(variant):].strip()
                break
    else:
        # Use the full base_name as model
        manufacturer = None
        model = base_name
    
    return {
        'manufacturer': manufacturer,
        'model': model,
        'size': size,
        'item_name': item_name
    }


async def get_all_wings_for_manufacturer(manufacturer: str) -> pd.DataFrame:
    """
    Get all wing items (with sizes) for a specific manufacturer from the database.
    Automatically determines the correct test organization.
    Handles manufacturer name variations using normalization.
    
    Args:
        manufacturer: Manufacturer name (e.g., 'Ozone', 'Advance')
    
    Returns:
        DataFrame with columns: item_name, report_class, manufacturer, model, size
    """
    # Determine which org to query
    org = MANUFACTURER_ORG_MAP.get(manufacturer, 'all')
    
    engine = create_engine(f'sqlite:///{DB_NAME}')
    
    # Get all manufacturer variants for the query
    variants = MANUFACTURER_VARIANTS.get(manufacturer, [manufacturer.lower()])
    
    # Build OR conditions for all variants
    variant_conditions = ' OR '.join([f"LOWER(item_name) LIKE '{variant}%'" for variant in variants])
    
    # Query to get all items for this manufacturer
    query = f"""
        SELECT DISTINCT org, item_name, report_class
        FROM (
            SELECT :org as [org], item_name, report_class FROM dhv_reports
            WHERE :org = 'dhv'  -- AND model is null AND size is null
            UNION ALL
            SELECT :org as [org], item_name, report_class FROM air_turquoise_reports
            WHERE :org = 'air-turquoise' -- AND model is null AND size is null
        )
        WHERE {variant_conditions} 
        ORDER BY item_name
    """
    
    with engine.connect() as db:
        df = pd.read_sql_query(
            text(query),
            db,
            params={'org': org}
        )
    
    if df.empty:
        return pd.DataFrame(columns=['item_name', 'report_class', 'manufacturer', 'model', 'size'])
    
    # Normalize manufacturer names and parse model/size
    df['manufacturer'] = df['item_name'].apply(normalize_manufacturer_name)
    parsed = df.apply(lambda row: extract_model_from_item_name(row['item_name'], row['manufacturer']), axis=1)
    df['model'] = parsed.apply(lambda x: x['model'])
    df['size'] = parsed.apply(lambda x: x['size'])
    
    return df


async def get_models_for_manufacturer(manufacturer: str) -> pd.DataFrame:
    """
    Get unique models (base names without sizes) for a specific manufacturer.
    Groups items by base model.
    
    Args:
        manufacturer: Manufacturer name (e.g., 'Ozone', 'Advance')
    
    Returns:
        DataFrame with columns: manufacturer, model, size_count, sizes, example_item_name
    """
    df = await get_all_wings_for_manufacturer(manufacturer)
    
    if df.empty:
        return pd.DataFrame(columns=['manufacturer', 'model', 'size_count', 'sizes', 'example_item_name'])
    
    # Group by model to get size variations
    grouped = df.groupby(['org','manufacturer', 'model']).agg({
        'size': ['count', lambda x: ', '.join(sorted(filter(None, set(x))))],
        'item_name': 'first'
    }).reset_index()
    
    grouped.columns = ['org','manufacturer', 'model', 'size_count', 'sizes', 'example_item_name']
    
    return grouped

async def link_reports_to_specs(manufacturer: str = None):
    """
    Populate manufacturer/model/size fields in reports tables.
    Call this before loading specs to get the models list.
    
    Args:
        manufacturer: Optional manufacturer filter, or None for all
    """
    from glider_tests_app.db import populate_report_glider_fields
    
    # Populate all reports or just one manufacturer
    if manufacturer:
        org = MANUFACTURER_ORG_MAP.get(manufacturer).replace('-', '_')
        await populate_report_glider_fields(org)
    else:
        await populate_report_glider_fields()
    
    logger.info(f"Successfully populated report fields for {manufacturer or 'all manufacturers'}")



async def load_specs(manufacturer: str, force_refresh: bool = False) -> pd.DataFrame:
    """
    Load technical specifications for all models of a given manufacturer.
    
    Args:
        manufacturer: Manufacturer name (e.g., 'Ozone', 'Advance')"""
    if not manufacturer or manufacturer not in MANUFACTURER_ORG_MAP:
        raise ValueError(f"Unsupported manufacturer: {manufacturer}")
    
    # get "open" models from DB
    models_df = await get_models_for_manufacturer(manufacturer)
    if models_df.empty:
        logger.info("No models to be processed.")
        return pd.DataFrame()

    # Initialize loader based on manufacturer
    loader = None
    if manufacturer == 'Ozone':
        loader = OzoneSpecsLoader(headless=True)
    if manufacturer == 'Advance':
        loader = AdvanceSpecsLoader(headless=True)
    if manufacturer == 'Niviuk':    
        loader = NiviukSpecsLoader(headless=True)

    if loader is None:
        raise ValueError(f"No loader available for manufacturer: {manufacturer}")


    #models_df = models_df[models_df['model'].str.contains('Alpina')]

    async with loader:
        specs_list = []
        for _, row in models_df.iterrows():
            model_name = row['model']
           
            # Check if we need to scrape
            if not force_refresh and await check_specs_freshness(manufacturer, model_name):
                logger.info(f"Using cached specs for {manufacturer} {model_name}")
                cached_specs = await get_specs_for_model(manufacturer, model_name)
                if not cached_specs.empty:
                    specs_list.append(cached_specs)
                    continue
            
            # Scrape new specs
            url_slug = loader.model_name_to_url_slug(model_name)
            url = loader.config['url_pattern'].format(model=url_slug)
            
            try:
                specs_df = await loader.load_glider_specs(model=url_slug, glider_name=model_name)
                
                if not specs_df.empty:
                    # Save raw data
                    raw_data = specs_df.to_dict('records') # this is not the actual raw data...
                    await save_raw_specs(
                        manufacturer=manufacturer,
                        model=model_name,
                        raw_data={'specs': raw_data, 'columns': list(specs_df.columns)},
                        scrape_status='success',
                        url=url
                    )
                    
                    # Save normalized data
                    count = await save_normalized_specs(manufacturer, model_name, specs_df)
                    logger.info(f"Saved {count} size specs for {manufacturer} {model_name}")
                    
                    specs_list.append(specs_df)

                else:
                    await save_raw_specs(
                        manufacturer=manufacturer,
                        model=model_name,
                        raw_data={},
                        scrape_status='not_found',
                        url=url,
                        error_message='No specifications found on page'
                    )
                    logger.warning(f"No specs found for {manufacturer} {model_name}")
                    
            except Exception as e:
                error_msg = str(e)
                status = 'timeout' if 'Timeout' in error_msg else 'error'
                
                await save_raw_specs(
                    manufacturer=manufacturer,
                    model=model_name,
                    raw_data={},
                    scrape_status=status,
                    url=url,
                    error_message=error_msg
                )
                logger.error(f"Error loading specs for {manufacturer} {model_name}: {error_msg}")



    # temp
    return models_df

# Example usage
async def get_models():
    """Example: Load all Ozone wing data from database"""
    print("\n=== Getting all Ozone wings from database ===")

    for manufacturer in ['Ozone','Advance', 'Niviuk']:    
        # Get all wings with sizes
        #wings = await get_all_wings_for_manufacturer(manufacturer)
        #print(f"\nTotal wings found: {len(wings)}")
        #print("\nSample data:")
        #print(wings.head(10))
        
        # Get grouped models
        models = await get_models_for_manufacturer(manufacturer)
        print(f"\n\nUnique models: {len(models)}")
        print("\nModels with sizes:")
        print(models[['model', 'size_count', 'sizes']])

async def main():
    """Scrape manufacturer data"""
    manufacturer = 'Niviuk'
    specs_df = await load_specs(manufacturer, force_refresh=True)
    
    if not specs_df.empty:
        print("\n\n=== Sample of scraped data ===")
        print(specs_df.head(10))
        print("\n\nColumns:", specs_df.columns.tolist())


    await link_reports_to_specs(manufacturer)

async def check_items():

    return await check_open_items()




if __name__ == '__main__':
    asyncio.run(main())

    df = asyncio.run(check_items())
    print(df)
