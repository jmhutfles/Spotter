from get_winds import get_winds_aloft
from physics import calculate_FF_drift, calculate_canopy_drift
from coord_math import feet_to_lat_long_offset
import math

#Define Variables
#Skydive Cross Keys
lat = 39.707250
long = -75.036050

# Target landing coordinates (same as dropzone for now)
target_lat = lat
target_long = long

#First Step is to Get Winds
raw_winds = get_winds_aloft(lat, long)

#Calculate Drift
ff_drift = calculate_FF_drift(raw_winds)
canopy_drift = calculate_canopy_drift(raw_winds)

total_north_drift = ff_drift['total_drift_north_feet'] + canopy_drift['total_drift_north_feet']
total_east_drift = ff_drift['total_drift_east_feet'] + canopy_drift['total_drift_east_feet']

print(f"Total drift: East {total_east_drift:.0f} ft, North {total_north_drift:.0f} ft")

# Calculate the offset needed to compensate for drift
lat_offset, long_offset = feet_to_lat_long_offset(total_east_drift, total_north_drift, lat)

# Ideal exit point is UPWIND of target (subtract the drift)
ideal_exit_lat = target_lat - lat_offset
ideal_exit_long = target_long - long_offset

print(f"\nTarget Landing: {target_lat:.6f}, {target_long:.6f}")
print(f"Ideal Exit:     {ideal_exit_lat:.6f}, {ideal_exit_long:.6f}")

