import folium
import math

def plot_jump_map(exit_lat, exit_lon, landing_lat, landing_lon, circle_radius_miles, output_file="jump_map.html"):
    """
    Plot exit point and landing zone on satellite map with glide circle
    
    Args:
        exit_lat (float): Exit point latitude
        exit_lon (float): Exit point longitude
        landing_lat (float): Landing zone latitude
        landing_lon (float): Landing zone longitude
        circle_radius_miles (float): Glide circle radius in miles
        output_file (str): Output HTML file name
    
    Returns:
        folium.Map: The created map object
    """
    
    # Calculate center point for map view
    center_lat = (exit_lat + landing_lat) / 2
    center_lon = (exit_lon + landing_lon) / 2
    
    # Calculate distance between points to set zoom level
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in miles"""
        lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 3959 * c  # Earth radius in miles
    
    distance = calculate_distance(exit_lat, exit_lon, landing_lat, landing_lon)
    
    # Set zoom level based on distance and circle size
    max_dimension = max(distance, circle_radius_miles * 2)
    if max_dimension < 0.5:
        zoom_level = 16
    elif max_dimension < 1:
        zoom_level = 15
    elif max_dimension < 2:
        zoom_level = 14
    elif max_dimension < 5:
        zoom_level = 13
    else:
        zoom_level = 12
    
    # Create map with satellite imagery
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles=None
    )
    
    # Add satellite tile layer
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add OpenStreetMap layer as alternative
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='Street Map',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add exit point marker (airplane icon)
    folium.Marker(
        location=[exit_lat, exit_lon],
        popup=f'Exit Point<br>Lat: {exit_lat:.6f}<br>Lon: {exit_lon:.6f}',
        tooltip='Exit Point',
        icon=folium.Icon(color='blue', icon='plane', prefix='fa')
    ).add_to(m)
    
    # Add landing zone marker (target icon)
    folium.Marker(
        location=[landing_lat, landing_lon],
        popup=f'Landing Zone<br>Lat: {landing_lat:.6f}<br>Lon: {landing_lon:.6f}',
        tooltip='Landing Zone',
        icon=folium.Icon(color='red', icon='bullseye', prefix='fa')
    ).add_to(m)
    
    # Add line between exit and landing
    folium.PolyLine(
        locations=[[exit_lat, exit_lon], [landing_lat, landing_lon]],
        color='yellow',
        weight=3,
        opacity=0.8,
        popup=f'Drift Line<br>Distance: {distance:.2f} miles'
    ).add_to(m)
    
    # Add glide circle around exit point
    folium.Circle(
        location=[exit_lat, exit_lon],
        radius=circle_radius_miles * 1609.34,  # Convert miles to meters
        color='green',
        weight=2,
        fill=True,
        fillColor='green',
        fillOpacity=0.1,
        popup=f'Glide Circle<br>Radius: {circle_radius_miles} miles'
    ).add_to(m)
    
    # Add distance and bearing info
    def calculate_bearing(lat1, lon1, lat2, lon2):
        """Calculate bearing between two points"""
        lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
        dlon = lon2_r - lon1_r
        y = math.sin(dlon) * math.cos(lat2_r)
        x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon)
        bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
        return bearing
    
    bearing = calculate_bearing(exit_lat, exit_lon, landing_lat, landing_lon)
    
    # Add info box
    info_html = f"""
    <div style='position: fixed; 
                top: 10px; left: 50px; width: 250px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px'>
    <h4>Jump Information</h4>
    <b>Distance:</b> {distance:.2f} miles<br>
    <b>Bearing:</b> {bearing:.0f}°<br>
    <b>Glide Circle:</b> {circle_radius_miles} miles<br>
    <b>Exit:</b> {exit_lat:.4f}, {exit_lon:.4f}<br>
    <b>Landing:</b> {landing_lat:.4f}, {landing_lon:.4f}
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(info_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    m.save(output_file)
    
    
    return m

def plot_simple_map(lat, lon, circle_radius_miles, title="Jump Map", output_file="simple_map.html"):
    """
    Plot a simple map with just one point and circle
    
    Args:
        lat (float): Point latitude
        lon (float): Point longitude
        circle_radius_miles (float): Circle radius in miles
        title (str): Map title
        output_file (str): Output HTML file name
    """
    
    # Create map
    m = folium.Map(
        location=[lat, lon],
        zoom_start=14,
        tiles=None
    )
    
    # Add satellite imagery
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add marker
    folium.Marker(
        location=[lat, lon],
        popup=f'{title}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}',
        tooltip=title,
        icon=folium.Icon(color='red', icon='bullseye', prefix='fa')
    ).add_to(m)
    
    # Add circle
    folium.Circle(
        location=[lat, lon],
        radius=circle_radius_miles * 1609.34,  # Convert miles to meters
        color='blue',
        weight=2,
        fill=True,
        fillColor='blue',
        fillOpacity=0.2,
        popup=f'Radius: {circle_radius_miles} miles'
    ).add_to(m)
    
    # Save map
    m.save(output_file)
    print(f"Simple map saved to {output_file}")
    
    return m

# Example usage
if __name__ == "__main__":
    # Test coordinates (Skydive Cross Keys)
    exit_lat = 39.707250
    exit_lon = -75.036050
    landing_lat = 39.707250  
    landing_lon = -75.036050
    circle_radius = 1.5
    
    # Create jump map
    jump_map = plot_jump_map(
        exit_lat, exit_lon, 
        landing_lat, landing_lon, 
        circle_radius,
        "jump_analysis.html"
    )
    
    # Create simple map
    simple_map = plot_simple_map(
        exit_lat, exit_lon,
        circle_radius,
        "Exit Point",
        "exit_point.html"
    )
    
    print("Maps created! Open the HTML files in your browser to view.")