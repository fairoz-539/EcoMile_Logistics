from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import openrouteservice
import random
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key for production

# Configure OpenRouteService client
ors_client = openrouteservice.Client(key='5b3ce3597851110001cf624882e76173985f4cfaa6282130d090ef18')  # Replace with your API key

# Database setup with migration
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    # Routes table (initial creation)
    c.execute('''CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        addresses TEXT NOT NULL,
        geometry TEXT NOT NULL,
        total_distance REAL,
        total_co2 REAL,
        analytics TEXT,
        created_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    # Leaderboard table
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    # Collaboration requests table
    c.execute('''CREATE TABLE IF NOT EXISTS collaboration_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        competitor_id TEXT,
        goods TEXT,
        services TEXT,
        routes TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    # Migration: Add 'locations' and 'risky_areas' columns to routes table if they don't exist
    try:
        c.execute('ALTER TABLE routes ADD COLUMN locations TEXT')
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            raise e  # Re-raise if it's not a duplicate column error
    try:
        c.execute('ALTER TABLE routes ADD COLUMN risky_areas TEXT')
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            raise e
    conn.commit()
    conn.close()

init_db()

# Mock competitor data
competitor_data = {
    "competitor_1": {
        "geometry": [[-0.09, 51.505], [-0.08, 51.506], [-0.07, 51.507]]
    },
    "competitor_2": {
        "geometry": [[-0.10, 51.504], [-0.09, 51.505], [-0.08, 51.506]]
    }
}

# Middleware to protect routes
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            # Initialize leaderboard entry for the user
            c.execute('INSERT OR IGNORE INTO leaderboard (user_id, points) VALUES (?, 0)', (user[0],))
            conn.commit()
            conn.close()
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            conn.close()
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Fetch the latest route for the user
    c.execute('SELECT * FROM routes WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (session['user_id'],))
    latest_route = c.fetchone()
    route_data = None
    if latest_route:
        try:
            # Adjust indices based on the updated schema
            route_data = {
                'id': latest_route[0],
                'addresses': json.loads(latest_route[2]) if latest_route[2] else [],
                'geometry': json.loads(latest_route[3]) if latest_route[3] else [],
                'total_distance': latest_route[4] if latest_route[4] is not None else 0,
                'total_co2': latest_route[5] if latest_route[5] is not None else 0,
                'analytics': json.loads(latest_route[6]) if latest_route[6] else {},
                'locations': json.loads(latest_route[7]) if len(latest_route) > 7 and latest_route[7] else [],
                'risky_areas': json.loads(latest_route[8]) if len(latest_route) > 8 and latest_route[8] else []
            }
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError in index route: {e}, data: {latest_route}")
            route_data = None  # Fallback to None if parsing fails
    conn.close()
    return render_template('index.html', route_data=route_data)

@app.route('/calculate_route', methods=['POST'])
@login_required
def calculate_route():
    data = request.get_json()
    addresses = data.get('addresses', [])
    eco_mode = data.get('ecoMode', False)

    if len(addresses) < 2:  # Require at least two addresses
        return jsonify({"error": "At least two addresses are required."}), 400

    try:
        # Geocode addresses
        locations = []
        for address in addresses:
            geocode = ors_client.pelias_search(address)
            if not geocode['features']:
                return jsonify({"error": f"Could not geocode address: {address}"}), 400
            coords = geocode['features'][0]['geometry']['coordinates']
            locations.append(coords)

        # Calculate route
        coords = [[lon, lat] for lon, lat in locations]
        route = ors_client.directions(
            coordinates=coords,
            profile='driving-car',
            format='geojson',
            instructions=False,
            preference='recommended' if not eco_mode else 'shortest'
        )

        # Extract route data
        geometry = route['features'][0]['geometry']['coordinates']
        total_distance = route['features'][0]['properties']['summary']['distance'] / 1000  # Convert to km
        total_duration = route['features'][0]['properties']['summary']['duration'] / 60  # Convert to minutes

        # Mock analytics (updated with realistic values)
        analytics = {
            "fuel_consumption": total_distance * 0.12,  # Realistic: 0.12 liters per km for a delivery van
            "fuel_savings": total_distance * 0.03 if eco_mode else 0,  # Realistic: 0.03 liters per km saved in eco mode
            "cost_savings": total_distance * 0.8 if eco_mode else 0,  # Realistic: $0.8 per km saved (assuming fuel cost)
            "traffic_impact": random.uniform(2, 15),  # Slightly adjusted for realism: 2-15 minutes delay
            "co2_savings_vs_industry": total_distance * 60 if eco_mode else 0,  # Realistic: 60g per km saved vs industry avg
            "efficiency_score": random.randint(75, 95),  # Adjusted for realism
            "delivery_times": [{"stop": i, "estimated_time": total_duration / len(locations)} for i in range(len(locations))]
        }

        total_co2 = total_distance * 200  # Realistic: 200g CO2 per km for a delivery van

        # Mock risky areas for safety alerts
        risky_areas = []
        if total_distance > 10:  # Mock: Assume routes over 10km have a risky area
            risky_areas.append({"location": "Midpoint", "reason": "High traffic zone detected"})

        # Store route in database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''INSERT INTO routes (user_id, addresses, geometry, total_distance, total_co2, analytics, locations, risky_areas, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (session['user_id'], json.dumps(addresses), json.dumps(geometry), total_distance, total_co2, json.dumps(analytics), json.dumps(locations), json.dumps(risky_areas), datetime.now()))
        conn.commit()
        conn.close()

        return jsonify({
            "geometry": geometry,
            "locations": locations,
            "total_distance": total_distance,
            "total_co2": total_co2,
            "analytics": analytics,
            "risky_areas": risky_areas
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_competitor_routes', methods=['POST'])
@login_required
def get_competitor_routes():
    data = request.get_json()
    geometry = data.get('geometry', [])

    if not geometry:
        return jsonify({"error": "No route geometry provided."}), 400

    # Mock competitor routes
    competitor_routes = [
        {
            "competitor_id": "competitor_1",
            "geometry": competitor_data["competitor_1"]["geometry"]
        }
    ]

    return jsonify({"competitor_routes": competitor_routes})

@app.route('/collaboration_hub')
@login_required
def collaboration_hub():
    return render_template('collaboration.html')

@app.route('/submit_collaboration', methods=['POST'])
@login_required
def submit_collaboration():
    data = request.get_json()
    goods = data.get('goods', [])
    services = data.get('services', '')
    routes = data.get('routes', '')
    competitor_id = data.get('competitor_id', 'competitor_1')  # Default to competitor_1

    if not goods or not services:
        return jsonify({"error": "Please select goods and a service type."}), 400

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Award EcoPoints for collaboration (10 points per submission)
    c.execute('INSERT OR IGNORE INTO leaderboard (user_id, points) VALUES (?, 0)', (session['user_id'],))
    c.execute('UPDATE leaderboard SET points = points + 10 WHERE user_id = ?', (session['user_id'],))
    # Store collaboration request
    c.execute('''INSERT INTO collaboration_requests (user_id, competitor_id, goods, services, routes, created_at)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (session['user_id'], competitor_id, json.dumps(goods), services, routes, datetime.now()))
    conn.commit()
    conn.close()

    return jsonify({"message": "Collaboration offer sent! You earned 10 EcoPoints."})

@app.route('/leaderboard', methods=['GET'])
@login_required
def get_leaderboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT u.username, l.points
                 FROM leaderboard l
                 JOIN users u ON l.user_id = u.id
                 ORDER BY l.points DESC''')
    leaderboard = [{"user": row[0], "points": row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify({"leaderboard": leaderboard})

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Fetch collaboration requests
    c.execute('''SELECT competitor_id, goods, services, routes, status, created_at
                 FROM collaboration_requests
                 WHERE user_id = ?
                 ORDER BY created_at DESC''', (session['user_id'],))
    requests = []
    for row in c.fetchall():
        try:
            goods = json.loads(row[1]) if row[1] else []
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError in dashboard route for goods: {e}, data: {row[1]}")
            goods = []
        requests.append({
            "competitor_id": row[0],
            "goods": goods,
            "services": row[2],
            "routes": row[3],
            "status": row[4],
            "created_at": row[5]
        })
    # Fetch leaderboard points
    c.execute('SELECT points FROM leaderboard WHERE user_id = ?', (session['user_id'],))
    result = c.fetchone()
    points = result[0] if result else 0
    conn.close()
    return render_template('dashboard.html', requests=requests, points=points)

if __name__ == '__main__':
    app.run(debug=True)