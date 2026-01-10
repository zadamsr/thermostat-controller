# Resideo Thermostat Control

Control your Honeywell Home (Resideo) thermostat via command line or web interface.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Your credentials are already in the `.env` file:
- `RESIDEO_CLIENT_ID`: Your Consumer Key
- `RESIDEO_CLIENT_SECRET`: Your Consumer Secret

### 3. Get Refresh Token

Run the authorization script to obtain a refresh token:

```bash
python get_refresh_token.py
```

This will:
1. Open your browser to authorize the app
2. Start a local server to capture the callback
3. Exchange the authorization code for tokens
4. Save the refresh token to your `.env` file

## Usage

### Web Interface (Recommended for Airbnb)

Start the web server:

```bash
python app.py
```

The web interface will be available at:
- Local: `http://localhost:5000`
- Network: `http://YOUR_LOCAL_IP:5000` (accessible from any device on your WiFi)

To find your local IP:
```bash
# On Mac/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# On Windows
ipconfig
```

**Features:**
- Dark mode professional interface
- Touch-friendly temperature controls
- Real-time status updates
- Works on any device with a web browser
- Perfect for Airbnb guests with QR code access
- Guest restrictions via `config.json` (limit temps, disable mode changes)

### Command Line

Control your thermostat with these commands:

#### Heat Mode
```bash
python thermostat.py Heat 70
```

#### Cool Mode
```bash
python thermostat.py Cool 74
```

#### Auto Mode
```bash
python thermostat.py Auto 68 75
```
(Sets heat to 68 and cool to 75)

## Guest Restrictions (config.json)

The web app includes guest restrictions to control what Airbnb guests can change. Edit `config.json` to customize:

```json
{
  "guest_restrictions": {
    "min_heat_setpoint": 65,        // Minimum temp guests can set in Heat mode
    "max_heat_setpoint": 72,        // Maximum temp guests can set in Heat mode
    "min_cool_setpoint": 70,        // Minimum temp guests can set in Cool mode
    "max_cool_setpoint": 78,        // Maximum temp guests can set in Cool mode
    "allow_mode_change": false,     // Can guests change Heat/Cool/Off modes?
    "allowed_modes": ["Heat"],      // Which modes are allowed (if enabled)
    "default_mode": "Heat"          // Mode to use if guests can't change it
  }
}
```

**Example configurations:**

**Winter Airbnb (Heat only, 65-72°F):**
```json
"allow_mode_change": false,
"default_mode": "Heat",
"min_heat_setpoint": 65,
"max_heat_setpoint": 72
```

**Summer Airbnb (Cool only, 70-78°F):**
```json
"allow_mode_change": false,
"default_mode": "Cool",
"min_cool_setpoint": 70,
"max_cool_setpoint": 78
```

**Full control (let guests change everything):**
```json
"allow_mode_change": true,
"allowed_modes": ["Heat", "Cool", "Off"]
```

After changing `config.json`, restart the web server for changes to take effect.

## How It Works

1. The script reads credentials from `.env`
2. Uses the refresh token to get an access token
3. Retrieves your location and thermostat device ID
4. Sends the temperature command to the API
5. Automatically refreshes the access token when needed
6. Web app enforces guest restrictions from `config.json`

## Troubleshooting

### "ERROR: Missing RESIDEO_REFRESH_TOKEN"
Run `python get_refresh_token.py` to obtain a new refresh token.

### "401 Unauthorized"
Your refresh token may have expired. Run `python get_refresh_token.py` again.

### "No locations found"
Ensure your Honeywell Home account has at least one location with a thermostat.

## Security Notes

- Never commit your `.env` file to version control
- The `.gitignore` file is configured to exclude it
- Refresh tokens can be invalidated by changing your Resideo account password
