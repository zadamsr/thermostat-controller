"""
Thermostat Web Control App
Simple Flask web app for controlling Honeywell Home thermostat
"""

from flask import Flask, render_template, jsonify, request
import thermostat_api
import json
import os

app = Flask(__name__)

# Load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()


@app.route('/')
def index():
    """Serve the thermostat control interface."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current thermostat status with guest restrictions."""
    try:
        status = thermostat_api.get_thermostat_status()

        # Add guest restrictions to response
        restrictions = config['guest_restrictions']
        status['guest_restrictions'] = {
            'min_heat': restrictions['min_heat_setpoint'],
            'max_heat': restrictions['max_heat_setpoint'],
            'min_cool': restrictions['min_cool_setpoint'],
            'max_cool': restrictions['max_cool_setpoint'],
            'allow_mode_change': restrictions['allow_mode_change'],
            'allowed_modes': restrictions['allowed_modes'],
            'default_mode': restrictions['default_mode']
        }

        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/set_temperature', methods=['POST'])
def set_temp():
    """Set thermostat temperature with guest restriction validation."""
    try:
        data = request.json
        mode = data.get('mode')
        heat_setpoint = data.get('heat_setpoint')
        cool_setpoint = data.get('cool_setpoint')
        device_id = data.get('device_id')
        location_id = data.get('location_id')

        if not all([mode, heat_setpoint, cool_setpoint, device_id, location_id]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Enforce guest restrictions
        restrictions = config['guest_restrictions']

        # Check mode restrictions
        if not restrictions['allow_mode_change']:
            # Preserve the thermostat's current live mode when guests are not
            # allowed to switch between Heat/Cool/Off.
            current_status = thermostat_api.get_thermostat_status()
            mode = current_status.get('mode') or restrictions['default_mode']
        elif mode not in restrictions['allowed_modes']:
            return jsonify({"error": f"Mode '{mode}' is not allowed"}), 403

        # Check temperature restrictions
        if heat_setpoint < restrictions['min_heat_setpoint']:
            heat_setpoint = restrictions['min_heat_setpoint']
        if heat_setpoint > restrictions['max_heat_setpoint']:
            heat_setpoint = restrictions['max_heat_setpoint']

        if cool_setpoint < restrictions['min_cool_setpoint']:
            cool_setpoint = restrictions['min_cool_setpoint']
        if cool_setpoint > restrictions['max_cool_setpoint']:
            cool_setpoint = restrictions['max_cool_setpoint']

        thermostat_api.set_temperature(
            device_id, location_id, mode, heat_setpoint, cool_setpoint
        )

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Run on all interfaces so it's accessible on the local network
    app.run(host='0.0.0.0', port=5000, debug=True)
