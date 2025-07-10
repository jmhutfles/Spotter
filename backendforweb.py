from flask import Flask, render_template, request, jsonify, send_file
from get_winds import get_winds_aloft
from physics import calculate_FF_drift, calculate_canopy_drift
from coord_math import feet_to_lat_long_offset
from plotting import plot_jump_map
import os
import tempfile
import math

app = Flask(__name__)

@app.route('/')
def index():
    """Main page with form inputs"""
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate_jump():
    """Calculate jump parameters and generate map"""
    try:
        # Get form data
        data = request.get_json()
        lat = float(data.get('latitude', 39.707250))
        lon = float(data.get('longitude', -75.036050))
        canopy_glide_circle = float(data.get('glide_circle', 1.0))
        canopy_descent_rate = float(data.get('descent_rate', 8.5))
        
        # Target landing (same as input coordinates for now)
        target_lat = lat
        target_lon = lon
        
        # Get wind data
        raw_winds = get_winds_aloft(lat, lon)
        
        # Calculate drift
        ff_drift = calculate_FF_drift(raw_winds)
        canopy_drift = calculate_canopy_drift(raw_winds, canopy_descent_rate)
        
        # Calculate total drift
        total_north_drift = ff_drift['total_drift_north_feet'] + canopy_drift['total_drift_north_feet']
        total_east_drift = ff_drift['total_drift_east_feet'] + canopy_drift['total_drift_east_feet']
        
        # Calculate ideal exit point
        lat_offset, lon_offset = feet_to_lat_long_offset(total_east_drift, total_north_drift, lat)
        ideal_exit_lat = target_lat - lat_offset
        ideal_exit_lon = target_lon - lon_offset
        
        # Generate map HTML content
        map_obj = plot_jump_map(
            ideal_exit_lat, ideal_exit_lon, 
            target_lat, target_lon, 
            canopy_glide_circle,
            output_file=None  # Don't save to file
        )
        
        # Get map HTML
        map_html = map_obj._repr_html_()
        
        # Calculate summary statistics
        total_drift_distance = math.sqrt(total_east_drift**2 + total_north_drift**2)
        
        # Return results
        results = {
            'success': True,
            'map_html': map_html,
            'summary': {
                'exit_lat': round(ideal_exit_lat, 6),
                'exit_lon': round(ideal_exit_lon, 6),
                'landing_lat': round(target_lat, 6),
                'landing_lon': round(target_lon, 6),
                'total_drift_feet': round(total_drift_distance, 0),
                'total_drift_miles': round(total_drift_distance / 5280, 2),
                'freefall_drift_feet': round(ff_drift['total_drift_distance_feet'], 0),
                'canopy_drift_feet': round(canopy_drift['total_drift_distance_feet'], 0),
                'total_time_minutes': round((ff_drift['total_freefall_time_seconds'] + canopy_drift['total_canopy_time_seconds']) / 60, 1),
                'wind_direction': round(math.degrees(math.atan2(total_east_drift, total_north_drift)) % 360, 0)
            }
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)