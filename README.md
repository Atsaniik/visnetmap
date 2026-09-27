# visnetmap

[![PyPI version](https://img.shields.io/pypi/v/visnetmap.svg)](https://pypi.org/project/visnetmap/)
[![Python versions](https://img.shields.io/pypi/pyversions/visnetmap.svg)](https://pypi.org/project/visnetmap/)
[![License](https://img.shields.io/pypi/l/visnetmap.svg)](https://github.com/Atsaniik/visnetmap/blob/main/LICENSE)

`visnetmap` is a Python library for creating interactive network and map visualizations as standalone HTML files.

It provides two main visualization tools:

- `visnet()` — interactive network graph visualization using **vis-network**
![netWork example](https://raw.githubusercontent.com/Atsaniik/visnetmap/main/img/network.png)
- `netMap()` — interactive geographical network map using **Leaflet**
![netMap example](https://raw.githubusercontent.com/Atsaniik/visnetmap/main/img/netmap.png)

The package is designed for researchers, students, and analysts who want to quickly generate shareable HTML visualizations from Python data structures, NetworkX graphs, or location-based network data.

---

## Live demo

A presentation/demo page is available here:

[https://atsaniik.github.io/Finland_DMOs_Vienna/](https://atsaniik.github.io/Finland_DMOs_Vienna/)

This page demonstrates the type of interactive network and map visualizations that can be produced with `visnetmap`.

---

## Main features

- Generate standalone interactive HTML files
- Visualize NetworkX-like graphs
- Visualize geographical networks on maps
- Support node and edge hover information
- Support weighted edges
- Support directed graphs
- Support custom node size, color, shape, and labels
- Support map markers and curved/arced connections
- Export generated visualizations as HTML
- Optionally open output directly in a browser
- No JavaScript coding required for normal use

---

## Installation

Install from PyPI:

```bash
pip install visnetmap
```

If you want to use NetworkX examples:

```bash
pip install "visnetmap[networkx]"
```

If the package is not yet published on PyPI, install directly from GitHub:

```bash
pip install git+https://github.com/Atsaniik/visnetmap.git
```

For local development:

```bash
git clone https://github.com/Atsaniik/visnetmap.git
cd visnetmap
pip install -e ".[dev]"
```

---

## Quick start: network visualization

```python
import networkx as nx
from visnetmap import visnet

G = nx.DiGraph()

G.add_weighted_edges_from([
    ("B", "A", 5),
    ("C", "A", 2),
    ("D", "A", 1),
    ("B", "C", 2),
    ("E", "F", 4),
    ("E", "G", 3),
    ("E", "H", 2),
])

visnet(
    G,
    network_title="Knowledge Sharing Network",
    writeHTML="knowledge_network.html",
    browserView=True,
)
```

This creates an HTML file such as:

```text
netOutPut/knowledge_network.html
```

and opens it in your browser if `browserView=True`.

---

## Quick start: map visualization

```python
from visnetmap import netMap

cities = [
    {
        "node": "New York",
        "lat": 40.7128,
        "lon": -74.0060,
        "size": 15,
        "color": "red",
        "shape": "circle",
        "node_hover": "The Big Apple, USA",
    },
    {
        "node": "London",
        "lat": 51.5074,
        "lon": -0.1278,
        "size": 12,
        "color": "blue",
        "shape": "star",
        "node_hover": "Capital of the UK",
    },
    {
        "node": "Tokyo",
        "lat": 35.6762,
        "lon": 139.6503,
        "size": 10,
        "color": "green",
        "shape": "square",
        "node_hover": "Capital of Japan",
    },
]

connections = [
    {
        "node1": "New York",
        "node2": "London",
        "color": "black",
        "width": 2,
        "style": "solid",
        "arrow": True,
        "curve": False,
        "edge_hover": "Flight from New York to London",
    },
    {
        "node1": "London",
        "node2": "Tokyo",
        "color": "blue",
        "width": 3,
        "style": "solid",
        "arrow": True,
        "curve": True,
        "edge_hover": "Connection from London to Tokyo",
    },
]

netMap(
    cities,
    connections,
    title="Global City Network",
    writeHTML="city_network_map.html",
    browserView=True,
)
```

This creates an HTML file such as:

```text
mapOutPut/city_network_map.html
```

---

## Import options

The main functions can be imported directly:

```python
from visnetmap import visnet, netMap
```

Additional helper functions:

```python
from visnetmap import nx2vis, latLong, base64_from_url, base64_from_loc
```

---

## `visnet()` overview

`visnet()` creates an interactive network graph.

Basic usage:

```python
visnet(
    G=None,
    nodes=None,
    edges=None,
    network_title="Network",
    writeHTML="network.html",
    browserView=False,
    maximum_display=100,
)
```

### Input option 1: NetworkX graph

```python
import networkx as nx
from visnetmap import visnet

G = nx.DiGraph()
G.add_weighted_edges_from([
    ("A", "B", 3),
    ("B", "C", 2),
    ("C", "A", 1),
])

visnet(G, network_title="Directed Network", browserView=True)
```

### Input option 2: node and edge dictionaries

```python
from visnetmap import visnet

nodes = [
    {
        "id": 1,
        "label": "Start",
        "size": 20,
        "color": "red",
        "shape": "dot",
        "title": "Starting node",
    },
    {
        "id": 2,
        "label": "Process",
        "size": 30,
        "color": "blue",
        "shape": "box",
        "title": "Processing node",
    },
]

edges = [
    {
        "from": 1,
        "to": 2,
        "width": 3,
        "color": {"color": "gray"},
        "arrows": "to",
        "title": "Connection from Start to Process",
    },
]

visnet(
    nodes=nodes,
    edges=edges,
    network_title="Simple Network",
    browserView=True,
)
```

---

## Node format for `visnet()`

Each node is a dictionary.

Required key:

| Key | Description |
|---|---|
| `id` | Unique node identifier |

Common optional keys:

| Key | Description |
|---|---|
| `label` | Text label shown near the node |
| `size` | Node size |
| `color` | Node color, for example `"red"` or `{"background": "red", "border": "black"}` |
| `shape` | Node shape, for example `"dot"`, `"box"`, `"triangle"`, `"star"`, `"image"`, `"icon"` |
| `title` | Hover tooltip |
| `image` | Image URL or Base64 image string for image nodes |
| `icon` | Font Awesome icon settings |
| `pos` | Optional position such as `(x, y)` |

Example:

```python
{
    "id": "A",
    "label": "Node A",
    "size": 25,
    "color": "orange",
    "shape": "dot",
    "title": "This is Node A",
}
```

---

## Edge format for `visnet()`

Each edge is a dictionary.

Required keys:

| Key | Description |
|---|---|
| `from` | Source node ID |
| `to` | Target node ID |

Common optional keys:

| Key | Description |
|---|---|
| `width` | Edge width |
| `weight` | Alternative edge weight, especially from NetworkX |
| `color` | Edge color, for example `{"color": "gray"}` |
| `arrows` | Arrow direction, for example `"to"` |
| `label` | Edge label |
| `title` | Hover tooltip |
| `dashes` | Dashed edge style |
| `smooth` | vis-network smooth edge settings |

Example:

```python
{
    "from": "A",
    "to": "B",
    "width": 4,
    "color": {"color": "black"},
    "arrows": "to",
    "title": "A shares knowledge with B",
}
```

---

## `netMap()` overview

`netMap()` creates an interactive geographical network map.

Basic usage:

```python
netMap(
    cities_data,
    connections_data,
    title="Network Map",
    maximum_nodes=100,
    writeHTML="network_map.html",
    browserView=False,
)
```

---

## City/node format for `netMap()`

Each city or map node is a dictionary.

Required key:

| Key | Description |
|---|---|
| `node` | Node name or identifier |

Recommended optional keys:

| Key | Description |
|---|---|
| `lat` | Latitude |
| `lon` | Longitude |
| `size` | Marker size |
| `color` | Marker color |
| `shape` | Marker shape: `"circle"`, `"square"`, `"triangle"`, or `"star"` |
| `node_hover` | Tooltip text shown when hovering over the node |

Example:

```python
{
    "node": "Helsinki",
    "lat": 60.1699,
    "lon": 24.9384,
    "size": 12,
    "color": "blue",
    "shape": "circle",
    "node_hover": "Helsinki, Finland",
}
```

If latitude and longitude are missing, `netMap()` may attempt to geocode the location name using `geopy` and Nominatim, depending on the installed version and function settings.

---

## Connection format for `netMap()`

Each connection is a dictionary.

Required keys:

| Key | Description |
|---|---|
| `node1` | Source node name |
| `node2` | Target node name |

Common optional keys:

| Key | Description |
|---|---|
| `color` | Line color |
| `width` | Line width |
| `style` | `"solid"`, `"dashed"`, or `"dotted"` |
| `arrow` | `True` or `False` |
| `curve` | `True` or `False` |
| `edge_hover` | Tooltip text shown when hovering over the edge |

Example:

```python
{
    "node1": "Helsinki",
    "node2": "Joensuu",
    "color": "darkblue",
    "width": 3,
    "style": "solid",
    "arrow": True,
    "curve": True,
    "edge_hover": "Connection from Helsinki to Joensuu",
}
```

---

## Example: Finnish destination network map

```python
from visnetmap import netMap

cities = [
    {
        "node": "Helsinki",
        "lat": 60.1699,
        "lon": 24.9384,
        "size": 15,
        "color": "blue",
        "shape": "circle",
        "node_hover": "Helsinki",
    },
    {
        "node": "Joensuu",
        "lat": 62.6010,
        "lon": 29.7636,
        "size": 10,
        "color": "green",
        "shape": "star",
        "node_hover": "Joensuu",
    },
    {
        "node": "Kuopio",
        "lat": 62.8924,
        "lon": 27.6770,
        "size": 10,
        "color": "orange",
        "shape": "square",
        "node_hover": "Kuopio",
    },
]

connections = [
    {
        "node1": "Helsinki",
        "node2": "Joensuu",
        "color": "blue",
        "width": 3,
        "arrow": True,
        "curve": True,
        "edge_hover": "Helsinki to Joensuu",
    },
    {
        "node1": "Helsinki",
        "node2": "Kuopio",
        "color": "orange",
        "width": 2,
        "arrow": True,
        "curve": True,
        "edge_hover": "Helsinki to Kuopio",
    },
]

netMap(
    cities,
    connections,
    title="Finnish Destination Network",
    writeHTML="finland_destination_network.html",
    browserView=True,
)
```

---

## Output files

By default, `visnet()` writes network HTML files to:

```text
netOutPut/
```

and `netMap()` writes map HTML files to:

```text
mapOutPut/
```

Example:

```python
visnet(G, writeHTML="my_network.html")
```

creates:

```text
netOutPut/my_network.html
```

Example:

```python
netMap(cities, connections, writeHTML="my_map.html")
```

creates:

```text
mapOutPut/my_map.html
```

---

## Tile provider note for maps

`netMap()` uses web map tiles through Leaflet. Depending on your configuration, map tiles may come from providers such as CARTO, OpenStreetMap, Esri, or other services.

For public or high-traffic use, avoid relying directly on OpenStreetMap volunteer tile servers. Use a proper tile provider or your own tile server if needed.

Example with CARTO tiles:

```python
netMap(
    cities,
    connections,
    title="Map with CARTO tiles",
    tile_url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    tile_attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    browserView=True,
)
```

---

## Geocoding note

If you use `latLong()` or provide map nodes without latitude and longitude, geocoding may be performed through Nominatim using `geopy`.

Please respect Nominatim usage policies and avoid sending large volumes of requests.

For larger datasets, it is recommended to prepare latitude and longitude values in advance.

Example:

```python
from visnetmap import latLong

lat, lon, address = latLong("Joensuu, Finland")

print(lat, lon, address)
```

---

## Helper: convert images to Base64

For image nodes in `visnet()`, local images can be converted to Base64 strings.

```python
from visnetmap import base64_from_loc, visnet

image_data = base64_from_loc("logo.png")

nodes = [
    {
        "id": "logo",
        "label": "Logo node",
        "shape": "image",
        "image": image_data,
        "size": 30,
    }
]

visnet(nodes=nodes, edges=[], network_title="Image Node Demo", browserView=True)
```

---

## Common problems

### NetworkX edge weight error

If an edge weight is written as a string:

```python
("B", "C", "2")
```

change it to a number:

```python
("B", "C", 2)
```

Edge widths and weights should be numeric.

---

### Map tiles show `403 Access blocked`

This usually means the selected map tile provider blocked the request.

Possible solutions:

- use a different tile provider,
- avoid heavy automated tile loading,
- use a valid tile service for public applications,
- use CARTO or another provider instead of direct OpenStreetMap volunteer tiles.

---

### Generated HTML does not show correctly offline

The generated HTML may load JavaScript and CSS from external CDNs, such as:

- vis-network
- Leaflet
- Leaflet.markercluster
- map tile providers

An internet connection may be required when opening the HTML file.

---

## Development

Clone the repository:

```bash
git clone https://github.com/Atsaniik/visnetmap.git
cd visnetmap
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install in editable mode:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Build the package:

```bash
python -m build
```

Check the distribution:

```bash
twine check dist/*
```

---



## Citation

If you use `visnetmap` in academic work, teaching, presentations, or research demos, please cite or acknowledge the package and the related project page:

```text
visnetmap: Interactive network and map visualization tools in Python.
Available at: https://github.com/Atsaniik/visnetmap
Demo: https://atsaniik.github.io/Finland_DMOs_Vienna/
```

---

## License

This project is released under the MIT License.

See the `LICENSE` file for details.

---

## Author

Developed by Atsaniik.

GitHub: [https://github.com/Atsaniik](https://github.com/Atsaniik)

Demo page: [https://atsaniik.github.io/Finland_DMOs_Vienna/](https://atsaniik.github.io/Finland_DMOs_Vienna/)
