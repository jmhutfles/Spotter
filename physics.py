import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import quad

# Calculate CdA constant based on 200lb jumper at 120mph terminal velocity
def _calculate_cda():
    """Calculate CdA constant for freefall physics"""
    g = 32.174  # ft/s^2
    rho_sl = 0.002377  # slug/ft^3 (air density at sea level)
    terminal_velocity_mph = 120
    weight_lb = 200
    
    terminal_velocity_fps = terminal_velocity_mph * 5280 / 3600  # 176 ft/s
    weight_slug = weight_lb / g  # Convert to slugs
    
    # At terminal velocity: Weight = Drag
    # mg = 0.5 * rho * V^2 * CdA
    CdA = (2 * weight_slug * g) / (rho_sl * terminal_velocity_fps**2)
    return CdA

# Constant CdA value (calculated once)
CDA = _calculate_cda()  # ≈ 8.85 ft²

def calculate_FF_drift(winds_df):
    """
    Calculate horizontal drift during freefall using curve fitting and integration
    
    Args:
        winds_df (DataFrame): Wind data from get_winds_aloft() with columns:
            - altitude_ft: Altitude in feet
            - wind_speed_mph: Wind speed in mph
            - wind_direction_deg: Wind direction in degrees
    
    Returns:
        dict: Drift calculation results
    """
    exit_altitude_ft = 13500
    deployment_altitude_ft = 5000
    
    # Constants
    g = 32.174  # ft/s^2
    rho_sl = 0.002377  # slug/ft^3 (air density at sea level)
    weight_lb = 200
    weight_slug = weight_lb / g
    
    # Use ALL wind data for better interpolation - don't filter!
    ff_winds = winds_df.copy()
    
    if ff_winds.empty or len(ff_winds) < 2:
        return {"error": "Insufficient wind data for interpolation"}
    
    # Sort by altitude
    ff_winds = ff_winds.sort_values('altitude_ft').reset_index(drop=True)
    
    # Convert wind to components
    ff_winds['wind_east_mph'] = ff_winds['wind_speed_mph'] * np.sin(np.radians(ff_winds['wind_direction_deg']))
    ff_winds['wind_north_mph'] = ff_winds['wind_speed_mph'] * np.cos(np.radians(ff_winds['wind_direction_deg']))
    
    # Create interpolation functions for wind components
    altitudes = ff_winds['altitude_ft'].values
    wind_east = ff_winds['wind_east_mph'].values
    wind_north = ff_winds['wind_north_mph'].values
    
    # Create smooth interpolation functions using ALL available data
    try:
        wind_east_func = interp1d(altitudes, wind_east, kind='cubic', 
                                bounds_error=False, fill_value='extrapolate')
        wind_north_func = interp1d(altitudes, wind_north, kind='cubic', 
                                 bounds_error=False, fill_value='extrapolate')
        interpolation_method = "cubic"
    except:
        # Fall back to linear if cubic fails
        wind_east_func = interp1d(altitudes, wind_east, kind='linear', 
                                bounds_error=False, fill_value='extrapolate')
        wind_north_func = interp1d(altitudes, wind_north, kind='linear', 
                                 bounds_error=False, fill_value='extrapolate')
        interpolation_method = "linear"
    
    def air_density(altitude_ft):
        """Calculate air density at altitude"""
        return rho_sl * (1 - 6.5756e-6 * altitude_ft)**4.2561
    
    def terminal_velocity(altitude_ft):
        """Calculate terminal velocity at altitude (ft/s)"""
        rho = air_density(altitude_ft)
        return np.sqrt((2 * weight_slug * g) / (rho * CDA))
    
    def drift_rate_east(altitude_ft):
        """Calculate eastward drift rate (ft/ft of altitude)"""
        # Wind speed in ft/s
        wind_east_fps = wind_east_func(altitude_ft) * 5280 / 3600
        # Terminal velocity in ft/s (negative because falling)
        term_vel = -terminal_velocity(altitude_ft)
        # Drift per unit altitude change
        return wind_east_fps / term_vel
    
    def drift_rate_north(altitude_ft):
        """Calculate northward drift rate (ft/ft of altitude)"""
        # Wind speed in ft/s
        wind_north_fps = wind_north_func(altitude_ft) * 5280 / 3600
        # Terminal velocity in ft/s (negative because falling)
        term_vel = -terminal_velocity(altitude_ft)
        # Drift per unit altitude change
        return wind_north_fps / term_vel
    
    def time_rate(altitude_ft):
        """Calculate time rate (s/ft of altitude)"""
        # Time per unit altitude change
        term_vel = terminal_velocity(altitude_ft)
        return 1 / term_vel
    
    # Integrate drift over the FREEFALL altitude range only
    try:
        drift_east, _ = quad(drift_rate_east, deployment_altitude_ft, exit_altitude_ft)
        drift_north, _ = quad(drift_rate_north, deployment_altitude_ft, exit_altitude_ft)
        total_time, _ = quad(time_rate, deployment_altitude_ft, exit_altitude_ft)
    except Exception as e:
        return {"error": f"Integration failed: {str(e)}"}
    
    # Calculate total drift distance and direction
    total_drift_distance = np.sqrt(drift_east**2 + drift_north**2)
    drift_direction = np.degrees(np.arctan2(drift_east, drift_north)) % 360
    
    # Create detailed breakdown for visualization (freefall range only)
    altitude_points = np.linspace(exit_altitude_ft, deployment_altitude_ft, 20)
    breakdown = []
    
    for alt in altitude_points:
        breakdown.append({
            'altitude_ft': alt,
            'wind_east_mph': float(wind_east_func(alt)),
            'wind_north_mph': float(wind_north_func(alt)),
            'wind_speed_mph': np.sqrt(wind_east_func(alt)**2 + wind_north_func(alt)**2),
            'wind_direction_deg': np.degrees(np.arctan2(wind_east_func(alt), wind_north_func(alt))) % 360,
            'terminal_velocity_mph': terminal_velocity(alt) * 3600 / 5280,
            'air_density': air_density(alt)
        })
    
    results = {
        'total_freefall_time_seconds': total_time,
        'total_drift_east_feet': drift_east,
        'total_drift_north_feet': drift_north,
        'total_drift_distance_feet': total_drift_distance,
        'total_drift_distance_miles': total_drift_distance / 5280,
        'drift_direction_degrees': drift_direction,
        'CdA_constant': CDA,
        'jumper_weight_lb': weight_lb,
        'exit_altitude_ft': exit_altitude_ft,
        'deployment_altitude_ft': deployment_altitude_ft,
        'interpolation_breakdown': breakdown,
        'interpolation_method': interpolation_method,
        'total_data_points_used': len(ff_winds),
        'data_altitude_range': f"{ff_winds['altitude_ft'].min():.0f} - {ff_winds['altitude_ft'].max():.0f} ft"
    }
    
    return results

def calculate_canopy_drift(winds_df, canopy_descent_rate_mph=12.5):
    """
    Calculate horizontal drift under canopy with constant descent rate
    
    Args:
        winds_df (DataFrame): Wind data from get_winds_aloft() 
        canopy_descent_rate_mph (float): Canopy descent rate in mph (default 12.5 mph)
    
    Returns:
        dict: Canopy drift calculation results
    """
    deployment_altitude_ft = 5000
    landing_altitude_ft = 0
    
    # Use ALL wind data for better interpolation
    canopy_winds = winds_df.copy()
    
    if canopy_winds.empty or len(canopy_winds) < 2:
        return {"error": "Insufficient wind data for interpolation"}
    
    # Sort by altitude
    canopy_winds = canopy_winds.sort_values('altitude_ft').reset_index(drop=True)
    
    # Convert wind to components
    canopy_winds['wind_east_mph'] = canopy_winds['wind_speed_mph'] * np.sin(np.radians(canopy_winds['wind_direction_deg']))
    canopy_winds['wind_north_mph'] = canopy_winds['wind_speed_mph'] * np.cos(np.radians(canopy_winds['wind_direction_deg']))
    
    # Create interpolation functions for wind components
    altitudes = canopy_winds['altitude_ft'].values
    wind_east = canopy_winds['wind_east_mph'].values
    wind_north = canopy_winds['wind_north_mph'].values
    
    # Create smooth interpolation functions
    try:
        wind_east_func = interp1d(altitudes, wind_east, kind='cubic', 
                                bounds_error=False, fill_value='extrapolate')
        wind_north_func = interp1d(altitudes, wind_north, kind='cubic', 
                                 bounds_error=False, fill_value='extrapolate')
        interpolation_method = "cubic"
    except:
        # Fall back to linear if cubic fails
        wind_east_func = interp1d(altitudes, wind_east, kind='linear', 
                                bounds_error=False, fill_value='extrapolate')
        wind_north_func = interp1d(altitudes, wind_north, kind='linear', 
                                 bounds_error=False, fill_value='extrapolate')
        interpolation_method = "linear"
    
    # Convert descent rate to ft/s
    descent_rate_fps = canopy_descent_rate_mph * 5280 / 3600
    
    def canopy_drift_rate_east(altitude_ft):
        """Calculate eastward drift rate under canopy (ft/ft of altitude)"""
        # Wind speed in ft/s
        wind_east_fps = wind_east_func(altitude_ft) * 5280 / 3600
        # Descent rate in ft/s (negative because descending)
        descent_vel = -descent_rate_fps
        # Drift per unit altitude change
        return wind_east_fps / descent_vel
    
    def canopy_drift_rate_north(altitude_ft):
        """Calculate northward drift rate under canopy (ft/ft of altitude)"""
        # Wind speed in ft/s
        wind_north_fps = wind_north_func(altitude_ft) * 5280 / 3600
        # Descent rate in ft/s (negative because descending)
        descent_vel = -descent_rate_fps
        # Drift per unit altitude change
        return wind_north_fps / descent_vel
    
    def canopy_time_rate(altitude_ft):
        """Calculate time rate under canopy (s/ft of altitude)"""
        # Time per unit altitude change (constant descent rate)
        return 1 / descent_rate_fps
    
    # Integrate drift over the CANOPY altitude range
    try:
        drift_east, _ = quad(canopy_drift_rate_east, landing_altitude_ft, deployment_altitude_ft)
        drift_north, _ = quad(canopy_drift_rate_north, landing_altitude_ft, deployment_altitude_ft)
        total_time, _ = quad(canopy_time_rate, landing_altitude_ft, deployment_altitude_ft)
    except Exception as e:
        return {"error": f"Integration failed: {str(e)}"}
    
    # Calculate total drift distance and direction
    total_drift_distance = np.sqrt(drift_east**2 + drift_north**2)
    drift_direction = np.degrees(np.arctan2(drift_east, drift_north)) % 360
    
    # Create detailed breakdown for visualization (canopy range only)
    altitude_points = np.linspace(deployment_altitude_ft, landing_altitude_ft, 15)
    breakdown = []
    
    for alt in altitude_points:
        breakdown.append({
            'altitude_ft': alt,
            'wind_east_mph': float(wind_east_func(alt)),
            'wind_north_mph': float(wind_north_func(alt)),
            'wind_speed_mph': np.sqrt(wind_east_func(alt)**2 + wind_north_func(alt)**2),
            'wind_direction_deg': np.degrees(np.arctan2(wind_east_func(alt), wind_north_func(alt))) % 360,
            'descent_rate_mph': canopy_descent_rate_mph
        })
    
    results = {
        'total_canopy_time_seconds': total_time,
        'total_drift_east_feet': drift_east,
        'total_drift_north_feet': drift_north,
        'total_drift_distance_feet': total_drift_distance,
        'total_drift_distance_miles': total_drift_distance / 5280,
        'drift_direction_degrees': drift_direction,
        'canopy_descent_rate_mph': canopy_descent_rate_mph,
        'deployment_altitude_ft': deployment_altitude_ft,
        'landing_altitude_ft': landing_altitude_ft,
        'interpolation_breakdown': breakdown,
        'interpolation_method': interpolation_method,
        'total_data_points_used': len(canopy_winds),
        'data_altitude_range': f"{canopy_winds['altitude_ft'].min():.0f} - {canopy_winds['altitude_ft'].max():.0f} ft"
    }
    
    return results

def calculate_total_drift(winds_df, canopy_descent_rate_mph=8.5):
    """
    Calculate total drift (freefall + canopy) and return combined results
    
    Args:
        winds_df (DataFrame): Wind data from get_winds_aloft()
        canopy_descent_rate_mph (float): Canopy descent rate in mph
    
    Returns:
        dict: Combined drift calculation results
    """
    
    # Calculate freefall drift
    ff_results = calculate_FF_drift(winds_df)
    if 'error' in ff_results:
        return ff_results
    
    # Calculate canopy drift
    canopy_results = calculate_canopy_drift(winds_df, canopy_descent_rate_mph)
    if 'error' in canopy_results:
        return canopy_results
    
    # Combine the drifts
    total_drift_east = ff_results['total_drift_east_feet'] + canopy_results['total_drift_east_feet']
    total_drift_north = ff_results['total_drift_north_feet'] + canopy_results['total_drift_north_feet']
    total_drift_distance = np.sqrt(total_drift_east**2 + total_drift_north**2)
    total_drift_direction = np.degrees(np.arctan2(total_drift_east, total_drift_north)) % 360
    total_time = ff_results['total_freefall_time_seconds'] + canopy_results['total_canopy_time_seconds']
    
    combined_results = {
        'freefall_results': ff_results,
        'canopy_results': canopy_results,
        'total_drift_east_feet': total_drift_east,
        'total_drift_north_feet': total_drift_north,
        'total_drift_distance_feet': total_drift_distance,
        'total_drift_distance_miles': total_drift_distance / 5280,
        'total_drift_direction_degrees': total_drift_direction,
        'total_jump_time_seconds': total_time,
        'total_jump_time_minutes': total_time / 60
    }
    
    return combined_results

def print_drift_summary(drift_results):
    """
    Print a formatted summary of drift calculations
    """
    if 'error' in drift_results:
        print(f"Error: {drift_results['error']}")
        return
    
    print("FREEFALL DRIFT CALCULATION (Curve Fitted)")
    print("=" * 45)
    print(f"Exit Altitude: {drift_results['exit_altitude_ft']:,} ft")
    print(f"Deployment Altitude: {drift_results['deployment_altitude_ft']:,} ft")
    print(f"Freefall Time: {drift_results['total_freefall_time_seconds']:.1f} seconds")
    print(f"Jumper Weight: {drift_results['jumper_weight_lb']} lbs")
    print(f"CdA Constant: {drift_results['CdA_constant']:.3f} ft²")
    print(f"Data Points Used: {drift_results['total_data_points_used']} ({drift_results['data_altitude_range']})")
    print(f"Interpolation Method: {drift_results['interpolation_method']}")
    print()
    print("DRIFT RESULTS:")
    print(f"Total Drift Distance: {drift_results['total_drift_distance_feet']:.0f} ft ({drift_results['total_drift_distance_miles']:.2f} miles)")
    print(f"Drift Direction: {drift_results['drift_direction_degrees']:.0f}°")
    print(f"East Component: {drift_results['total_drift_east_feet']:.0f} ft")
    print(f"North Component: {drift_results['total_drift_north_feet']:.0f} ft")
    print()
    print("INTERPOLATED WIND PROFILE (Freefall Range):")
    print(f"{'Altitude':>8} {'Wind Spd':>9} {'Wind Dir':>8} {'Term Vel':>8}")
    print(f"{'(ft)':>8} {'(mph)':>9} {'(deg)':>8} {'(mph)':>8}")
    print("-" * 40)
    
    breakdown = drift_results['interpolation_breakdown']
    for i in range(0, len(breakdown), 3):  # Show every 3rd point
        point = breakdown[i]
        print(f"{point['altitude_ft']:>8.0f} {point['wind_speed_mph']:>9.1f} "
              f"{point['wind_direction_deg']:>8.0f} {point['terminal_velocity_mph']:>8.1f}")

def print_canopy_summary(canopy_results):
    """
    Print a formatted summary of canopy drift calculations
    """
    if 'error' in canopy_results:
        print(f"Error: {canopy_results['error']}")
        return
    
    print("CANOPY DRIFT CALCULATION (Curve Fitted)")
    print("=" * 45)
    print(f"Deployment Altitude: {canopy_results['deployment_altitude_ft']:,} ft")
    print(f"Landing Altitude: {canopy_results['landing_altitude_ft']:,} ft")
    print(f"Canopy Time: {canopy_results['total_canopy_time_seconds']:.1f} seconds ({canopy_results['total_canopy_time_seconds']/60:.1f} minutes)")
    print(f"Descent Rate: {canopy_results['canopy_descent_rate_mph']} mph")
    print(f"Data Points Used: {canopy_results['total_data_points_used']} ({canopy_results['data_altitude_range']})")
    print(f"Interpolation Method: {canopy_results['interpolation_method']}")
    print()
    print("CANOPY DRIFT RESULTS:")
    print(f"Total Drift Distance: {canopy_results['total_drift_distance_feet']:.0f} ft ({canopy_results['total_drift_distance_miles']:.2f} miles)")
    print(f"Drift Direction: {canopy_results['drift_direction_degrees']:.0f}°")
    print(f"East Component: {canopy_results['total_drift_east_feet']:.0f} ft")
    print(f"North Component: {canopy_results['total_drift_north_feet']:.0f} ft")
    print()
    print("INTERPOLATED WIND PROFILE (Canopy Range):")
    print(f"{'Altitude':>8} {'Wind Spd':>9} {'Wind Dir':>8} {'Descent':>8}")
    print(f"{'(ft)':>8} {'(mph)':>9} {'(deg)':>8} {'(mph)':>8}")
    print("-" * 40)
    
    breakdown = canopy_results['interpolation_breakdown']
    for i in range(0, len(breakdown), 3):  # Show every 3rd point
        point = breakdown[i]
        print(f"{point['altitude_ft']:>8.0f} {point['wind_speed_mph']:>9.1f} "
              f"{point['wind_direction_deg']:>8.0f} {point['descent_rate_mph']:>8.1f}")

def print_total_summary(total_results):
    """
    Print a formatted summary of total drift calculations
    """
    if 'error' in total_results:
        print(f"Error: {total_results['error']}")
        return
    
    print("\n" + "="*60)
    print("TOTAL JUMP DRIFT SUMMARY")
    print("="*60)
    print(f"Total Jump Time: {total_results['total_jump_time_seconds']:.1f} seconds ({total_results['total_jump_time_minutes']:.1f} minutes)")
    print(f"Total Drift Distance: {total_results['total_drift_distance_feet']:.0f} ft ({total_results['total_drift_distance_miles']:.2f} miles)")
    print(f"Total Drift Direction: {total_results['total_drift_direction_degrees']:.0f}°")
    print(f"Total East Component: {total_results['total_drift_east_feet']:.0f} ft")
    print(f"Total North Component: {total_results['total_drift_north_feet']:.0f} ft")
    print()
    print("BREAKDOWN BY PHASE:")
    ff = total_results['freefall_results']
    canopy = total_results['canopy_results']
    print(f"Freefall:  {ff['total_drift_distance_feet']:.0f} ft in {ff['total_freefall_time_seconds']:.1f}s")
    print(f"Canopy:    {canopy['total_drift_distance_feet']:.0f} ft in {canopy['total_canopy_time_seconds']:.1f}s")

# Example usage - ONLY prints when run as main
if __name__ == "__main__":
    from get_winds import get_winds_aloft
    
    print(f"Calculated CdA constant: {CDA:.3f} ft²")
    print()
    
    # Get real wind data
    lat, lon = 39.707250, -75.036050
    print(f"Getting wind data for {lat}, {lon}...")
    
    try:
        winds_df = get_winds_aloft(lat, lon)
        print("Wind data retrieved successfully!")
        print(winds_df[['altitude_ft', 'wind_speed_mph', 'wind_direction_deg']])
        print()
        
        # Calculate total drift (freefall + canopy)
        total_results = calculate_total_drift(winds_df, canopy_descent_rate_mph=8.5)
        
        # Print detailed results
        print_drift_summary(total_results['freefall_results'])
        print()
        print_canopy_summary(total_results['canopy_results'])
        print_total_summary(total_results)
        
    except Exception as e:
        print(f"Error: {e}")