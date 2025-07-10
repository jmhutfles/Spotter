"""
Database of popular skydiving dropzones with their coordinates
"""

DROPZONES = {
    "US_EAST": {
        "Skydive Cross Keys (NJ)": {"lat": 39.707250, "lon": -75.036050}
    }
}

def get_all_dropzones():
    """Return all dropzones as a flat dictionary"""
    all_dzs = {}
    for region, dzs in DROPZONES.items():
        all_dzs.update(dzs)
    return all_dzs

def get_dropzones_by_region():
    """Return dropzones organized by region"""
    return DROPZONES

def search_dropzone(name):
    """Search for a dropzone by name (case insensitive)"""
    all_dzs = get_all_dropzones()
    name_lower = name.lower()
    
    # Exact match first
    for dz_name, coords in all_dzs.items():
        if dz_name.lower() == name_lower:
            return dz_name, coords
    
    # Partial match
    for dz_name, coords in all_dzs.items():
        if name_lower in dz_name.lower():
            return dz_name, coords
    
    return None, None

def add_dropzone(region, name, lat, lon):
    """Add a new dropzone to the database"""
    if region not in DROPZONES:
        DROPZONES[region] = {}
    DROPZONES[region][name] = {"lat": lat, "lon": lon}

# Example usage
if __name__ == "__main__":
    print("Available dropzones:")
    for region, dzs in DROPZONES.items():
        print(f"\n{region}:")
        for name, coords in dzs.items():
            print(f"  {name}: {coords['lat']}, {coords['lon']}")
    
    # Test search
    name, coords = search_dropzone("Cross Keys")
    if coords:
        print(f"\nFound: {name} at {coords}")