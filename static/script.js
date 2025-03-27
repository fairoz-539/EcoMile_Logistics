// Initialize map
let map = null;
let vehicleMarker = null;
let competitorMarkers = [];
let pins = [];
let routeData = null;

// Load map state from localStorage
function initializeMap() {
    map = L.map('map').setView([51.505, -0.09], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Restore route if it exists
    const savedRoute = localStorage.getItem('routeData');
    if (savedRoute) {
        routeData = JSON.parse(savedRoute);
        displayRoute(routeData);
    }
}

// Vehicle icon
const vehicleIcon = L.icon({
    iconUrl: '/static/car.svg',
    iconSize: [40, 40],
    iconAnchor: [20, 20]
});

// Voice input setup
let mediaRecorder = null;
let audioChunks = [];

// Helper function to update voice status
function updateVoiceStatus(message, isError = false) {
    const voiceStatus = document.getElementById('voice-status');
    voiceStatus.textContent = message;
    voiceStatus.classList.remove('hidden', 'text-red-600', 'text-gray-600');
    voiceStatus.classList.add(isError ? 'text-red-600' : 'text-gray-600');
    setTimeout(() => voiceStatus.classList.add('hidden'), 3000);
}

// Add address entry
document.getElementById('add-address').addEventListener('click', () => {
    const addressList = document.getElementById('address-list');
    const count = addressList.getElementsByClassName('address-entry').length;
    const div = document.createElement('div');
    div.className = 'address-entry';
    div.innerHTML = `
        <label class="block text-sm text-gray-600">Delivery ${count}</label>
        <input type="text" class="address-input w-full p-2 bg-gray-100 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none" placeholder="Enter delivery address" required>
    `;
    addressList.appendChild(div);
    updateLaunchButton();
});

// Voice input
document.getElementById('voice-btn').addEventListener('click', async () => {
    const voiceBtn = document.getElementById('voice-btn');
    const voiceLoading = document.getElementById('voice-loading');

    // Check for browser support
    if (!navigator.mediaDevices || !window.MediaRecorder) {
        updateVoiceStatus('Your browser does not support audio recording.', true);
        return;
    }

    try {
        // Show loading spinner
        voiceLoading.classList.remove('hidden');
        voiceBtn.disabled = true;
        updateVoiceStatus('Requesting microphone access...');

        // Start recording
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            // Convert audio to blob
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const arrayBuffer = await audioBlob.arrayBuffer();
            const base64Audio = btoa(
                new Uint8Array(arrayBuffer).reduce(
                    (data, byte) => data + String.fromCharCode(byte),
                    ''
                )
            );

            console.log('Base64 Audio:', base64Audio.substring(0, 100) + '...');

            // Use SpeechRecognition API
            if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = 'en-US';
                recognition.interimResults = false;
                recognition.maxAlternatives = 1;

                recognition.onresult = (event) => {
                    if (event.results.length > 0) {
                        const transcribedAddress = event.results[0][0].transcript;
                        console.log('Transcribed Address:', transcribedAddress);
                        const addressInputs = document.getElementsByClassName('address-input');
                        const lastInput = addressInputs[addressInputs.length - 1];
                        lastInput.value = transcribedAddress;
                        lastInput.dispatchEvent(new Event('input'));
                        updateVoiceStatus('Address added: ' + transcribedAddress);
                    } else {
                        updateVoiceStatus('No speech detected. Please try again.', true);
                    }
                };

                recognition.onerror = (event) => {
                    console.error('SpeechRecognition Error:', event.error);
                    updateVoiceStatus('Failed to transcribe audio: ' + event.error, true);
                };

                recognition.onend = () => {
                    stream.getTracks().forEach(track => track.stop());
                    voiceLoading.classList.add('hidden');
                    voiceBtn.disabled = false;
                };

                recognition.start();
            } else {
                updateVoiceStatus('Speech recognition not supported in this browser.', true);
                stream.getTracks().forEach(track => track.stop());
                voiceLoading.classList.add('hidden');
                voiceBtn.disabled = false;
            }
        };

        // Start recording for 10 seconds
        mediaRecorder.start();
        updateVoiceStatus('Recording... Speak the address now.');
        setTimeout(() => {
            if (mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
            }
        }, 10000);  // Increased to 10 seconds
    } catch (error) {
        console.error('Error accessing microphone:', error);
        updateVoiceStatus('Failed to access microphone: ' + error.message, true);
        voiceLoading.classList.add('hidden');
        voiceBtn.disabled = false;
    }
});

// Update Launch button state
function updateLaunchButton() {
    const launchBtn = document.getElementById('launch-btn');
    const inputs = Array.from(document.getElementsByClassName('address-input')).filter(input => input.value);
    launchBtn.disabled = inputs.length < 2;
}

// Launch Route
document.getElementById('launch-btn').addEventListener('click', () => {
    const inputs = Array.from(document.getElementsByClassName('address-input')).filter(input => input.value);
    if (inputs.length < 2) {
        alert('Please enter at least one starting point and one delivery address.');
        return;
    }
    const addresses = inputs.map(input => input.value);

    fetch('/calculate_route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ addresses, ecoMode: document.getElementById('eco-mode').checked })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }

        routeData = data;
        localStorage.setItem('routeData', JSON.stringify(data));  // Save to localStorage
        displayRoute(data);

        // Show competitor modal
        document.getElementById('competitor-modal').classList.remove('hidden');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to calculate route.');
    });
});

// Display route
function displayRoute(data) {
    // Clear existing layers
    map.eachLayer(layer => {
        if (layer instanceof L.Polyline || layer instanceof L.Marker) map.removeLayer(layer);
    });
    pins = [];

    // Draw route
    const latlngs = data.geometry.map(coord => [coord[1], coord[0]]);
    L.polyline(latlngs, { color: '#3b82f6', weight: 4, opacity: 0.8 }).addTo(map);

    // Add markers
    data.locations.forEach((loc, index) => {
        const marker = L.marker([loc[1], loc[0]], {
            icon: L.divIcon({
                className: 'custom-marker',
                html: `<div class="pin ${index === 0 ? 'bg-blue-600' : 'bg-amber-500'} text-white rounded-full w-6 h-6 flex items-center justify-center">${index === 0 ? 'S' : index}</div>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            })
        }).addTo(map);
        pins.push({ marker, latlng: { lat: loc[1], lng: loc[0] } });
    });

    // Fit bounds
    map.fitBounds(latlngs);

    // Animate vehicle
    if (vehicleMarker) map.removeLayer(vehicleMarker);
    vehicleMarker = L.marker(latlngs[0], { icon: vehicleIcon }).addTo(map);
    let i = 0;
    function moveVehicle() {
        if (i < latlngs.length) {
            vehicleMarker.setLatLng(latlngs[i]);
            i++;
            setTimeout(moveVehicle, 50);
        } else {
            // Update analytics after route animation
            updateAnalytics(data);

            // Mock traffic alert
            if (data.analytics.traffic_impact > 5) {
                document.getElementById('traffic-alert').classList.remove('hidden');
            }

            // Show safety alert if risky areas are detected
            if (data.risky_areas && data.risky_areas.length > 0) {
                document.getElementById('safety-message').textContent = data.risky_areas[0].reason;
                document.getElementById('safety-alert').classList.remove('hidden');
            }

            // Show customer notification modal
            document.getElementById('notification-modal').classList.remove('hidden');
        }
    }
    moveVehicle();
}

// Update analytics cards
function updateAnalytics(data) {
    const analytics = data.analytics;

    // Total Distance
    const totalDistance = data.total_distance.toFixed(2);
    document.getElementById('total-distance').textContent = `${totalDistance} km`;
    document.getElementById('distance-trend').textContent = `+${Math.round(totalDistance / 10)}%`;
    document.getElementById('total-distance').parentElement.parentElement.classList.add('fade-in');

    // CO2 Emissions
    const totalCo2 = data.total_co2.toFixed(0);
    document.getElementById('total-co2').textContent = `${totalCo2} g`;
    document.getElementById('co2-trend').textContent = `+${Math.round(totalCo2 / 100)}%`;
    document.getElementById('total-co2').parentElement.parentElement.classList.add('fade-in');

    // Fuel Consumption
    const fuelConsumption = analytics.fuel_consumption.toFixed(2);
    document.getElementById('fuel-consumption').textContent = `${fuelConsumption} liters`;
    document.getElementById('fuel-trend').textContent = `+${Math.round(fuelConsumption / 1)}%`;
    document.getElementById('fuel-consumption').parentElement.parentElement.classList.add('fade-in');

    // Fuel Savings
    const fuelSavings = analytics.fuel_savings.toFixed(2);
    document.getElementById('fuel-savings').textContent = `${fuelSavings} liters`;
    document.getElementById('fuel-savings-trend').textContent = `+${Math.round(fuelSavings / 0.5)}%`;
    document.getElementById('fuel-savings').parentElement.parentElement.classList.add('fade-in');

    // Total Delivery Time
    const totalTime = analytics.delivery_times.reduce((sum, dt) => sum + dt.estimated_time, 0).toFixed(1);
    document.getElementById('total-time').textContent = `${totalTime} mins`;
    document.getElementById('time-trend').textContent = `+${Math.round(totalTime / 5)}%`;
    document.getElementById('total-time').parentElement.parentElement.classList.add('fade-in');

    // Cost Savings
    const costSavings = analytics.cost_savings.toFixed(2);
    document.getElementById('cost-savings').textContent = `$${costSavings}`;
    document.getElementById('cost-trend').textContent = `+${Math.round(costSavings / 2)}%`;
    document.getElementById('cost-savings').parentElement.parentElement.classList.add('fade-in');

    // Traffic Impact
    const trafficImpact = analytics.traffic_impact.toFixed(1);
    document.getElementById('traffic-impact').textContent = `${trafficImpact} mins`;
    document.getElementById('traffic-trend').textContent = `+${Math.round(trafficImpact / 1)}%`;
    document.getElementById('traffic-impact').parentElement.parentElement.classList.add('fade-in');

    // CO2 Savings vs Industry
    const co2Savings = analytics.co2_savings_vs_industry.toFixed(0);
    document.getElementById('co2-savings').textContent = `${co2Savings} g`;
    document.getElementById('co2-savings-trend').textContent = `+${Math.round(co2Savings / 100)}%`;
    document.getElementById('co2-savings').parentElement.parentElement.classList.add('fade-in');

    // Efficiency Score
    const efficiencyScore = analytics.efficiency_score.toFixed(0);
    document.getElementById('efficiency-score').textContent = `${efficiencyScore}/100`;
    document.getElementById('efficiency-trend').textContent = `+${Math.round(efficiencyScore / 10)}%`;
    document.getElementById('efficiency-score').parentElement.parentElement.classList.add('fade-in');

    // Sustainability Score
    const sustainabilityScore = Math.min(100, 100 - (data.total_co2 / 50)).toFixed(0);
    document.getElementById('sustainability-score').textContent = `${sustainabilityScore}/100`;
    document.getElementById('sustainability-trend').textContent = `+${Math.round(sustainabilityScore / 10)}%`;
    document.getElementById('sustainability-score').parentElement.parentElement.classList.add('fade-in');

    // Average Delivery Time
    const avgDeliveryTime = (totalTime / data.analytics.delivery_times.length).toFixed(1);
    document.getElementById('avg-delivery-time').textContent = `${avgDeliveryTime} mins`;
    document.getElementById('avg-time-trend').textContent = `+${Math.round(avgDeliveryTime / 2)}%`;
    document.getElementById('avg-delivery-time').parentElement.parentElement.classList.add('fade-in');

    // Driver Performance
    const driverPerformance = Math.min(100, efficiencyScore * 1.2).toFixed(0);
    document.getElementById('driver-performance').textContent = `${driverPerformance}/100`;
    document.getElementById('driver-trend').textContent = `+${Math.round(driverPerformance / 10)}%`;
    document.getElementById('driver-performance').parentElement.parentElement.classList.add('fade-in');
}

// Handle traffic re-routing (mocked)
document.getElementById('reroute-btn').addEventListener('click', () => {
    alert('Re-routing... (Mocked)');
    document.getElementById('traffic-alert').classList.add('hidden');
});

// Handle customer notification
document.getElementById('notify-ok').addEventListener('click', () => {
    alert('Notification sent to customer! (Mocked)');
    document.getElementById('notification-modal').classList.add('hidden');
});

document.getElementById('notify-skip').addEventListener('click', () => {
    document.getElementById('notification-modal').classList.add('hidden');
});

// Handle competitor modal
document.getElementById('competitor-ok').addEventListener('click', () => {
    document.getElementById('competitor-modal').classList.add('hidden');
    fetch('/get_competitor_routes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ geometry: routeData.geometry })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }

        // Display competitor routes
        data.competitor_routes.forEach(comp => {
            const latlngs = comp.geometry.map(coord => [coord[1], coord[0]]);
            L.polyline(latlngs, { color: '#ef4444', weight: 4, opacity: 0.8, dashArray: '5, 10' }).addTo(map);
            const marker = L.marker(latlngs[0], { icon: vehicleIcon }).addTo(map);
            let i = 0;
            function moveCompetitor() {
                if (i < latlngs.length) {
                    marker.setLatLng(latlngs[i]);
                    i++;
                    setTimeout(moveCompetitor, 50);
                }
            }
            moveCompetitor();
            competitorMarkers.push(marker);
        });

        // Show collaboration modal
        const competitorId = data.competitor_routes[0].competitor_id;
        document.getElementById('collaboration-text').textContent = `Interested in a deal with ${competitorId} sharing this route?`;
        document.getElementById('collaboration-modal').classList.remove('hidden');
        window.currentCompetitorId = competitorId;
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to fetch competitor routes.');
    });
});

document.getElementById('competitor-skip').addEventListener('click', () => {
    document.getElementById('competitor-modal').classList.add('hidden');
});

// Handle collaboration modal
document.getElementById('collaboration-proceed').addEventListener('click', () => {
    window.location.href = `/collaboration_hub?competitor_id=${window.currentCompetitorId}`;
});

document.getElementById('collaboration-cancel').addEventListener('click', () => {
    document.getElementById('collaboration-modal').classList.add('hidden');
});

document.getElementById('collaboration-close').addEventListener('click', () => {
    document.getElementById('collaboration-modal').classList.add('hidden');
});

// Update launch button on input
document.getElementById('address-list').addEventListener('input', updateLaunchButton);

// Initialize map on page load
window.onload = function() {
    initializeMap();
    const routeData = JSON.parse(localStorage.getItem('routeData'));
    if (routeData) {
        displayRoute(routeData);
    }
};