"""
Service layer for managing manufacturer technical specifications.
Handles extraction of models from DB and coordination with loaders.
"""

import re
import asyncio
from typing import List, Dict, Optional, Tuple
import pandas as pd
from sqlalchemy import create_engine, text


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
        SELECT DISTINCT item_name, report_class
        FROM (
            SELECT item_name, report_class FROM dhv_reports
            WHERE :org = 'dhv'
            UNION ALL
            SELECT item_name, report_class FROM air_turquoise_reports
            WHERE :org = 'air-turquoise'
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
    grouped = df.groupby(['manufacturer', 'model']).agg({
        'size': ['count', lambda x: ', '.join(sorted(filter(None, set(x))))],
        'item_name': 'first'
    }).reset_index()
    
    grouped.columns = ['manufacturer', 'model', 'size_count', 'sizes', 'example_item_name']
    
    return grouped


# Example usage
async def main():
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


if __name__ == '__main__':
    asyncio.run(main())
