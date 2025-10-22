import json
import pandas as pd
from geopy.geocoders import Nominatim
import random
import time

def latLong(place):
    user_agent = random.randint(10000, 99999)
    geolocator = Nominatim(user_agent=str(user_agent))
    location = geolocator.geocode(place)
    latitude = location.latitude
    longitude = location.longitude
    full_address = location.address
    return latitude, longitude, full_address

def netmap(cities_data, connections_data, title="Network Map", maximum_nodes=100, output_html_file="network_map.html", default_size=5):
    """
    cities_data (list):  {
        "node": "New York", "lat": 40.7128, "lon": -74.0060, "size": 15,
        "color": "red", "shape": "circle", "node_hover": "The Big Apple, USA"
    }, # shape: circle, triangle, square, star
    connections_data(list):  {
        "node1": "New York", "node2": "Paris", "color": "darkblue", "width": 2,
        "style": "dashed", "arrow": False, "curve": True,
        "edge_hover": any text e.g. "Transatlantic flight"
        "default_size": node size 5
    },
    maximum_nodes: maximum nodes to display initially
    """
    df_nodes = pd.DataFrame(cities_data)
    if not df_nodes['lat'].apply(lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)).all():
        raise ValueError("latitude contains non-numeric values.")
    if not df_nodes['lon'].apply(lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)).all():
        raise ValueError("longitude contains non-numeric values.")
    if not df_nodes['size'].apply(lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)).all():
        raise ValueError("node size contains non-numeric values.")

    df_edges = pd.DataFrame(connections_data)
    if not df_edges['width'].apply(lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)).all():
        raise ValueError("edge width contains non-numeric values.")

    # Define default values
    defaults_city = {
        "lat": lambda city: latLong(city["node"])[0],
        "lon": lambda city: latLong(city["node"])[1],
        "size": default_size,
        "color": "gray",
        "shape": "circle",
        "node_hover": lambda city: city["node"]
    }

    for city in cities_data:
        for key, default_value in defaults_city.items():
            if key not in city:
                city[key] = default_value(city) if callable(default_value) else default_value

    defaults_connection = {
        "color": "gray",
        "width": 1,
        "style": "solid",
        "arrow": False,
        "curve": False,
        "edge_hover": lambda connection: (connection['node1'] + ' to ' + connection['node2'])
    }

    for connection in connections_data:
        for key, default_value in defaults_connection.items():
            if key not in connection:
                connection[key] = default_value(connection) if callable(default_value) else default_value

    # Pre-filter based on maximum_nodes for initial load
    sorted_cities = sorted(cities_data, key=lambda x: x['size'], reverse=True)
    selected_cities = sorted_cities[:min(maximum_nodes, len(cities_data))]
    selected_city_nodes = {city['node'] for city in selected_cities}
    filtered_connections = [conn for conn in connections_data if conn['node1'] in selected_city_nodes and conn['node2'] in selected_city_nodes]

    cities_json = json.dumps(selected_cities, indent=2)
    connections_json = json.dumps(filtered_connections, indent=2)
    all_cities_json = json.dumps(cities_data, indent=2)
    all_connections_json = json.dumps(connections_data, indent=2)

    total_nodes = len(cities_data)
    total_edges = len(connections_data)
    effective_max_nodes = min(maximum_nodes, len(selected_cities))

    # Extract unique colors and hover texts from all cities_data
    unique_colors = sorted(set(city['color'] for city in cities_data))
    unique_hovers = sorted(set(city['node_hover'] for city in cities_data))

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>Network Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <style>
      html, body, #map {{
        height: 100%;
        margin: 0;
      }}
      .arrow-label {{
        background: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        box-shadow: 0 0 4px rgba(0,0,0,0.3);
        pointer-events: none;
        white-space: nowrap;
      }}
      .leaflet-control-title {{
        background: rgba(255, 255, 255, 0.8);
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 0 8px rgba(0,0,0,0.3);
        cursor: move;
        position: absolute;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1000;
        user-select: none;
      }}
      .slider-container {{
        position: absolute;
        bottom: 10px;
        left: 10px;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 8px rgba(0,0,0,0.3);
        display: none; /* Initially hidden */
      }}
      .slider-label {{
        font-size: 14px;
        margin-bottom: 5px;
      }}
      .dimmed {{
        opacity: 0.3;
      }}
      .dropdown-container {{
        margin-top: 10px;
      }}
      select, input {{
        width: 100%;
        padding: 5px;
        font-size: 14px;
        border-radius: 4px;
      }}
      .toggle-button {{
        position: absolute;
        top: 10px; /* Moved to top to avoid covering controls */
        right: 10px; /* Positioned to the right */
        z-index: 1001;
        background: rgba(255, 255, 255, 0.8);
        padding: 8px 12px;
        border-radius: 5px;
        font-size: 14px;
        cursor: pointer;
        box-shadow: 0 0 8px rgba(0,0,0,0.3);
        border: none;
      }}
      .toggle-button:hover {{
        background: rgba(255, 255, 255, 1);
      }}
    </style>
    </head>
    <body>
    <div id="map"></div>
    <div id="map-title" class="leaflet-control-title">{title}</div>
    <button id="toggle-controls" class="toggle-button">Show Controls</button>
    <div id="controls" class="slider-container">
      <div class="slider-label">Max Nodes: <span id="node-count">{effective_max_nodes}</span></div>
      <input type="range" id="node-slider" min="1" max="{total_nodes}" value="{effective_max_nodes}" step="1">
      <div class="slider-label">Edges: <span id="edge-count">0 / {total_edges}</span></div>
      <div class="dropdown-container">
        <div class="slider-label">Filter by Color:</div>
        <select id="color-filter" multiple>
          <option value="all">All Colors</option>
          {"".join(f'<option value="{color}">{color}</option>' for color in unique_colors)}
        </select>
      </div>
      <div class="dropdown-container">
        <div class="slider-label">Filter by Hover:</div>
        <select id="hover-filter" multiple>
          <option value="all">All Hovers</option>
          {"".join(f'<option value="{hover}">{hover}</option>' for hover in unique_hovers)}
        </select>
      </div>
      <div class="dropdown-container">
        <div class="slider-label">Lat Range (-90 to 90):</div>
        <input type="number" id="lat-min" min="-90" max="90" value="-90" step="0.1">
        <input type="number" id="lat-max" min="-90" max="90" value="90" step="0.1">
      </div>
      <div class="dropdown-container">
        <div class="slider-label">Lon Range (-180 to 180):</div>
        <input type="number" id="lon-min" min="-180" max="180" value="-180" step="0.1">
        <input type="number" id="lon-max" min="-180" max="180" value="180" step="0.1">
      </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <script src="https://rawcdn.githack.com/makinacorpus/Leaflet.TextPath/master/leaflet.textpath.js"></script>

    <script>
      const cities = {cities_json};
      const connections = {connections_json};
      const all_cities = {all_cities_json};
      const all_connections = {all_connections_json};
      const total_nodes = {total_nodes};
      const total_edges = {total_edges};
      let selectedNode = null;
      let selectedColor = ['all'];
      let selectedHover = ['all'];
      let latMin = -90;
      let latMax = 90;
      let lonMin = -180;
      let lonMax = 180;

      const map = L.map('map').setView([20, 0], 2);
      L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: '© CartoDB'
      }}).addTo(map);

      const titleDiv = document.getElementById('map-title');
      const draggable = new L.Draggable(titleDiv);
      draggable.enable();

      map.getContainer().style.position = 'relative';

      // Initialize marker cluster group and edges layer
      const markers = L.markerClusterGroup({{
        maxClusterRadius: 50,
        disableClusteringAtZoom: 10,
        spiderfyOnMaxZoom: true
      }});
      const edges = L.layerGroup();
      map.addLayer(markers);
      map.addLayer(edges);

      // Function to create a marker for a city
      function createMarker(city) {{
        let iconHtml = '';
        const size = city.size * 2;

        if (city.shape === "circle") {{
          iconHtml = `<div style="width:${{size}}px;height:${{size}}px;background:${{city.color}};border-radius:50%;opacity:0.8;"></div>`;
        }} else if (city.shape === "square") {{
          iconHtml = `<div style="width:${{size}}px;height:${{size}}px;background:${{city.color}};opacity:0.8;"></div>`;
        }} else if (city.shape === "star") {{
          iconHtml = `
            <svg width="${{size}}" height="${{size}}" viewBox="0 0 100 100">
              <polygon points="50,5 61,35 95,35 67,57 76,91 50,70 24,91 33,57 5,35 39,35"
                fill="${{city.color}}" opacity="0.8" />
            </svg>`;
        }}

        const icon = L.divIcon({{
          html: iconHtml,
          className: "",
          iconSize: [size, size]
        }});

        const marker = L.marker([city.lat, city.lon], {{
          icon: icon
        }});

        if (city.node_hover) {{
          marker.bindTooltip(city.node_hover, {{
            direction: 'top',
            permanent: false,
            opacity: 0.9
          }});
        }}

        marker.bindPopup(city.node);

        marker.on('click', () => {{
          selectedNode = city.node;
          debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
        }});

        return marker;
      }}

      function generateBezierPoints(p0, p1, p2, numPoints) {{
        const points = [p0];
        for (let t = 1 / (numPoints - 1); t < 1; t += 1 / (numPoints - 1)) {{
          const u = 1 - t;
          const tt = t * t;
          const uu = u * u;
          const lat = uu * p0[0] + 2 * u * t * p1[0] + tt * p2[0];
          const lon = uu * p0[1] + 2 * u * t * p1[1] + tt * p2[1];
          points.push([lat, lon]);
        }}
        points.push(p2);
        return points;
      }}

      // Debounce function to limit update frequency
      function debounce(func, wait) {{
        let timeout;
        return function executedFunction(...args) {{
          const later = () => {{
            clearTimeout(timeout);
            func(...args);
          }};
          clearTimeout(timeout);
          timeout = setTimeout(later, wait);
        }};
      }}

      function updateNodes(maxNodes) {{
        document.getElementById('node-count').textContent = maxNodes + ' / ' + total_nodes;
        let filteredCities = all_cities;

        // Apply color filter
        if (selectedColor[0] !== 'all' && selectedColor.length > 0) {{
          filteredCities = filteredCities.filter(city => selectedColor.includes(city.color));
        }}

        // Apply hover filter
        if (selectedHover[0] !== 'all' && selectedHover.length > 0) {{
          filteredCities = filteredCities.filter(city => selectedHover.includes(city.node_hover));
        }}

        // Apply lat/lon range filter
        filteredCities = filteredCities.filter(city =>
          city.lat >= latMin && city.lat <= latMax &&
          city.lon >= lonMin && city.lon <= lonMax
        );

        // Apply max nodes limit
        const sortedCities = filteredCities.sort((a, b) => b.size - a.size).slice(0, maxNodes);
        const selectedCitynodes = new Set(sortedCities.map(city => city.node));

        // Get visible bounds
        const bounds = map.getBounds();
        const visibleCities = sortedCities.filter(city =>
          bounds.contains([city.lat, city.lon])
        );
        const visibleCitynodes = new Set(visibleCities.map(city => city.node));

        // Clear existing markers, edges, and hover labels
        markers.clearLayers();
        edges.clearLayers();
        map.eachLayer(layer => {{
          if (layer instanceof L.Marker && layer.options.icon.options.className === 'arrow-label') {{
            map.removeLayer(layer);
          }}
        }});

        // Add markers for visible cities
        visibleCities.forEach(city => {{
          const marker = createMarker(city);
          if (selectedNode && city.node !== selectedNode && !all_connections.some(link =>
            (link.node1 === selectedNode && link.node2 === city.node) ||
            (link.node2 === selectedNode && link.node1 === city.node))) {{
            marker.setOpacity(0.3);
          }} else {{
            marker.setOpacity(1);
          }}
          markers.addLayer(marker);
        }});

        // Filter connections to include edges between visible nodes or connected to selectedNode
        const filteredConnections = all_connections.filter(link =>
          (visibleCitynodes.has(link.node1) && visibleCitynodes.has(link.node2)) ||
          (selectedNode && (link.node1 === selectedNode || link.node2 === selectedNode))
        );

        // Update node count to reflect visible nodes out of filtered total
        document.getElementById('node-count').textContent = visibleCities.length + ' / ' + sortedCities.length;

        // Update edge count display
        document.getElementById('edge-count').textContent = filteredConnections.length + ' / ' + total_edges;

        // Detect bidirectional edges
        const bidirectionalEdges = new Set();
        filteredConnections.forEach((link, index) => {{
          const reverseLink = filteredConnections.find((l, i) => i !== index && l.node1 === link.node2 && l.node2 === link.node1);
          if (reverseLink) {{
            bidirectionalEdges.add(`${{link.node1}}-${{link.node2}}`);
            bidirectionalEdges.add(`${{link.node2}}-${{link.node1}}`);
          }}
        }});

        filteredConnections.forEach(link => {{
          const fromCity = all_cities.find(c => c.node === link.node1);
          const toCity = all_cities.find(c => c.node === link.node2);
          // Skip if either node is missing
          if (!fromCity || !toCity) return;
          
          const from = [fromCity.lat, fromCity.lon];
          const to = [toCity.lat, toCity.lon];

          let latlngs = [from, to];
          const edgeKey = `${{link.node1}}-${{link.node2}}`;
          const isBidirectional = bidirectionalEdges.has(edgeKey);
          const shouldCurve = link.curve || isBidirectional;

          if (shouldCurve) {{
            const midLat = (from[0] + to[0]) / 2;
            const midLon = (from[1] + to[1]) / 2;
            const latDiff = to[0] - from[0];
            const lonDiff = to[1] - from[1];
            const length = Math.sqrt(latDiff * latDiff + lonDiff * lonDiff);
            const baseOffsetMagnitude = Math.min(length * 0.1, 5);
            const perpLat = -lonDiff / length * baseOffsetMagnitude;
            const perpLon = latDiff / length * baseOffsetMagnitude;

            let controlLat, controlLon;
            if (isBidirectional) {{
              const isReverse = link.node1 > link.node2;
              const bidirectionalOffset = baseOffsetMagnitude * 2;
              controlLat = midLat + (isReverse ? -perpLat * 2 : perpLat * 2) + (isReverse ? bidirectionalOffset : -bidirectionalOffset);
              controlLon = midLon + (isReverse ? -perpLon * 2 : perpLon * 2) + (isReverse ? bidirectionalOffset : -bidirectionalOffset);
            }} else {{
              controlLat = midLat + perpLat;
              controlLon = midLon + perpLon;
            }}

            latlngs = generateBezierPoints(from, [controlLat, controlLon], to, 50);
          }}

          const lineStyle = {{
            color: link.color,
            weight: link.width,
            dashArray:
              link.style === "dashed" ? "5, 10" :
              link.style === "dotted" ? "2, 6" : null,
            opacity: selectedNode && !(link.node1 === selectedNode || link.node2 === selectedNode) ? 0.3 : 1
          }};

          const polyline = L.polyline(latlngs, {{
            ...lineStyle
          }}).addTo(edges);

          if (link.arrow) {{
            const arrowSize = Math.max(10, link.width * 4);
            polyline.setText('▶', {{
              repeat: false,
              center: true,
              offset: 0,
              attributes: {{
                fill: link.color,
                "font-size": `${{arrowSize}}`,
                "font-weight": "bold",
                "dy": `${{arrowSize / 3}}`,
                opacity: selectedNode && !(link.node1 === selectedNode || link.node2 === selectedNode) ? 0.3 : 1
              }}
            }});
          }}

          const hoverLabel = L.marker([0, 0], {{
            icon: L.divIcon({{
              className: 'arrow-label',
              html: link.edge_hover || `${{link.node1}} → ${{link.node2}}`,
              iconSize: null
            }}),
            interactive: false
          }});

          const hoverLine = L.polyline(latlngs, {{
            color: '#0000',
            weight: Math.max(link.width + 10, 15),
            opacity: 0,
            interactive: true
          }}).addTo(edges);

          hoverLine.on("mouseover", (e) => {{
            hoverLabel.setLatLng(e.latlng);
            map.addLayer(hoverLabel);
          }});
          hoverLine.on("mouseout", () => {{
            if (map.hasLayer(hoverLabel)) {{
              map.removeLayer(hoverLabel);
            }}
          }});
          hoverLine.on("click", () => {{
            if (map.hasLayer(hoverLabel)) {{
              map.removeLayer(hoverLabel);
            }}
          }});
        }});
      }}

      // Debounced update function
      const debouncedUpdateNodes = debounce(updateNodes, 300);

      // Toggle controls visibility
      const toggleButton = document.getElementById('toggle-controls');
      const controlsDiv = document.getElementById('controls');
      toggleButton.addEventListener('click', () => {{
        if (controlsDiv.style.display === 'none') {{
          controlsDiv.style.display = 'block';
          toggleButton.textContent = 'Hide Controls';
        }} else {{
          controlsDiv.style.display = 'none';
          toggleButton.textContent = 'Show Controls';
        }}
      }});

      // Update selected values for multiple selections
      function updateSelectedValues(selectElement, selectedArray) {{
        const options = Array.from(selectElement.selectedOptions);
        selectedArray.length = 0; // Clear the array
        options.forEach(option => selectedArray.push(option.value));
        if (selectedArray.length === 0) selectedArray.push('all'); // Default to 'all' if nothing selected
      }}

      // Event listeners for multiple selections
      document.getElementById('color-filter').addEventListener('change', (e) => {{
        updateSelectedValues(e.target, selectedColor);
        debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
      }});

      document.getElementById('hover-filter').addEventListener('change', (e) => {{
        updateSelectedValues(e.target, selectedHover);
        debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
      }});

      document.getElementById('lat-min').addEventListener('input', (e) => {{
        latMin = parseFloat(e.target.value);
        debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
      }});

      document.getElementById('lat-max').addEventListener('input', (e) => {{
        latMax = parseFloat(e.target.value);
        debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
      }});

      document.getElementById('lon-min').addEventListener('input', (e) => {{
        lonMin = parseFloat(e.target.value);
        debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
      }});

      document.getElementById('lon-max').addEventListener('input', (e) => {{
        lonMax = parseFloat(e.target.value);
        debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
      }});

      document.getElementById('node-slider').addEventListener('input', (e) => {{
        debouncedUpdateNodes(parseInt(e.target.value));
      }});

      map.on('click', (e) => {{
        if (!e.originalEvent.target.closest('.leaflet-marker-icon')) {{
          selectedNode = null;
          debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
        }}
      }});

      map.on('moveend zoomend', () => {{
        debouncedUpdateNodes(parseInt(document.getElementById('node-slider').value));
      }});

      // Initial update
      debouncedUpdateNodes({effective_max_nodes});
    </script>
    </body>
    </html>
    """

    with open(output_html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {output_html_file} successfully!")
    import webbrowser
    webbrowser.open(output_html_file)

if __name__ == "__main__":
    cities = [
        {"node": "rovaniemi,finland"},
        {
            'node': 'eventti.net',
            'lat': 60.1497055,
            'lon': 24.7376876,
            'size': 10,
            'color': 'blue',
            'shape': 'circle',
            'node_hover': 'eventti.net'
        },
        {
            "node": "New York", "lat": 40.7128, "lon": -74.0060, "size": 15,
            "color": "red", "shape": "circle", "node_hover": "The Big Apple, USA"
        },
        {
            "node": "London", "lat": 51.5074, "lon": -0.1278, "size": 12,
            "color": "blue", "shape": "star", "node_hover": "Capital of the UK"
        },
        {
            "node": "Tokyo", "lat": 35.6762, "lon": 139.6503, "size": 10,
            "color": "green", "shape": "square", "node_hover": "Capital of Japan"
        },
        {
            "node": "Sydney", "lat": -33.8688, "lon": 151.2093, "size": 8,
            "color": "purple", "shape": "circle", "node_hover": "Australia’s coastal gem"
        },
        {
            "node": "Paris", "lat": 48.8566, "lon": 2.3522, "size": 11,
            "color": "orange", "shape": "star", "node_hover": "City of Love"
        },
    ]

    connections = [
          {
            "node1": "rovaniemi,finland", "node2": "eventti.net"
        },
        {
            "node1": "New York", "node2": "London", "color": "black", "width": 2,
            "style": "solid", "arrow": True, "curve": False,
            "edge_hover": "Flight from NY to London"
        },
        {
            "node1": "Tokyo", "node2": "London", "color": "black", "width": 2,
            "style": "solid", "arrow": True, "curve": False,
            "edge_hover": "Flight tokyo to London"
        },
        {
            "node1": "London", "node2": "Tokyo", "color": "blue", "width": 3,
            "style": "solid", "arrow": True, "curve": False,
            "edge_hover": "From London to Tokyo"
        },
        {
            "node1": "Tokyo", "node2": "rovaniemi,finland", "color": "red", "width": 10,
            "style": "dashed", "arrow": True, "curve": True,
            "edge_hover": "From Tokyo to Rovaniemi"
        },
        {
            "node1": "Tokyo", "node2": "Sydney", "color": "blue", "width": 1,
            "style": "solid", "arrow": True, "curve": False,
            "edge_hover": "Trade route Tokyo ↔ Sydney"
        },
        {
            "node1": "Sydney", "node2": "New York", "color": "green", "width": 12,
            "style": "solid", "arrow": True, "curve": True,
            "edge_hover": "Tourist route Sydney–NY"
        },
        {
            "node1": "London", "node2": "Paris", "color": "brown", "width": 4,
            "style": "solid", "arrow": True, "curve": False,
            "edge_hover": "Eurostar connection"
        },
        {
            "node1": "New York", "node2": "Paris", "color": "darkblue", "width": 2,
            "style": "dashed", "arrow": False, "curve": False,
            "edge_hover": "Transatlantic flight"
        },
    ]

    netmap(cities, connections, title="net map", output_html_file='simple.html', maximum_nodes=2)