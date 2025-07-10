from get_winds import get_winds_aloft
from physics import calculate_FF_drift, calculate_canopy_drift
from coord_math import feet_to_lat_long_offset
import math
from plotting import plot_jump_map

#Define Variables
#Skydive Cross Keys
lat = 39.707250
long = -75.036050

canopy_glide_circle_miles = 1  # Glide circle radius in miles

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

# Calculate the offset needed to compensate for drift
lat_offset, long_offset = feet_to_lat_long_offset(total_east_drift, total_north_drift, lat)

# Ideal exit point is UPWIND of target (subtract the drift)
ideal_exit_lat = target_lat - lat_offset
ideal_exit_long = target_long - long_offset

#plot it!
plot_jump_map(ideal_exit_lat, ideal_exit_long, target_lat, target_long, canopy_glide_circle_miles, output_file="jump_map.html")