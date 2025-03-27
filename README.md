# EcoMile Logistics

Revolutionizing Sustainable Last-Mile Delivery for a Greener Future

## Overview

EcoMile is an innovative Minimum Viable Product (MVP) designed to transform last-mile delivery logistics by prioritizing sustainability, efficiency, and collaboration. Built for a hackathon, EcoMile addresses the pressing challenges faced by logistics companies: rising fuel costs, environmental impact, and inefficient delivery routes. Our solution empowers delivery services to optimize routes, reduce CO2 emissions, and collaborate with competitors to share routes, thereby minimizing redundant trips and fostering a greener ecosystem.

EcoMile stands out by combining route optimization, real-time analytics, and a unique collaboration hub, all while integrating user-friendly features like voice input for address entry. The app not only helps companies save costs and reduce their carbon footprint but also gamifies sustainability through an EcoPoints leaderboard, encouraging eco-friendly practices. With a focus on usability and impact, EcoMile is a hackathon-ready solution poised to make a difference in the logistics industry.

## Key Features

1. **Route Optimization with EcoMode**:
   - Calculates the most efficient delivery routes using the OpenRouteService API.
   - Offers an "EcoMode" toggle to prioritize shorter, greener routes, reducing fuel consumption and CO2 emissions.

2. **Real-Time Analytics Dashboard**:
   - Displays key metrics such as total distance, CO2 emissions, fuel savings, cost savings, traffic impact, efficiency score, and sustainability score.
   - Provides actionable insights to help companies monitor and improve their environmental impact.

3. **Voice-Enabled Address Input**:
   - Leverages the Web Speech API to allow drivers to input delivery addresses hands-free, enhancing safety and efficiency.

4. **Collaboration Hub**:
   - Enables logistics companies to share routes with competitors, reducing redundant trips and earning EcoPoints for sustainable practices.
   - Features a user-friendly interface to propose goods, services, and routes for collaboration.

5. **EcoPoints Leaderboard**:
   - Gamifies sustainability by awarding EcoPoints for eco-friendly actions like using EcoMode and collaborating with competitors.
   - Displays a leaderboard to foster competition and encourage green practices.

6. **Safety Alerts**:
   - Identifies risky areas on routes (mocked for the MVP) to alert drivers, improving safety during deliveries.

7. **Map Persistence**:
   - Ensures the map state (route and markers) persists across page navigation using `localStorage`, providing a seamless user experience.

8. **User Authentication**:
   - Includes a login system with SQLite to manage user sessions securely, ensuring data privacy for each company.

## Tech Stack

- **Backend**: Flask (Python)
  - Handles route calculations, user authentication, and database interactions.

- **Frontend**:
  - **HTML & Tailwind CSS**: For a clean, responsive, and visually appealing user interface.
  - **JavaScript & Leaflet.js**: For interactive map rendering and route visualization.
  - **Web Speech API**: For voice-enabled address input.

- **Database**: SQLite
  - A lightweight, serverless database for storing user data, routes, collaboration requests, and leaderboard scores.

- **APIs**:
  - **OpenRouteService API**: Used for geocoding addresses and calculating optimized routes.
  - **Web Speech API**: A browser-based API for speech recognition.

- **Deployment**: **Vercel**
  - A free-tier hosting platform for Flask applications, enabling quick deployment and public access for hackathon judging.

## How to Use

### Prerequisites

- Python 3.x
- Flask
- SQLite

### Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/fairoz-539/EcoMile_Logistics.git
   cd EcoMile_Logistics

2. **Create a virtual environment and activate it:**

```sh
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. **Install the required dependencies:**

```sh
pip install -r requirements.txt
```

4. **Initialize the database:**

```sh
flask db init
flask db migrate
flask db upgrade
```

5. **Running the Application**
**Start the Flask development server:**

```sh
flask run
```

```Access the application in your web browser: Navigate to http://127.0.0.1:5000 to use EcoMile.
```

## Using the Features
 - Route Optimization: Enter delivery addresses and click on the "Optimize Route" button.
 - EcoMode: Toggle the EcoMode switch to prioritize greener routes.
 - Voice Input: Click on the microphone icon and speak the delivery address.
 - Collaboration Hub: Propose and share routes with competitors.
 - EcoPoints Leaderboard: Check the leaderboard to see your ranking and EcoPoints.
 - Safety Alerts: View alerts for risky areas on the route map.


## Contributing

 - We welcome contributions from the community! If you have suggestions or improvements, please open an issue or submit a pull request.

## Acknowledgements
 - OpenRouteService API
 - Web Speech API
 - Flask
 - Leaflet.js
 - Tailwind CSS

   
**EcoMile is more than just a delivery planner—it’s a movement toward sustainable logistics. By combining route optimization, voice input, and a collaboration hub, we’ve created a solution that reduces environmental impact, saves costs, and fosters cooperation in the logistics industry. With a solid technical foundation, a focus on sustainability, and a nod to Google’s innovative technologies, EcoMile is ready to make an impact at the hackathon and beyond.**
   
