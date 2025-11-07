import requests
import base64
import json, os
from IPython.display import HTML, display
import pandas as pd
import webbrowser
import random

def base64_from_url(image_url):
    """
    Downloads an image from a URL and returns its Base64 encoded string.

    Args:
        image_url (str): The URL of the image.

    Returns:
        str: The Base64 encoded string of the image, prefixed with data URI,
             or None if an error occurs.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        content_type = response.headers['Content-Type']
        if not content_type.startswith('image/'):
            print(f"Warning: URL does not point to an image. Content-Type: {content_type}")
            return None

        image_bytes = response.content
        encoded_string = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{content_type};base64,{encoded_string}"

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def base64_from_loc(image_local):
    """ turn local image to base64 for vis.js diagram for an image node 

    Args:
        image_local (_type_): local image address 
    """
    try:
        with open(image_local, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            base64_image_local = f"data:image/png;base64,{encoded_string}"
            return base64_image_local
    except FileNotFoundError:
        print("Error: Image file not found. Using placeholder image.")
        return None      

def visnet(nodes, edges, network_title='Atsaniik', description_df=None, description_title="Introduce your network", writeHTML="network_visualization.html", browserView=False, min_default_node_size=0, min_default_edge_width=0, maximum_display=100):
    """ visualize your network with a save button to export selected nodes and edges to JSON files
    Args:
        nodes(list): list of nodes dict e.g. {"id": 1, "label": "Start", "size": 30, "color": "red-spain", "shape": "dot-america", "title": "starting the point"}
        edges(list): list of edges dict e.g. {"from": 1, "to": 3, "width": 4, "color": {"color": "#C70039-europe"}, "arrows": "to", "title": "from 1 to 3"}
        description_df(dataframe): a dataframe with columns "Name", "Description"
        description_title(str): describe your network in short
        writeHTML(str): output HTML file name
        browserView(bool): whether to open the HTML in a browser
        min_default_node_size(float): minimum node size for initial display
        min_default_edge_width(float): minimum edge width for initial display
        maximum_display(int): maximum number of nodes to display at any time
    """
    defaults_node = {"label": lambda node: str(node['id']), "size": 1, "color": "gray", "shape": "dot", "title": lambda node: str(node['id'])}

    nodeIDchecks = []
    for node in nodes:
        nodeIDcheck = node['id']
        nodeIDchecks.append(nodeIDcheck)
        for key, default_value in defaults_node.items():
            if key not in node:
                # If the key is lon or node_hover, use the lambda to compute the value
                node[key] = default_value(node) if callable(default_value) else default_value
    #print(nodes)


    defaults_edge = {"width": 1, "color": {"color": "gray"}, "title": lambda edge: str(edge['from'])+ ' - ' + str(edge['to'] )}
    edgeIDchecks = []
    for edge in edges:
        edgeIDcheck = [edge['from'], edge['to']]
        missingNodes = [x for x in edgeIDcheck if x not in nodeIDchecks]
        if len(missingNodes)>0:
            print(f'edge {edge['from']}-{edge['to']} missing nodes description:  {missingNodes}')
        edgeIDchecks.extend(edgeIDcheck)
        for key, default_value in defaults_edge.items():
            if key not in edge:
                # If the key is lon or node_hover, use the lambda to compute the value
                edge[key] = default_value(edge) if callable(default_value) else default_value
    #print(edges)
  
  
    
    def extract_base_value(full_value, is_shape=False):
        if "-" in full_value:
            return full_value.split("-")[0]
        return full_value

    node_colors = [
        node["color"]["background"] if isinstance(node["color"], dict) else node["color"]
        for node in nodes if "color" in node
]


    edge_colors = [edge["color"]["color"] for edge in edges if "color" in edge and "color" in edge["color"]]

    color_bases = {}
    for color in node_colors + edge_colors:
        base = extract_base_value(color)
        if base in color_bases:
            color_bases[base].add(str(color))
        else:
            color_bases[base] = {str(color)}
            
            
    for base, variants in color_bases.items():
        if len(variants) > 1:
            print(f"Error: Multiple extra labels detected for base color '{base}': {', '.join(variants)}. Execution stopped.")
            return

    shape_bases = {}
    icon_shapes = {}
    image_shapes = {}
    for node in nodes:
            if "shape" in node:
                full_shape = node["shape"]
                base = extract_base_value(full_shape, is_shape=True)
                if base in shape_bases:
                    shape_bases[base].add(full_shape)
                else:
                    shape_bases[base] = {full_shape}
                # Track icon and image consistency
                if base == "icon" and "icon" in node and "code" in node["icon"]:
                    shape_label = full_shape.split("-")[1] if "-" in full_shape else full_shape
                    if node["icon"]["code"] in icon_shapes:
                        if shape_label not in icon_shapes[node["icon"]["code"]]:
                            icon_shapes[node["icon"]["code"]].add(shape_label)
                        else:
                            continue
                    else:
                        icon_shapes[node["icon"]["code"]] = {shape_label}
                elif base == "image" and "image" in node:
                    shape_label = full_shape.split("-")[1] if "-" in full_shape else full_shape
                    image_value = str(node["image"])
                    if image_value in image_shapes:
                        if shape_label not in image_shapes[image_value]:
                            image_shapes[image_value].add(shape_label)
                        else:
                            continue
                    else:
                        image_shapes[image_value] = {shape_label}

    for code, shapes in icon_shapes.items():
        if len(shapes) > 1:
            print(f"Error: Inconsistent icon code '{code}' used with different shape names: {', '.join(shapes)}. Execution stopped.")
            return

    for image_value, shapes in image_shapes.items():
        if len(shapes) > 1:
            print(f"Error: Inconsistent image name '{image_value}' used with different shape names: {', '.join(shapes)}. Execution stopped.")
            return

    for base, variants in shape_bases.items():
        if len(variants) > 1 and base not in ["icon", "image"]:
            print(f"Error: Multiple extra labels detected for base shape '{base}': {', '.join(variants)}. Execution stopped.")
            return

    if description_df is None:
        df = pd.DataFrame({
            "Name": ["Nodes amount", "Edges amount"],
            "Description": [len(nodes), len(edges)]
        })
    else:
        df = description_df

    table_rows = "".join([f'<tr><td>{row["Name"]}</td><td>{row["Description"]}</td></tr>' for _, row in df.iterrows()])

    all_nodes = sorted(nodes, key=lambda x: x["size"], reverse=True)
    unique_sizes = len(set(node["size"] for node in all_nodes))
    if unique_sizes == 1:
        random.shuffle(all_nodes)
    initial_nodes = all_nodes[:maximum_display]
    initial_node_ids = set(node["id"] for node in initial_nodes)

    initial_edges = [
        edge for edge in edges
        if edge["from"] in initial_node_ids and edge["to"] in initial_node_ids and 
        (min_default_edge_width is None or edge["width"] >= min_default_edge_width)
    ]

    min_size = round(min(node["size"] for node in all_nodes), 2) if all_nodes else 0.00
    max_size = round(max(node["size"] for node in all_nodes), 2) if all_nodes else 0.00
    min_width = round(min(edge["width"] for edge in edges), 2) if edges else 0.00
    max_width = round(max(edge["width"] for edge in edges), 2) if edges else 0.00

    def extract_base_value(full_value, is_shape=False):
        if isinstance(full_value, dict):
            full_value = full_value.get('background', '') if is_shape else full_value.get('color', '') if not is_shape else ''
        if "-" in full_value:
            return full_value.split("-")[0]
        return full_value
    
    
    

    colors = sorted(set(
        node["color"]["background"] if isinstance(node["color"], dict) else node["color"]
        for node in all_nodes
))
    shapes = sorted(set(node["shape"] for node in nodes))
    labels = sorted(set(node["label"] for node in all_nodes))
    titles = sorted(set(node.get("title", "") for node in all_nodes if "title" in node))
    edge_colors = sorted(set(edge["color"]["color"] for edge in edges))

    for node in all_nodes:
        full_shape = node["shape"]
        base_shape = extract_base_value(full_shape, is_shape=True)
        node["shape_label"] = full_shape
        node["shape"] = base_shape
        if isinstance(node["color"], dict):
            color_base = extract_base_value(node["color"].get('background', ''))
        else:
            color_base = extract_base_value(node["color"])
        node["color"] = {"background": color_base, "border": node["color"].get('border', 'gray') if isinstance(node["color"], dict) else 'gray'}
        
        
    for edge in edges:
        edge["color"]["color"] = extract_base_value(edge["color"]["color"])

    color_options = "\n".join([f'            <option value="{color}">{color}</option>' for color in colors])
    shape_options = "\n".join([f'            <option value="{shape}">{shape}</option>' for shape in shapes])
    title_options = "\n".join([f'            <option value="{title}">{title}</option>' for title in titles if title])
    edge_color_options = "\n".join([f'            <option value="{color}">{color}</option>' for color in edge_colors])
    max_display_options = "\n".join([f'            <option value="{val}"{" selected" if val == maximum_display else ""}>{val}</option>' for val in [1,5,10,20,30,50,60,70,80,90,100,108,150,200,300,400,500,1000,2000,5000,10000,20000]])

    nodes_json = json.dumps(initial_nodes, ensure_ascii=False)
    all_nodes_json = json.dumps(all_nodes, ensure_ascii=False)
    all_edges_json = json.dumps(edges, ensure_ascii=False)
    edges_json = json.dumps(initial_edges, ensure_ascii=False)

    drag_script = """
    <script type="text/javascript">
        var isDragging = false;
        var currentX;
        var currentY;
        var initialX;
        var initialY;
        var titleElement = document.getElementById('diagram-title');

        function startDragging(e) {
            initialX = e.clientX - currentX;
            initialY = e.clientY - currentY;
            isDragging = true;
            titleElement.style.cursor = 'grabbing';
        }

        function stopDragging() {
            isDragging = false;
            titleElement.style.cursor = 'move';
        }

        function dragTitle(e) {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
                titleElement.style.left = currentX + 'px';
                titleElement.style.top = currentY + 'px';
            }
        }

        if (titleElement) {
            currentX = parseInt(window.getComputedStyle(titleElement).left) || 50;
            currentY = parseInt(window.getComputedStyle(titleElement).top) || 10;
            titleElement.addEventListener('mousedown', startDragging);
            document.addEventListener('mousemove', dragTitle);
            document.addEventListener('mouseup', stopDragging);
            titleElement.style.userSelect = 'none';
        }
    </script>
    """

    script_code = """
    <script type="text/javascript">
    var allNodes = {all_nodes_json};
    var allEdges = {all_edges_json};
    var originalNodes = {nodes_json};
    var originalEdges = {edges_json};
    var nodes = new vis.DataSet(originalNodes);
    var edges = new vis.DataSet(originalEdges);
    var lastZoomCenter = {{ x: 0, y: 0 }};
    var lastScale = 1;
    var uniqueLabels = [...new Set(allNodes.map(node => node.label).filter(label => label))].sort();
    var previousNodes = originalNodes;
    var previousEdges = originalEdges;

    var container = document.getElementById('mynetwork');
    if (!container) {{
        console.error("Container #mynetwork not found!");
    }}
    var loadingBar = document.getElementById('loading-bar');
    var loadingProgress = document.getElementById('loading-progress');
    var loadingPercentage = document.getElementById('loading-percentage');

    var data = {{
        nodes: nodes,
        edges: edges
    }};
    var options = {{
        nodes: {{
            shape: 'dot',
            size: 20,
            font: {{ size: 14, color: '#333333' }},
            borderWidth: 2,
            color: {{
                background: '#97C2E6',
                border: '#2B7CE9',
                highlight: {{ background: '#D2E5FF', border: '#2B7CE9' }},
                hover: {{ background: '#D2E5FF', border: '#2B7CE9' }}
            }}
        }},
        edges: {{
            width: 1,
            color: {{ color: '#848484', highlight: '#848484', hover: '#848484', inherit: 'from', opacity: 0.8 }},
            smooth: {{ enabled: true, type: "dynamic" }},
            font: {{ size: 12 }}
        }},
        physics: {{
            enabled: true,
            stabilization: {{
                enabled: true,
                iterations: 1000,
                updateInterval: 50
            }},
            barnesHut: {{
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 95,
                springConstant: 0.04,
                damping: 0.09,
                avoidOverlap: 0
            }},
            solver: 'barnesHut'
        }},
        configure: {{
            enabled: true,
            filter: 'physics',
            showButton: true,
            container: document.getElementById('physics-config')
        }}
    }};

    container.style.opacity = '0';

    var network = new vis.Network(container, data, options);
    if (!network) {{
        console.error("Failed to initialize vis.Network!");
    }}

    network.on("stabilizationProgress", function(params) {{
        var progress = (params.iterations / params.total) * 100;
        if (loadingProgress && loadingPercentage) {{
            loadingProgress.style.width = progress + '%';
            loadingPercentage.textContent = Math.round(progress) + '%';
        }}
    }});

    network.on("stabilizationIterationsDone", function() {{
        if (loadingBar) {{
            loadingBar.style.display = 'none';
        }}
        container.style.opacity = '1';
        network.setOptions({{ physics: false }});
        updateNodes();
    }});

    function getSelectedOptions(selectElement) {{
        return Array.from(selectElement.selectedOptions).map(option => option.value);
    }}

    function updateSuggestions() {{
        var input = document.getElementById('label-search').value;
        var suggestionsDiv = document.getElementById('label-suggestions');
        suggestionsDiv.innerHTML = '';
        suggestionsDiv.style.display = 'none';

        if (input.trim() !== '') {{
            var terms = input.split(',').map(term => term.trim().toLowerCase());
            var lastTerm = terms[terms.length - 1];
            if (lastTerm) {{
                var matches = uniqueLabels.filter(label => 
                    label.toLowerCase().includes(lastTerm)
                );
                if (matches.length > 0) {{
                    suggestionsDiv.style.display = 'block';
                    matches.forEach(label => {{
                        var div = document.createElement('div');
                        div.className = 'suggestion-item';
                        div.textContent = label;
                        div.onclick = function() {{
                            var currentTerms = input.split(',').slice(0, -1);
                            currentTerms.push(label);
                            document.getElementById('label-search').value = currentTerms.join(',') + (currentTerms.length > 0 ? ',' : '');
                            suggestionsDiv.innerHTML = '';
                            suggestionsDiv.style.display = 'none';
                            updateNodes();
                        }};
                        suggestionsDiv.appendChild(div);
                    }});
                }}
            }}
        }} else {{
            updateNodes();
        }}
    }}

    function saveSelection() {{
        var currentNodes = nodes.get();
        var currentEdges = edges.get();

        // Create JSON strings
        var nodesJson = JSON.stringify(currentNodes, null, 2);
        var edgesJson = JSON.stringify(currentEdges, null, 2);

        // Create Blob objects for download
        var nodesBlob = new Blob([nodesJson], {{ type: 'application/json' }});
        var edgesBlob = new Blob([edgesJson], {{ type: 'application/json' }});

        // Create temporary URLs for the Blobs
        var nodesUrl = URL.createObjectURL(nodesBlob);
        var edgesUrl = URL.createObjectURL(edgesBlob);

        // Create download links
        var nodesLink = document.createElement('a');
        nodesLink.href = nodesUrl;
        nodesLink.download = 'nodes.json';
        document.body.appendChild(nodesLink);
        nodesLink.click();
        document.body.removeChild(nodesLink);

        var edgesLink = document.createElement('a');
        edgesLink.href = edgesUrl;
        edgesLink.download = 'edges.json';
        document.body.appendChild(edgesLink);
        edgesLink.click();
        document.body.removeChild(edgesLink);

        // Clean up URLs
        URL.revokeObjectURL(nodesUrl);
        URL.revokeObjectURL(edgesUrl);

        // Log saved locations (simulating file paths for console output)
        console.log("Nodes saved to: nodes.json");
        console.log("Edges saved to: edges.json");
    }}

    function updateNodes(zoomCenter = null, zoomDirection = null) {{
        console.log("Updating nodes...");
        var maxDisplay = parseInt(document.getElementById('max-display-select').value) || {maximum_display};
        var colorSelect = getSelectedOptions(document.getElementById('color-select'));
        var shapeSelect = getSelectedOptions(document.getElementById('shape-select'));
        var sizeMin = parseFloat(document.getElementById('size-min').value) || 0;
        var sizeMax = parseFloat(document.getElementById('size-max').value) || Infinity;
        var labelSearch = document.getElementById('label-search').value;
        var titleSelect = getSelectedOptions(document.getElementById('title-select'));
        var widthMin = document.getElementById('width-min').value ? parseFloat(document.getElementById('width-min').value) : null;
        var widthMax = document.getElementById('width-max').value ? parseFloat(document.getElementById('width-max').value) : null;
        var edgeColorSelect = getSelectedOptions(document.getElementById('edge-color-select'));

        var filteredNodes = allNodes;
        var filteredEdges = allEdges;

        if (labelSearch.trim() !== '') {{
            previousNodes = nodes.get();
            previousEdges = edges.get();
            console.log("Saving previous state: ", previousNodes.length, "nodes,", previousEdges.length, "edges");

            var searchTerms = labelSearch.split(',').map(term => term.trim().toLowerCase()).filter(term => term !== '');
            console.log("Search terms:", searchTerms);
            var selectedNodes = allNodes.filter(function(node) {{
                return node.label && searchTerms.some(term => node.label.toLowerCase() === term);
            }});
            console.log("Selected nodes:", selectedNodes.map(node => node.label));
            var neighborIds = new Set();
            selectedNodes.forEach(function(node) {{
                neighborIds.add(node.id);
                allEdges.forEach(function(edge) {{
                    if (edge.from === node.id) {{
                        neighborIds.add(edge.to);
                    }}
                    if (edge.to === node.id) {{
                        neighborIds.add(edge.from);
                    }}
                }});
            }});
            console.log("Neighbor IDs:", Array.from(neighborIds));
            filteredNodes = allNodes.filter(function(node) {{
                return neighborIds.has(node.id);
            }});
            console.log("Filtered nodes:", filteredNodes.map(node => node.label));
        }} 

        var validNodeIds = new Set();
        if (widthMin !== null || widthMax !== null) {{
            filteredEdges = allEdges.filter(function(edge) {{
                var widthMatch = true;
                if (widthMin !== null) {{
                    widthMatch = widthMatch && edge.width >= widthMin;
                }}
                if (widthMax !== null) {{
                    widthMatch = widthMatch && edge.width <= widthMax;
                }}
                return widthMatch;
            }});
            if (widthMin !== null && widthMin > 0) {{
                filteredEdges.forEach(function(edge) {{
                    validNodeIds.add(edge.from);
                    validNodeIds.add(edge.to);
                }});
                filteredNodes = filteredNodes.filter(function(node) {{
                    return validNodeIds.has(node.id) || filteredEdges.some(edge => edge.from === node.id || edge.to === node.id);
                }});
            }}
        }}

        filteredNodes = filteredNodes.filter(function(node) {{
            var fullColor = typeof node.color === 'string' ? node.color : node.color.background;
            var fullShape = node.shape_label || node.shape;
            var colorMatch = colorSelect.includes('all') || colorSelect.some(cs => fullColor === cs || fullColor.startsWith(cs.split('-')[0]));
            var shapeMatch = shapeSelect.includes('all') || (shapeSelect.length === 1 && shapeSelect[0] !== 'all' && fullShape === shapeSelect[0]);
            var sizeMatch = node.size >= sizeMin && node.size <= sizeMax;
            var titleMatch = titleSelect.includes('all') || (node.title && titleSelect.includes(node.title));
            return colorMatch && shapeMatch && sizeMatch && titleMatch;
        }});

        filteredNodes.sort((a, b) => b.size - a.size);

        filteredNodes = filteredNodes.slice(0, maxDisplay);

        filteredEdges = allEdges.filter(function(edge) {{
            var fullEdgeColor = edge.color.color;
            var colorMatch = edgeColorSelect.includes('all') || edgeColorSelect.some(function(ecs) {{
                return fullEdgeColor === ecs || fullEdgeColor.startsWith(ecs.split('-')[0]);
            }});

            var widthMatch = true;
            if (widthMin !== null) {{
                widthMatch = widthMatch && edge.width >= widthMin;
            }}
            if (widthMax !== null) {{
                widthMatch = widthMatch && edge.width <= widthMax;
            }}

            var nodeMatch = filteredNodes.some(function(n) {{
                return n.id === edge.from;
            }}) && filteredNodes.some(function(n) {{
                return n.id === edge.to;
            }});
            return colorMatch && widthMatch && nodeMatch;
        }});

        document.getElementById('node-count').textContent = filteredNodes.length;
        document.getElementById('edge-count').textContent = filteredEdges.length;

        nodes.clear();
        nodes.add(filteredNodes);
        edges.clear();
        edges.add(filteredEdges);
    }}

    function togglePanel(panelId) {{
        console.log("Toggling panel: " + panelId);
        var panel = document.getElementById(panelId);
        if (panel) {{
            panel.classList.toggle('panel-hidden');
        }} else {{
            console.error("Panel " + panelId + " not found!");
        }}
    }}

    network.on("zoom", function(params) {{
        var scale = params.scale;
        if (scale > lastScale) {{
            var pointerDOM = params.pointer.DOM;
            var pointerCanvas = network.DOMtoCanvas(pointerDOM);
            lastZoomCenter = pointerCanvas;
            updateNodes(lastZoomCenter, 'in');
        }} else if (scale < lastScale) {{
            updateNodes(null, 'out');
        }}
        lastScale = scale;
    }});

    // Add Enter key handler for label-search input
    document.getElementById('label-search').addEventListener('keydown', function(event) {{
        if (event.key === 'Enter') {{
            document.getElementById('label-suggestions').style.display = 'none';
            updateNodes();
        }}
    }});

    updateNodes();
    </script>
    """.format(
        all_nodes_json=all_nodes_json,
        all_edges_json=all_edges_json,
        nodes_json=nodes_json,
        edges_json=edges_json,
        maximum_display=maximum_display
    )

    html_code = f"""
    <html>
    <head>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" integrity="sha512-SnH5WK+bZxgPHs44uWIX+LLJAJ9/2PkPKZ5QiAj6Ta86w+fsb2TkcmfRyVX3pBnMFcV7oQPJkl9QevSCWr3W6A==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <style type="text/css">
        body {{
            font-family: 'Inter', sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background-color: #e0e0e0;
            position: relative;
        }}
        #mynetwork {{
            width: 100vw;
            height: 100vh;
            border: 1px solid lightgray;
            background-color: #f9f9f9;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: opacity 0.5s ease;
        }}
        #diagram-title {{
            position: absolute;
            top: 10px;
            left: 50px;
            z-index: 100;
            background-color: rgba(255, 255, 255, 0.8);
            padding: 10px 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 24px;
            color: #333;
            cursor: move;
            user-select: none;
        }}
        #loading-bar {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 300px;
            height: 30px;
            background-color: #ddd;
            border-radius: 15px;
            overflow: hidden;
            z-index: 150;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        #loading-progress {{
            width: 0%;
            height: 100%;
            background-color: #4CAF50;
            transition: width 0.3s ease;
        }}
        #loading-percentage {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 16px;
            font-weight: bold;
            color: #333;
            z-index: 151;
        }}
        #config-container {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            z-index: 100;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: calc(100vh - 40px);
            max-width: 20vw;
            overflow-y: auto;
            padding: 10px;
        }}
        #description-container {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            z-index: 100;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: calc(100vh - 40px);
            max-width: 20vw;
            overflow-y: auto;
            padding: 10px;
        }}
        #save-button-container {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 100;
            display: flex;
            justify-content: center;
        }}
        #save-selection {{
            background-color: white;
            color: #333333;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: background-color 0.3s ease;
        }}
        #save-selection:hover {{
            background-color: #45a049;
        }}
        #node-config, #physics-config, #description-table {{
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            max-width: 100%;
            overflow-x: auto;
        }}
        #node-config .filter-group, #description-table .table-group {{
            margin-bottom: 20px;
        }}
        #node-config .filter-group label, #description-table .table-group label {{
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
            
        }}
        .label-search {{ 
            color: #0066cc; /* Added color for Node Label Search label */
            display: block;              /* ensures it takes full width */
            text-align: center;          /* centers the text */
            font-size: 1.2em;            /* makes the label larger */
            font-weight: bold;           /* optional: makes it stand out */
            margin-bottom: 10px;         /* space between label and input */
            
        }}
        #label-search {{
                        display: block;
                        margin: 0 auto;
                        width: 80%;
                        height: 40px;            /* increases height */
                        padding: 10px 12px;      /* adds internal space */
                        font-size: 1.1em;        /* makes text slightly larger */
                        border: 1px solid #ccc;
                        border-radius: 6px;      /* optional rounded corners */
                        box-sizing: border-box;
                    }}
        #node-config select, #node-config input[type="number"], #node-config input[type="text"], #description-table table {{
            width: 100%;
            padding: 5px;
            border-radius: 3px;
            border: 1px solid #ccc;
            box-sizing: border-box;
        }}
        #node-config .size-inputs {{
            display: flex;
            gap: 5px;
        }}
        #node-config .size-inputs input[type="number"] {{
            flex: 1;
        }}
        .legend {{
            cursor: pointer;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 8px 12px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 14px;
            font-weight: bold;
            color: #333;
            text-align: center;
        }}
        .panel-hidden {{
            display: none;
        }}
        #node-config p {{
            font-size: 12px;
            color: #555;
            margin: 5px 0;
        }}
        .vis-icon {{
            font-family: "Font Awesome 5 Free" !important;
            font-weight: 900;
        }}
        #description-table table {{
            border-collapse: collapse;
            width: 100%;
        }}
        #description-table th, #description-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        #description-table th {{
            background-color: #f2f2f2;
        }}
        #color-select, #shape-select, #title-select, #edge-color-select {{
            height: 100px;
        }}
        #node-edge-count {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 8px 12px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 14px;
            font-weight: bold;
            color: #333;
            text-align: center;
        }}
        .suggestions {{
            position: absolute;
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 3px;
            max-height: 150px;
            overflow-y: auto;
            width: 100%;
            z-index: 200;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: none;
        }}
        .suggestion-item {{
            padding: 5px 10px;
            cursor: pointer;
        }}
        .suggestion-item:hover {{
            background-color: #f0f0f0;
        }}
    </style>
    </head>
    <body>
    <h2 id="diagram-title">{network_title}</h2>
    <div id="mynetwork"></div>
    <div id="loading-bar">
        <div id="loading-progress"></div>
        <span id="loading-percentage">0%</span>
    </div>
    <div id="config-container">
        <div class="legend" onclick="togglePanel('node-config')">Node & Edge Selection</div>
        <div id="node-config" class="panel-hidden">
            <div class="filter-group">
                <label class="label-search">Node Label Search</label>
                <input type="text" id="label-search" placeholder="Enter labels, e.g., Node1,Node2" oninput="updateSuggestions()">
                <div id="label-suggestions" class="suggestions"></div>
            </div>
            <div class="filter-group">
                <label>Maximum Nodes to Display</label>
                <select id="max-display-select" onchange="updateNodes()">
                    {max_display_options}
                </select>
            </div>
            <div class="filter-group">
                <label>Node Color</label>
                <select id="color-select" multiple onchange="updateNodes()">
                    <option value="all" selected>All</option>
                    {color_options}
                </select>
            </div>
            <div class="filter-group">
                <label>Node Shape</label>
                <select id="shape-select" multiple onchange="updateNodes()">
                    <option value="all" selected>All</option>
                    {shape_options}
                </select>
            </div>
            <div class="filter-group">
                <label>Node Size ({min_size}-{max_size})</label>
                <div class="size-inputs">
                    <input type="number" id="size-min" value="{min_default_node_size}" placeholder="Min" min="0" oninput="updateNodes()">
                    <input type="number" id="size-max" placeholder="Max" min="0" oninput="updateNodes()">
                </div>
            </div>

            <div class="filter-group">
                <label>Node Title (Class)</label>
                <select id="title-select" multiple onchange="updateNodes()">
                    <option value="all" selected>All</option>
                    {title_options}
                </select>
            </div>
            <div class="filter-group">
                <label>Edge Width ({min_width}-{max_width})</label>
                <div class="size-inputs">
                    <input type="number" id="width-min" value="{min_default_edge_width}" placeholder="min" min="0" oninput="updateNodes()">
                    <input type="number" id="width-max" placeholder="Max" min="0" oninput="updateNodes()">
                </div>
            </div>
            <div class="filter-group">
                <label>Edge Color</label>
                <select id="edge-color-select" multiple onchange="updateNodes()">
                    <option value="all" selected>All</option>
                    {edge_color_options}
                </select>
            </div>
        </div>
        <div class="legend" onclick="togglePanel('physics-config')">Physics</div>
        <div id="physics-config" class="panel-hidden"></div>
    </div>
    <div id="description-container">
        <div id="node-edge-count" class="legend">
            Nodes: <span id="node-count">0</span>, Edges: <span id="edge-count">0</span>
        </div>
        <div class="legend" onclick="togglePanel('description-table')">Diagram Description</div>
        <div id="description-table" class="panel-hidden">
            <p>{description_title}</p>
            <div class="table-group">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                    {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <div id="save-button-container">
        <button id="save-selection" onclick="saveSelection()">Save Selection</button>
    </div>
    {drag_script}
    {script_code}
    </body>
    </html>
    """

    if writeHTML is None:
        html_add = "network_visualization.html"
    else:
        html_add = writeHTML 
    
    with open(html_add, "w", encoding="utf-8") as file:
        file.write(html_code)
    base_path = os.path.dirname(os.path.abspath(__file__))

    if browserView:
        webbrowser.open(html_add)

    print(f"HTML file has been created: {base_path}/{writeHTML}")
    return None


if __name__ == "__main__":

    
    gipuzkoa_path = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Escudo_de_Donostia.svg/800px-Escudo_de_Donostia.svg.png"
    turku_path = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Turku.vaakuna.svg/800px-Turku.vaakuna.svg.png"
    
    turku_path2 = r"C:\PhDDocs\pythonPhD\pyBase4All\hyperlinks_scrape\scrapper\network_visual\network_visual\Turku.vaakuna.png"
    gipuzkoa_path2 = r"C:\PhDDocs\pythonPhD\pyBase4All\hyperlinks_scrape\scrapper\network_visual\network_visual\Escudo_de_Donostia.png"
    
    turku_img64 = base64_from_loc(turku_path2)
    gipuzkoa_img64 = base64_from_loc(gipuzkoa_path2 )

    nodes = [
        {"id": 1, "label": "Start", "size": 9, "color": "red-spain", "shape": "dot", "title": "starting the point"},
        {"id": 2, "label": "Process A", "size": 25, "color": "#33FF57-france", "shape": "triangle", "title": "process one"},
        {"id": 3, "label": "Process B", "size": 40, "color": "#3357FF-france", "shape": "box-canada", "title": "process two"},
        {"id": 4, "label": "Critical", "size": 35, "color": "#FFBD33-japan", "shape": "star-asia", "title": "critical point"},
        {"id": 5, "label": "User", "size": 45, "color": "#8D33FF-germany", "shape": "icon-africa", 
            "icon": {"face": '"Font Awesome 5 Free"', "code": "\uf007", "size": 50, "color": "#8D33FF-germany"}},
        {"id": 6, "label": "Info A", "size": 48, "color": "#33B5E5-canada", "shape": "icon-africa",
            "icon": {"face": "Font Awesome 5 Brands", "code": "\uf007", "size": 40, "color": "#33B5E5-canada"}},
        {"id": 7, "label": "Image Node A ", "size": 15, "shape": "image-gipuzkoa", "image": gipuzkoa_img64, "color": "#33B5E7-gipuzkoa"},
        {"id": 8, "label": "Gogo", "size": 30, "color": "#FF5733-italy", "shape": "dot", "title": "I am so Alone"},
        {"id": 9, "label": "comecome", "size": 8, "color": "#FF5733-italy", "shape": "dot", "title": "I am so Alone"},
            {"id": 10, "label": "Image Node B", "size": 15, "shape": "image-gipuzkoa", "image": gipuzkoa_img64, "color": "#33B5E7-gipuzkoa"},
            {"id": 11, "label": "Info B", "size": 48, "color": "#33B5E5-canada", "shape": "icon-australia",
            "icon": {"face": "Font Awesome 5 Brands", "code": "\uf05a", "size": 40, "color": "#33B5E5-canada"}},
                {"id": 12, "label": "turku", "size": 15, "shape": "image-turku", "image": turku_img64, "color": "#33B5E6-turku"},
                {"id": 13, "label": "dict", "size": 9, "color": {"background": "yellow-Finland", "border": "green"}, "shape": "dot", "title": "starting the point"},
                {"id":'abcdefg',"label":"abcdefg-label",'shape':'square','size':50},
                
    ]

    edges = [
        {"from": 1, "to": 3, "width": 1, "color": {"color": "#C70039-europe"}, "arrows": "to", "title": "from 1 to 3"},
        {"from": 1, "to": 2, "width": 2, "color": {"color": "#C70038-africa"}},
        {"from": 2, "to": 4, "width": 3, "color": {"color": "#581845-africa"}, "arrows": "to", "dashes": True},
        {"from": 2, "to": 5, "width": 4, "color": {"color": "#FFC300-australia"}, "arrows": "to", "smooth": {"type": "curvedCW"}},
        {"from": 3, "to": 3, "width": 5, "color": {"color": "#DAF7A6-america"}, "arrows": "to"},
        {"from": 4, "to": 6, "width": 6, "color": {"color": "#4CAF50-europe"}, "arrows": "to", "smooth": {"type": "curvedCCW"}},
        {"from": 5, "to": 1, "width": 7, "color": {"color": "#2196F3-asia"}, "arrows": "to", "dashes": True},
        {"from": 7, "to": 1, "width": 8, "color": {"color": "#FF00FF-africa"}, "arrows": "to"},
        {"from":14,"to":13}
    ]
    visnet(nodes, edges, network_title='small Network', browserView=True, writeHTML='test_small.html', min_default_node_size=1, min_default_edge_width=0, maximum_display=10)



    import random 
    nodes2 = []
    edges2 = []

    for i in range(1, 10001):  # Changed to 10,000 nodes
        if i<20:
            size = random.randint(10,20)
        else:
            size = random.randint(1,5)
        width = random.randint(1, 4)
        node = {"id": i, "label": "Node " + str(i), "size": size, "color": random.choice(['red','blue','yellow']), "shape": "dot", "title": "Node " + str(i)}
        nodes2.append(node)
        edge = {"from": random.randint(1, 20), "to": i , "width": width, "color": {"color": "#131112"}, "arrows": "to", "title": f"to {i} width {width}"}
        edges2.append(edge)

    visnet(nodes2, edges2, network_title='Large Network', browserView=True, writeHTML='test_large.html', min_default_node_size=1, min_default_edge_width=1, maximum_display=100)