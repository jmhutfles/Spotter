import math

def feet_to_lat_long_offset(east_feet, north_feet, reference_lat):
    """
    Convert drift in feet to lat/long offsets
    
    Args:
        east_feet (float): Eastward drift in feet
        north_feet (float): Northward drift in feet  
        reference_lat (float): Reference latitude for calculation
    
    Returns:
        tuple: (lat_offset, long_offset) in degrees
    """
    # Conversion factors
    feet_per_degree_lat = 364000  # Approximately constant
    feet_per_degree_long = 364000 * math.cos(math.radians(reference_lat))  # Varies with latitude
    
    # Convert feet to degree offsets
    lat_offset = north_feet / feet_per_degree_lat
    long_offset = east_feet / feet_per_degree_long
    
    return lat_offset, long_offset