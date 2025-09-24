#!/usr/bin/env python3
"""
Fix for data alignment issues in macro announcement analysis.

This script fixes the sparse data problem by properly aligning timestamps
and filling missing values for event study analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def fix_aligned_data():
    """Fix the aligned data by properly handling timestamps and missing values."""
    
    # Read the current aligned data
    aligned_file = project_root / "data/processed/aligned_data.csv"
    print(f"Reading aligned data from: {aligned_file}")
    
    if not aligned_file.exists():
        print("❌ Aligned data file not found!")
        return
    
    # Load data
    data = pd.read_csv(aligned_file, index_col=0, parse_dates=True)
    print(f"Original data shape: {data.shape}")
    print(f"Missing values per column:\n{data.isnull().sum()}")
    
    # Separate different asset types
    stock_columns = [col for col in data.columns if any(symbol in col for symbol in ['^GSPC', '^VIX', '^TNX', 'DX-Y'])]
    crypto_price_columns = [col for col in data.columns if 'price' in col and any(symbol in col for symbol in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'])]
    crypto_volume_columns = [col for col in data.columns if 'volume' in col and any(symbol in col for symbol in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'])]
    econ_columns = [col for col in data.columns if any(indicator in col for indicator in ['UNRATE', 'PAYEMS', 'CIVPART', 'CPIAUCSL', 'CPILFESL', 'PCEPI', 'PCEPILFE'])]
    
    print(f"\nData breakdown:")
    print(f"Stock columns: {len(stock_columns)}")
    print(f"Crypto price columns: {len(crypto_price_columns)}")
    print(f"Crypto volume columns: {len(crypto_volume_columns)}")
    print(f"Economic columns: {len(econ_columns)}")
    
    # Convert to daily frequency by aggregating intraday data
    print("\n🔧 Resampling to daily frequency...")
    daily_data = data.resample('D').last()  # Use last price of each day
    
    # Forward fill missing values for up to 7 days
    print("🔧 Forward filling missing values...")
    daily_data = daily_data.fillna(method='ffill', limit=7)
    
    # For economic data (typically monthly/quarterly), forward fill for longer periods
    for col in econ_columns:
        if col in daily_data.columns:
            daily_data[col] = daily_data[col].fillna(method='ffill', limit=90)  # 3 months
    
    # Remove rows where all price columns are NaN
    price_columns = stock_columns + crypto_price_columns
    if price_columns:
        # Keep rows where at least one price column has data
        mask = daily_data[price_columns].notna().any(axis=1)
        daily_data = daily_data[mask]
    
    # Drop rows where all values are NaN
    daily_data = daily_data.dropna(how='all')
    
    print(f"Daily data shape after cleaning: {daily_data.shape}")
    print(f"Date range: {daily_data.index.min()} to {daily_data.index.max()}")
    print(f"Missing values after cleaning:\n{daily_data.isnull().sum()}")
    
    # Save the fixed data
    print("\n💾 Saving fixed data...")
    daily_data.to_csv(aligned_file)
    print(f"✅ Fixed data saved to: {aligned_file}")
    
    # Update metadata
    metadata_file = project_root / "data/processed/data_metadata.json"
    if metadata_file.exists():
        import json
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Update metadata
        metadata.update({
            "processed_date": pd.Timestamp.now().isoformat(),
            "data_shape": list(daily_data.shape),
            "date_range": {
                "start": str(daily_data.index.min()),
                "end": str(daily_data.index.max())
            },
            "columns": list(daily_data.columns),
            "stock_columns": stock_columns,
            "crypto_columns": crypto_price_columns,
            "economic_columns": econ_columns,
            "missing_values_per_column": daily_data.isnull().sum().to_dict(),
            "data_cleaning_applied": True
        })
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✅ Metadata updated: {metadata_file}")
    
    return daily_data

def create_clean_datasets():
    """Create separate clean datasets for stocks and crypto."""
    
    # Read the fixed aligned data
    aligned_file = project_root / "data/processed/aligned_data.csv"
    data = pd.read_csv(aligned_file, index_col=0, parse_dates=True)
    
    # Create separate stock and crypto datasets
    stock_columns = [col for col in data.columns if any(symbol in col for symbol in ['^GSPC', '^VIX', '^TNX', 'DX-Y'])]
    crypto_columns = [col for col in data.columns if any(symbol in col for symbol in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'])]
    
    # Stock data
    if stock_columns:
        stock_data = data[stock_columns].dropna(how='all')
        stock_file = project_root / "data/processed/stock_data_clean.csv"
        stock_data.to_csv(stock_file)
        print(f"✅ Clean stock data saved: {stock_file} ({stock_data.shape})")
    
    # Crypto data (prices only for better quality)
    crypto_price_columns = [col for col in crypto_columns if 'price' in col]
    if crypto_price_columns:
        crypto_data = data[crypto_price_columns].dropna(how='all')
        crypto_file = project_root / "data/processed/crypto_data_clean.csv"
        crypto_data.to_csv(crypto_file)
        print(f"✅ Clean crypto data saved: {crypto_file} ({crypto_data.shape})")
    
    # Combined price data for event study
    price_columns = stock_columns + crypto_price_columns
    if price_columns:
        price_data = data[price_columns].dropna(how='all')
        price_file = project_root / "data/processed/price_data_for_events.csv"
        price_data.to_csv(price_file)
        print(f"✅ Price data for events saved: {price_file} ({price_data.shape})")

def fix_empty_charts():
    """Clear existing empty chart files so they get regenerated."""
    
    figures_dir = project_root / "results/figures"
    
    # List of files to remove
    files_to_remove = [
        "event_study/average_cumulative_abnormal_returns.png",
        "overview/all_price_series_overview.png", 
        "overview/stock_market_indices_overview.png"
    ]
    
    for file_path in files_to_remove:
        full_path = figures_dir / file_path
        if full_path.exists():
            full_path.unlink()
            print(f"🗑️  Removed empty chart: {full_path}")

if __name__ == "__main__":
    print("="*60)
    print("🔧 FIXING DATA ALIGNMENT ISSUES")
    print("="*60)
    
    # Fix the data alignment
    fixed_data = fix_aligned_data()
    
    # Create clean datasets
    create_clean_datasets()
    
    # Remove empty charts
    fix_empty_charts()
    
    print("\n" + "="*60)
    print("✅ DATA ALIGNMENT FIXES COMPLETED")
    print("="*60)
    print("\n📊 Next steps:")
    print("1. Run the analysis again: uv run main.py")
    print("2. The charts should now display proper data")
    print("3. Check results/figures/ for updated visualizations")