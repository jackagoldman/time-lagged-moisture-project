import numpy as np
import pandas as pd
import xarray as xr
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


# read in weather data
wx = pd.read_csv("/Users/jgoldman/Library/CloudStorage/GoogleDrive-jandrewgoldman@gmail.com/My Drive/2_SCHOOL/wx/ontario-complete-wx-data-90-21.csv")

print("Original data sample:")
print(wx.head())

# Check if there's already a date column in the dataset
print("\nColumns in the dataset:")
print(wx.columns.tolist())

# Assuming there's a date column named 'date' or similar
# First, let's try to identify the date column
date_columns = [col for col in wx.columns if 'date' in col.lower() or 'time' in col.lower()]
if date_columns:
    date_col = date_columns[0]
    print(f"\nFound date column: {date_col}")
    
    # Convert to datetime and extract year
    wx[date_col] = pd.to_datetime(wx[date_col], errors='coerce')
    wx['year'] = wx[date_col].dt.year
    
    # Display unique years
    years = wx['year'].unique()
    years.sort()
    print("\nUnique years in the dataset:")
    print(years)
    
    print(f"\nTotal number of years: {len(years)}")
    print(f"Year range: {min(years)} - {max(years)}")
else:
    print("\nNo obvious date column found. Please specify the date column name.")
    print("Available columns:", wx.columns.tolist())

# Show updated dataframe with year column
print("\nUpdated data sample:")
print(wx.head())




## Calculate VPD
print("\nCalculating Vapor Pressure Deficit (VPD)...")

# First, check if we have the necessary columns: temperature and relative humidity
temp_columns = [col for col in wx.columns if any(term in col.lower() for term in ['temp', 'temperature'])]
rh_columns = [col for col in wx.columns if any(term in col.lower() for term in ['rh', 'humidity', 'rel_hum'])]

if not temp_columns or not rh_columns:
    print("Could not find temperature or relative humidity columns.")
    print("Temperature columns found:", temp_columns)
    print("Humidity columns found:", rh_columns)
else:
    # Use the first found temperature and humidity columns
    temp_col = temp_columns[0]
    rh_col = rh_columns[0]
    print(f"Using temperature column: {temp_col}")
    print(f"Using humidity column: {rh_col}")
    
    # Function to calculate saturation vapor pressure (es) in kPa
    # Uses the Clausius-Clapeyron equation
    def calc_saturation_vp(temp_c):
        return 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))
    
    # Function to calculate actual vapor pressure (ea) in kPa
    def calc_actual_vp(es, rh):
        return es * (rh / 100.0)
    
    # Calculate VPD = es - ea
    wx['es'] = calc_saturation_vp(wx[temp_col])
    wx['ea'] = calc_actual_vp(wx['es'], wx[rh_col])
    wx['vpd'] = wx['es'] - wx['ea']
    
    # Display the results
    print("\nData with VPD calculations:")
    print(wx[['year', date_col, temp_col, rh_col, 'es', 'ea', 'vpd']].head())
    
    # Calculate daily averages if needed
    if 'station_id' in wx.columns:
        # Group by station_id and date to get daily averages
        daily_vpd = wx.groupby(['station_id', pd.Grouper(key=date_col, freq='D')]).agg({
            temp_col: 'mean',
            rh_col: 'mean',
            'vpd': 'mean'
        }).reset_index()
        
        print("\nDaily average VPD by station:")
        print(daily_vpd.head())
    
    # Basic statistics
    print("\nVPD Statistics:")
    print(wx['vpd'].describe())
    
    # Check for missing values
    print(f"\nMissing VPD values: {wx['vpd'].isna().sum()} out of {len(wx)}")
    
    #  Save the results
    wx.to_csv("~/Work/PhD/time-lagged-moisture-project/data/ont_shield_weather_station_1990_2021_vpd.csv", index=False)