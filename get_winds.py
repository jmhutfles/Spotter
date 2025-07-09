import requests
import pandas as pd
from datetime import datetime

def get_winds_aloft(latitude, longitude):
    """
    Get current winds aloft data from Open-Meteo API
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
    
    Returns:
        pandas.DataFrame: Current winds aloft data with columns:
            - datetime: Current timestamp
            - altitude_m: Altitude in meters
            - wind_speed_mph: Wind speed in mph
            - wind_direction_deg: Wind direction in degrees
    """
    
    # Open-Meteo API endpoint
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Parameters for current winds aloft at different pressure levels
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'current': [
            'wind_speed_1000hPa',
            'wind_direction_1000hPa',
            'wind_speed_925hPa', 
            'wind_direction_925hPa',
            'wind_speed_850hPa',
            'wind_direction_850hPa',
            'wind_speed_700hPa',
            'wind_direction_700hPa',
            'wind_speed_500hPa',
            'wind_direction_500hPa',
            'wind_speed_300hPa',
            'wind_direction_300hPa'
        ],
        'wind_speed_unit': 'mph',
        'timezone': 'auto'
    }
    
    # Make API request
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    # Extract current data
    current = data['current']
    current_time = pd.to_datetime(current['time'])
    
    # Pressure levels and their approximate altitudes (in meters)
    levels = {
        '1000hPa': 100,    # Surface level
        '925hPa': 760,     # ~2,500 ft
        '850hPa': 1500,    # ~5,000 ft  
        '700hPa': 3000,    # ~10,000 ft
        '500hPa': 5500,    # ~18,000 ft
        '300hPa': 9000     # ~30,000 ft
    }
    
    # Build DataFrame for current time only
    rows = []
    for level, altitude in levels.items():
        speed_key = f'wind_speed_{level}'
        direction_key = f'wind_direction_{level}'
        
        if speed_key in current and direction_key in current:
            rows.append({
                'datetime': current_time,
                'altitude_m': altitude,
                'altitude_ft': int(altitude * 3.28084),
                'pressure_level': level,
                'wind_speed_mph': current[speed_key],
                'wind_direction_deg': current[direction_key]
            })
    
    # Create DataFrame and sort by altitude
    df = pd.DataFrame(rows)
    df = df.sort_values('altitude_m').reset_index(drop=True)
    
    return df

# Example usage
if __name__ == "__main__":
    # Test with coordinates (e.g., XKeys)
    lat, lon = 39.707250, -75.036050


    
    print(f"Getting current winds aloft for coordinates: {lat}, {lon}")
    winds_df = get_winds_aloft(lat, lon)
    
    print(f"\nDataFrame shape: {winds_df.shape}")
    print(f"Columns: {list(winds_df.columns)}")
    
    print(f"\nCurrent winds aloft ({winds_df['datetime'].iloc[0]}):")
    print(winds_df[['altitude_ft', 'wind_speed_mph', 'wind_direction_deg']])