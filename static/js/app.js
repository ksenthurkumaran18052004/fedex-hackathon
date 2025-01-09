function initMap() {
    const map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 13.0827, lng: 80.2707 },
        zoom: 7,
    });

    const directionsRenderers = [
        new google.maps.Polyline({ strokeColor: "#FF0000", strokeWeight: 4, map }),
        new google.maps.Polyline({ strokeColor: "#00FF00", strokeWeight: 4, map }),
        new google.maps.Polyline({ strokeColor: "#0000FF", strokeWeight: 4, map }),
    ];

    const originInput = document.getElementById("origin-input");
    const destinationInput = document.getElementById("destination-input");
    const originAutocomplete = new google.maps.places.Autocomplete(originInput);
    const destinationAutocomplete = new google.maps.places.Autocomplete(destinationInput);

    document.getElementById("route-form").addEventListener("submit", (e) => {
        e.preventDefault();

        const originPlace = originAutocomplete.getPlace();
        const destinationPlace = destinationAutocomplete.getPlace();
        const fuelEfficiency = document.getElementById("fuel-efficiency").value;
        const emissionFactor = document.getElementById("emission-factor").value;

        if (!originPlace || !destinationPlace) {
            alert("Please select valid origin and destination.");
            return;
        }

        fetch("/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                origin: {
                    lat: originPlace.geometry.location.lat(),
                    lng: originPlace.geometry.location.lng(),
                },
                destination: {
                    lat: destinationPlace.geometry.location.lat(),
                    lng: destinationPlace.geometry.location.lng(),
                },
                fuel_efficiency: fuelEfficiency,
                emission_factor: emissionFactor,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(`Error: ${data.error}`);
                    return;
                }

                const resultsDiv = document.getElementById("results");
                resultsDiv.innerHTML = "";

                data.routes.forEach((route, index) => {
                    const routePath = route.route_points.map(
                        (point) => new google.maps.LatLng(point.latitude, point.longitude)
                    );
                    directionsRenderers[index].setPath(routePath);

                    const routeDetails = `
                        <div style="margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 10px;">
                            <h3>Route ${index + 1}</h3>
                            <p><strong>Distance:</strong> ${route.distance}</p>
                            <p><strong>Duration:</strong> ${route.duration}</p>
                            <p><strong>Traffic Delay:</strong> ${route.traffic_delay}</p>
                            <p><strong>Emissions:</strong> ${route.emissions}</p>
                            <p><strong>Traffic Locations:</strong></p>
                            <ul>
                                ${route.traffic_locations
                                    .map(location => `<li>${location}</li>`)
                                    .join("")}
                            </ul>
                            <p><strong>Weather Data:</strong></p>
                            <ul>
                                ${route.weather_data
                                    .map((weather) => `<li>${weather.location}: ${weather.weather}</li>`)
                                    .join("")}
                            </ul>
                        </div>
                    `;
                    resultsDiv.innerHTML += routeDetails;
                });
            })
            .catch((error) => {
                console.error("Error:", error);
            });
    });
}

google.maps.event.addDomListener(window, "load", initMap);
