from __future__ import annotations
import requests
import base64
import json, os
from IPython.display import HTML, display
import pandas as pd
import webbrowser
import random
import html


from pathlib import Path
from os import PathLike
from typing import Any, TypeAlias
NodeId: TypeAlias = str | int
VisNode: TypeAlias = dict[str, Any]
VisEdge: TypeAlias = dict[str, Any]
NetworkXGraph: TypeAlias = Any


def base64_from_url(image_url: str) -> str | None:
    """
    Download an image from a URL and return it as a Base64 data URI.

    The returned string can be used directly in HTML, CSS, or vis.js image
    nodes, for example as the value of a node's ``image`` property.

    Parameters
    ----------
    image_url : str
        URL pointing directly to an image file. The response must have a
        Content-Type header beginning with ``image/``.

    Returns
    -------
    str | None
        A Base64 data URI string such as
        ``"data:image/png;base64,..."`` if successful.
        Returns ``None`` if the image cannot be downloaded, the URL does not
        point to an image, or another error occurs.

    Notes
    -----
    GitHub ``blob`` URLs usually point to an HTML page, not the raw image.
    For GitHub images, use a raw URL such as:

    ``https://raw.githubusercontent.com/user/repo/main/path/image.png``
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


def base64_from_loc(image_local: str | PathLike[str]) -> str | None:
    """
    Convert a local image file into a Base64 data URI.

    The returned string can be used as the ``image`` value for vis.js image
    nodes.

    Parameters
    ----------
    image_local : str | os.PathLike[str]
        Path to a local image file.

    Returns
    -------
    str | None
        A Base64 data URI string such as
        ``"data:image/png;base64,..."`` if successful.
        Returns ``None`` if the file is not found.

    Notes
    -----
    The current implementation always labels the output as ``image/png``.
    If you use JPG, SVG, WebP, or other image formats, consider detecting the
    MIME type with Python's ``mimetypes`` module.
    """
    try:
        with open(image_local, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            base64_image_local = f"data:image/png;base64,{encoded_string}"
            return base64_image_local
    except FileNotFoundError:
        print("Error: Image file not found. Using placeholder image.")
        return None


def nx2vis(G: NetworkXGraph) -> tuple[list[VisNode], list[VisEdge]]:
    """
    Convert a NetworkX graph into vis.js-compatible node and edge lists.

    This function reads nodes and edges from a NetworkX graph and converts
    their attributes into dictionaries that can be passed to ``visnet()``.

    Parameters
    ----------
    G : networkx.Graph | networkx.DiGraph | networkx.MultiGraph | networkx.MultiDiGraph
        A NetworkX graph object. Directed graphs are rendered with arrows by
        default unless an edge already defines its own ``arrows`` attribute.

    Returns
    -------
    tuple[list[VisNode], list[VisEdge]]
        A tuple containing:

        ``vis_nodes``
            List of vis.js-compatible node dictionaries.

        ``vis_edges``
            List of vis.js-compatible edge dictionaries.

    Supported node attributes
    -------------------------
    The following NetworkX node attributes are mapped to vis.js node options:

    - ``label``
    - ``size``
    - ``shape``
    - ``title``
    - ``color``
    - ``font``
    - ``icon``
    - ``image``
    - ``group``
    - ``mass``
    - ``physics``
    - ``hidden``
    - ``fixed``

    Additional handling:

    - If a node has a ``pos`` attribute as ``(x, y)``, the node receives
      fixed ``x`` and ``y`` coordinates.
    - If ``label`` is missing, the node ID is used as the label.
    - If ``title`` is missing, ``"Node {id}"`` is used.

    Supported edge attributes
    -------------------------
    The following NetworkX edge attributes are mapped to vis.js edge options:

    - ``label``
    - ``title``
    - ``color``
    - ``dashes``
    - ``smooth``
    - ``arrows``
    - ``physics``
    - ``hidden``

    Edge width handling
    -------------------
    Edge width is read in this priority order:

    1. ``width``
    2. ``weight``
    3. default value ``1``

    Notes
    -----
    If edge weights are strings, for example ``"2"`` instead of ``2``,
    later numeric comparisons in ``visnet()`` may fail unless the value is
    converted to ``float`` or ``int``.
    """
    vis_nodes = []
    vis_edges = []

    is_directed = G.is_directed()

    NODE_ATTR_MAP = {
        "label": "label",
        "size": "size",
        "shape": "shape",
        "title": "title",
        "color": "color",
        "font": "font",
        "icon": "icon",
        "image": "image",
        "group": "group",
        "mass": "mass",
        "physics": "physics",
        "hidden": "hidden",
        "fixed": "fixed",
    }

    EDGE_ATTR_MAP = {
        "label": "label",
        "title": "title",
        "color": "color",
        "dashes": "dashes",
        "smooth": "smooth",
        "arrows": "arrows",
        "physics": "physics",
        "hidden": "hidden",
    }

    for n, data in G.nodes(data=True):
        node_entry = {
            "id": n,
            "label": str(data.get("label", n)),
            "size": data.get("size", 2),
            "shape": data.get("shape", "dot"),
            "title": data.get("title", f"Node {n}"),
            "color": data.get("color", "#97C2FC"),
        }

        if "pos" in data and isinstance(data["pos"], (tuple, list)):
            node_entry["x"] = data["pos"][0]
            node_entry["y"] = data["pos"][1]
            node_entry["fixed"] = True

        for nx_attr, vis_attr in NODE_ATTR_MAP.items():
            if nx_attr in data:
                node_entry[vis_attr] = data[nx_attr]

        vis_nodes.append(node_entry)

    for u, v, data in G.edges(data=True):
        width = data.get("width", data.get("weight", 1))
        try:
            width = float(width)
        except (TypeError, ValueError):
            width = 1.0

        if "arrows" in data:
            arrows = data["arrows"]
        else:
            arrows = "to" if is_directed else ""

        edge_entry = {
            "from": u,
            "to": v,
            "width": width,
            "arrows": arrows,
            "label": data.get("label", ""),
            "title": data.get("title", f"from {u} to {v}"),
            "color": data.get("color", {"color": "#848484"}),
        }

        for nx_attr, vis_attr in EDGE_ATTR_MAP.items():
            if nx_attr in data:
                edge_entry[vis_attr] = data[nx_attr]

        vis_edges.append(edge_entry)

    return vis_nodes, vis_edges

def visnet(
    G: NetworkXGraph| None = None,
    nodes: list[VisNode] | tuple[VisNode, ...] | None = None,
    edges: list[VisEdge] | tuple[VisEdge, ...] | None = None,
    network_title: str | None = "Atsaniik",
    network_subtitle: str | None = None,
    description_df: pd.DataFrame | None = None,
    description_title: str = "Introduce your network",
    writeHTML: str | None = "network_visualization.html",
    browserView: bool = False,
    min_default_node_size: int | float = 0,
    min_default_edge_width: int | float | None = 0,
    maximum_display: int = 100,
    plotly_fig: Any | None = None,
    freeText: str | None = None,
) -> None:
    """
    Generate an interactive vis.js network visualization as an HTML file.

    The function accepts either a NetworkX graph through ``G`` or explicit
    vis.js-style ``nodes`` and ``edges`` lists. It writes a standalone HTML
    file containing an interactive network diagram with filtering controls,
    node and edge counters, a description table, optional Plotly chart panel,
    and export buttons for the currently displayed node and edge selection.

    Parameters
    ----------
    G : networkx.Graph | networkx.DiGraph | networkx.MultiGraph | networkx.MultiDiGraph | None, default None
        Optional NetworkX graph to visualize.

        If provided, ``G`` is converted into vis.js-compatible node and edge
        dictionaries using ``nx2vis(G)``. In that case, the ``nodes`` and
        ``edges`` arguments are ignored.

        For directed graphs, edges receive ``"arrows": "to"`` by default
        unless an edge already contains an ``arrows`` attribute.

    nodes : list[VisNode] | tuple[VisNode, ...] | None, default None
        Optional list or tuple of vis.js-compatible node dictionaries.

        Each node dictionary should contain at least:

        ``id``
            Unique node identifier. Usually ``str`` or ``int``.

        Common optional node keys include:

        ``label``
            Text shown near the node. Defaults to ``str(id)``.

        ``size``
            Numeric node size. Defaults to ``1``.

        ``color``
            Node color. Can be a string such as ``"red"`` or a vis.js color
            dictionary such as ``{"background": "red", "border": "black"}``.

            This function also supports custom label suffixes such as
            ``"red-group1"``. The suffix is used in filter menus, while the
            base color before ``"-"`` is passed to vis.js.

        ``shape``
            vis.js node shape. Examples: ``"dot"``, ``"box"``,
            ``"triangle"``, ``"star"``, ``"icon"``, ``"image"``.

            This function also supports custom shape labels such as
            ``"box-category1"``, ``"icon-person"``, or ``"image-logo"``.

        ``title``
            HTML hover tooltip text for the node.

        ``icon``
            Font Awesome icon configuration for nodes with shape ``"icon"``.

        ``image``
            Image URL or Base64 data URI for nodes with shape ``"image"``.

        ``pos``
            Optional NetworkX-style position tuple/list ``(x, y)``. If
            present, the node receives fixed coordinates in the visualization.

    edges : list[VisEdge] | tuple[VisEdge, ...] | None, default None
        Optional list or tuple of vis.js-compatible edge dictionaries.

        Each edge dictionary should contain at least:

        ``from``
            Source node ID.

        ``to``
            Target node ID.

        Common optional edge keys include:

        ``width``
            Numeric edge width. Defaults to ``1``.

        ``weight``
            Alternative source for edge width when converting from NetworkX.

        ``color``
            Edge color dictionary, for example
            ``{"color": "gray"}``.

            This function also supports custom label suffixes such as
            ``{"color": "#C70039-europe"}``. The suffix is used in filter
            menus, while the base color before ``"-"`` is passed to vis.js.

        ``arrows``
            Edge arrow setting. Common value: ``"to"``.

        ``label``
            Edge label text.

        ``title``
            Hover tooltip text for the edge.

        ``dashes``
            Whether the edge should be dashed.

        ``smooth``
            vis.js smooth edge configuration.

    network_title : str | None, default "Atsaniik"
        Main title displayed on top of the network. The title box is draggable.
        If ``None``, the current implementation may display ``"None"`` unless
        handled separately.

    network_subtitle : str | None, default None
        Optional subtitle displayed below the main title. The subtitle box is
        draggable. If ``None`` or empty, no subtitle is shown.

    description_df : pandas.DataFrame | None, default None
        Optional dataframe used to populate the diagram description table.

        If ``None``, a default dataframe is created with:

        - number of nodes
        - number of edges

        All dataframe values are escaped before being inserted into the HTML
        table.

    description_title : str, default "Introduce your network"
        Title shown in the description popup window.

    writeHTML : str | None, default "network_visualization.html"
        Output HTML file name.

        If ``None``, the function currently uses ``"network.html"``.
        The file is written into a ``netOutPut`` subfolder.

    browserView : bool, default False
        If ``True``, open the generated HTML file in the default web browser
        after writing it.

    min_default_node_size : int | float, default 0
        Initial minimum node size used in the node size filter.

        Nodes smaller than this value are excluded when filters are applied.

    min_default_edge_width : int | float | None, default 0
        Initial minimum edge width used in the edge width filter.

        If ``None``, no minimum edge width is applied during initial edge
        selection.

    maximum_display : int, default 100
        Maximum number of nodes displayed initially and after filtering.

        Nodes are sorted by descending ``size`` before applying this limit.
        If all nodes have the same size, their order is randomized.

    plotly_fig : Any | None, default None
        Optional Plotly figure object.

        If provided, the Plotly figure is converted to an HTML fragment and
        displayed in a draggable, resizable panel that can be toggled from the
        interface.

        The object is expected to support:

        - ``update_layout()``
        - ``to_html()``

    freeText : str | None, default None
        Optional free text displayed in the lower-right corner of the diagram.
        The text is HTML-escaped before insertion.

    Returns
    -------
    None
        The function writes an HTML file to disk and optionally opens it in a
        browser. It does not return the generated HTML.

    Generated interface features
    ----------------------------
    The HTML output includes:

    - interactive vis.js network visualization
    - node label search with suggestions
    - node filtering by color, shape, size, and title/class
    - edge filtering by color and width
    - maximum displayed node count selector
    - node and edge count display
    - physics configuration panel
    - diagram description popup table
    - draggable title and subtitle
    - optional Plotly chart panel
    - optional free-text box
    - save button for exporting the current node and edge selection as JSON

    Notes
    -----
    This function writes a standalone HTML file, but the generated page depends
    on external CDN resources for:

    - ``vis-network``
    - Font Awesome
    - Plotly, if ``plotly_fig`` is used with CDN JavaScript

    Therefore, the generated visualization may require an internet connection
    unless these dependencies are replaced with local files.

    Important implementation details
    --------------------------------
    The current implementation mutates node and edge dictionaries internally.
    If you need to preserve the original input data unchanged, consider making
    deep copies at the start of the function:

    ``nodes = copy.deepcopy(nodes)``

    ``edges = copy.deepcopy(edges)``

    Also, if this function is used in Jupyter notebooks, ``__file__`` may not
    be available. In that case, use ``Path.cwd()`` for the output folder.

    Examples
    --------
    Visualize a NetworkX directed graph:

    >>> import networkx as nx
    >>> G = nx.DiGraph()
    >>> G.add_weighted_edges_from([
    ...     ("B", "A", 5),
    ...     ("C", "A", 2),
    ...     ("D", "A", 1),
    ...     ("B", "C", 2),
    ... ])
    >>> visnet(G, network_title="Knowledge sharing network")

    Visualize explicit node and edge dictionaries:

    >>> nodes = [
    ...     {"id": 1, "label": "Start", "size": 10, "color": "red", "shape": "dot"},
    ...     {"id": 2, "label": "End", "size": 20, "color": "blue", "shape": "box"},
    ... ]
    >>> edges = [
    ...     {"from": 1, "to": 2, "width": 3, "arrows": "to"},
    ... ]
    >>> visnet(nodes=nodes, edges=edges, network_title="Simple network")
    """

    nodes = [] if nodes is None else list(nodes)
    edges = [] if edges is None else list(edges)

    if G is not None:
        nodes, edges = nx2vis(G)

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    defaults_node = {
        "label": lambda node: str(node["id"]),
        "size": 1,
        "color": "gray",
        "shape": "dot",
        "title": lambda node: str(node["id"])
    }

    nodeIDchecks = []
    for node in nodes:
        nodeIDcheck = node["id"]
        nodeIDchecks.append(nodeIDcheck)

        for key, default_value in defaults_node.items():
            if key not in node:
                node[key] = default_value(node) if callable(default_value) else default_value

    defaults_edge = {
        "width": 1,
        "color": {"color": "gray"},
        "title": lambda edge: str(edge["from"]) + " - " + str(edge["to"])
    }

    for edge in edges:
        edgeIDcheck = [edge["from"], edge["to"]]
        missingNodes = [x for x in edgeIDcheck if x not in nodeIDchecks]

        if len(missingNodes) > 0:
            print(f"edge {edge['from']}-{edge['to']} missing nodes description: {missingNodes}")

        for key, default_value in defaults_edge.items():
            if key not in edge:
                edge[key] = default_value(edge) if callable(default_value) else default_value

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def extract_base_value(full_value, is_shape=False):
        if isinstance(full_value, str) and "-" in full_value:
            return full_value.split("-")[0]
        return full_value

    # ------------------------------------------------------------------
    # Validate colors
    # ------------------------------------------------------------------
    node_colors = [
        node["color"]["background"] if isinstance(node["color"], dict) else node["color"]
        for node in nodes
        if "color" in node
    ]

    edge_colors_raw = [
        edge["color"]["color"]
        for edge in edges
        if "color" in edge and isinstance(edge["color"], dict) and "color" in edge["color"]
    ]

    color_bases = {}
    for color in node_colors + edge_colors_raw:
        base = extract_base_value(color)

        if base in color_bases:
            color_bases[base].add(str(color))
        else:
            color_bases[base] = {str(color)}

    for base, variants in color_bases.items():
        if len(variants) > 1:
            print(
                f"Error: Multiple extra labels detected for base color '{base}': "
                f"{', '.join(variants)}. Execution stopped."
            )
            return

    # ------------------------------------------------------------------
    # Validate shapes, icons, and images
    # ------------------------------------------------------------------
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

            if base == "icon" and "icon" in node and "code" in node["icon"]:
                shape_label = full_shape.split("-")[1] if "-" in full_shape else full_shape

                if node["icon"]["code"] in icon_shapes:
                    icon_shapes[node["icon"]["code"]].add(shape_label)
                else:
                    icon_shapes[node["icon"]["code"]] = {shape_label}

            elif base == "image" and "image" in node:
                shape_label = full_shape.split("-")[1] if "-" in full_shape else full_shape
                image_value = str(node["image"])

                if image_value in image_shapes:
                    image_shapes[image_value].add(shape_label)
                else:
                    image_shapes[image_value] = {shape_label}

    for code, shapes_set in icon_shapes.items():
        if len(shapes_set) > 1:
            print(
                f"Error: Inconsistent icon code '{code}' used with different shape names: "
                f"{', '.join(shapes_set)}. Execution stopped."
            )
            return

    for image_value, shapes_set in image_shapes.items():
        if len(shapes_set) > 1:
            print(
                f"Error: Inconsistent image name '{image_value}' used with different shape names: "
                f"{', '.join(shapes_set)}. Execution stopped."
            )
            return

    for base, variants in shape_bases.items():
        if len(variants) > 1 and base not in ["icon", "image"]:
            print(
                f"Error: Multiple extra labels detected for base shape '{base}': "
                f"{', '.join(variants)}. Execution stopped."
            )
            return

    # ------------------------------------------------------------------
    # Description table
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    if description_df is None:
        df = pd.DataFrame({
            "Name": ["Nodes amount", "Edges amount"],
            "Description": [len(nodes), len(edges)]
        })
    else:
        df = description_df.copy()

    # Replace NaN values with empty strings
    df = df.fillna("")

    # Create table headers dynamically from all dataframe columns
    table_headers = "".join([
        f"<th>{html.escape(str(col))}</th>"
        for col in df.columns
    ])

    # Create table rows dynamically from all dataframe values
    if df.empty:
        table_rows = f"""
        <tr>
            <td colspan="{max(len(df.columns), 1)}">No description data available</td>
        </tr>
        """
    else:
        table_rows = "".join([
            "<tr>" + "".join([
                f"<td>{html.escape(str(value))}</td>"
                for value in row
            ]) + "</tr>"
            for _, row in df.iterrows()
        ])

    # ------------------------------------------------------------------
    # Initial display set
    # ------------------------------------------------------------------
    all_nodes = sorted(nodes, key=lambda x: x["size"], reverse=True)

    unique_sizes = len(set(node["size"] for node in all_nodes))
    if unique_sizes == 1:
        random.shuffle(all_nodes)

    initial_nodes = all_nodes[:maximum_display]
    initial_node_ids = set(node["id"] for node in initial_nodes)

    initial_edges = [
        edge for edge in edges
        if edge["from"] in initial_node_ids
        and edge["to"] in initial_node_ids
        and (min_default_edge_width is None or edge["width"] >= min_default_edge_width)
    ]

    min_size = round(min(node["size"] for node in all_nodes), 2) if all_nodes else 0.00
    max_size = round(max(node["size"] for node in all_nodes), 2) if all_nodes else 0.00
    min_width = round(min(edge["width"] for edge in edges), 2) if edges else 0.00
    max_width = round(max(edge["width"] for edge in edges), 2) if edges else 0.00

    colors = sorted(set(
        node["color"]["background"] if isinstance(node["color"], dict) else node["color"]
        for node in all_nodes
    ))

    shapes = sorted(set(node["shape"] for node in nodes))

    titles = sorted(set(
        node.get("title", "")
        for node in all_nodes
        if "title" in node
    ))

    edge_colors = sorted(set(
        edge["color"]["color"]
        if isinstance(edge.get("color"), dict) and "color" in edge["color"]
        else "gray"
        for edge in edges
    ))

    # ------------------------------------------------------------------
    # Normalize shapes and colors
    # ------------------------------------------------------------------
    for node in all_nodes:
        full_shape = node["shape"]
        base_shape = extract_base_value(full_shape, is_shape=True)

        node["shape_label"] = full_shape
        node["shape"] = base_shape

        if isinstance(node["color"], dict):
            color_base = extract_base_value(node["color"].get("background", ""))
            node["color"] = {
                "background": color_base,
                "border": node["color"].get("border", "gray")
            }
        else:
            color_base = extract_base_value(node["color"])
            node["color"] = {
                "background": color_base,
                "border": "gray"
            }

    for edge in edges:
        if isinstance(edge.get("color"), dict) and "color" in edge["color"]:
            edge["color"]["color"] = extract_base_value(edge["color"]["color"])
        else:
            edge["color"] = {"color": "gray"}

    # ------------------------------------------------------------------
    # HTML select options
    # ------------------------------------------------------------------
    color_options = "\n".join([
        f'            <option value="{color}">{color}</option>'
        for color in colors
    ])

    shape_options = "\n".join([
        f'            <option value="{shape}">{shape}</option>'
        for shape in shapes
    ])

    title_options = "\n".join([
        f'            <option value="{title}">{title}</option>'
        for title in titles
        if title
    ])

    edge_color_options = "\n".join([
        f'            <option value="{color}">{color}</option>'
        for color in edge_colors
    ])

    max_display_values = [
        1, 5, 10, 20, 30, 50, 60, 70, 80, 90,
        100, 108, 150, 200, 300, 400, 500,
        1000, 2000, 5000, 10000, 20000
    ]

    max_display_options = "\n".join([
        f'            <option value="{val}"{" selected" if val == maximum_display else ""}>{val}</option>'
        for val in max_display_values
    ])

    nodes_json = json.dumps(initial_nodes, ensure_ascii=False)
    all_nodes_json = json.dumps(all_nodes, ensure_ascii=False)
    all_edges_json = json.dumps(edges, ensure_ascii=False)
    edges_json = json.dumps(initial_edges, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Optional Plotly panel
    # ------------------------------------------------------------------
    if plotly_fig is not None:
        plotly_fig.update_layout(
            autosize=True,
            width=None,
            height=None
        )

        plotly_html_fragment = plotly_fig.to_html(
            full_html=False,
            include_plotlyjs="cdn",
            default_width="100%",
            default_height="100%",
            config={"responsive": True}
        )

        plotly_panel_html = f"""
        <div id="plotly-panel" style="display:none;">
            <div id="plotly-header">
                <span>Interactive Chart</span>
                <button type="button" onclick="togglePanel('plotly-panel', event)" title="Hide">✕</button>
            </div>
            <div id="plotly-content">
                {plotly_html_fragment}
            </div>
        </div>
        """

        plotly_toggle_html = """
        <div class="legend save-row-toggle" onclick="togglePanel('plotly-panel', event)">
            Show Chart
        </div>
        """
        plotly_drag_script = """
        <script type="text/javascript">
        (function() {
            var panel = document.getElementById('plotly-panel');
            var header = document.getElementById('plotly-header');
            var content = document.getElementById('plotly-content');

            if (!panel || !header || !content) return;

            var isDragging = false;
            var offsetX = 0;
            var offsetY = 0;

            function resizePlotlyGraphs() {
                if (!window.Plotly) return;

                var graphs = panel.querySelectorAll('.plotly-graph-div');

                graphs.forEach(function(graphDiv) {
                    try {
                        Plotly.Plots.resize(graphDiv);
                    } catch (err) {
                        console.warn("Plotly resize failed:", err);
                    }
                });
            }

            header.addEventListener('mousedown', function(e) {
                if (e.target.closest('button')) return;

                isDragging = true;

                var rect = panel.getBoundingClientRect();

                offsetX = e.clientX - rect.left;
                offsetY = e.clientY - rect.top;

                panel.style.left = rect.left + 'px';
                panel.style.top = rect.top + 'px';
                panel.style.right = 'auto';
            });

            document.addEventListener('mousemove', function(e) {
                if (!isDragging) return;

                e.preventDefault();

                panel.style.left = (e.clientX - offsetX) + 'px';
                panel.style.top = (e.clientY - offsetY) + 'px';
                panel.style.right = 'auto';
            });

            document.addEventListener('mouseup', function() {
                if (isDragging) {
                    isDragging = false;
                    resizePlotlyGraphs();
                }
            });

            if (window.ResizeObserver) {
                var resizeObserver = new ResizeObserver(function() {
                    resizePlotlyGraphs();
                });

                resizeObserver.observe(panel);
                resizeObserver.observe(content);
            }

            window.addEventListener('resize', resizePlotlyGraphs);

            setTimeout(resizePlotlyGraphs, 300);
        })();
        </script>
        """

    else:
        plotly_panel_html = ""
        plotly_toggle_html = ""
        plotly_drag_script = ""

    # ------------------------------------------------------------------
    # Draggable title
    drag_script = """
    <script type="text/javascript">
        function makeElementDraggable(elementId, defaultX, defaultY) {
            var element = document.getElementById(elementId);

            if (!element) return;

            var isDragging = false;
            var currentX = parseInt(window.getComputedStyle(element).left) || defaultX;
            var currentY = parseInt(window.getComputedStyle(element).top) || defaultY;
            var initialX;
            var initialY;

            function startDragging(e) {
                initialX = e.clientX - currentX;
                initialY = e.clientY - currentY;
                isDragging = true;
                element.style.cursor = 'grabbing';
            }

            function stopDragging() {
                isDragging = false;
                element.style.cursor = 'move';
            }

            function dragElement(e) {
                if (!isDragging) return;

                e.preventDefault();

                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;

                element.style.left = currentX + 'px';
                element.style.top = currentY + 'px';
            }

            element.addEventListener('mousedown', startDragging);
            document.addEventListener('mousemove', dragElement);
            document.addEventListener('mouseup', stopDragging);

            element.style.userSelect = 'none';
        }

        makeElementDraggable('diagram-title', 50, 10);
        makeElementDraggable('diagram-subtitle', 50, 70);
    </script>
    """

    # ------------------------------------------------------------------
    # Main JavaScript
    # ------------------------------------------------------------------
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

    var uniqueLabels = [...new Set(
        allNodes.map(node => node.label).filter(label => label)
    )].sort();

    var previousNodes = originalNodes;
    var previousEdges = originalEdges;

    var container = document.getElementById('mynetwork');

    if (!container) {{
        console.error("Container #mynetwork not found.");
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
            font: {{
                size: 14,
                color: '#333333'
            }},
            borderWidth: 2,
            color: {{
                background: '#97C2E6',
                border: '#2B7CE9',
                highlight: {{
                    background: '#D2E5FF',
                    border: '#2B7CE9'
                }},
                hover: {{
                    background: '#D2E5FF',
                    border: '#2B7CE9'
                }}
            }}
        }},
        edges: {{
            width: 1,
            color: {{
                color: '#848484',
                highlight: '#848484',
                hover: '#848484',
                inherit: 'from',
                opacity: 0.8
            }},
            smooth: {{
                enabled: true,
                type: "dynamic"
            }},
            font: {{
                size: 12
            }}
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
        console.error("Failed to initialize vis.Network.");
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
        if (!selectElement) return [];
        return Array.from(selectElement.selectedOptions).map(option => option.value);
    }}

    function hideSuggestions() {{
        var suggestionsDiv = document.getElementById('label-suggestions');

        if (suggestionsDiv) {{
            suggestionsDiv.innerHTML = '';
            suggestionsDiv.style.display = 'none';
        }}
    }}

    function updateSuggestions() {{
        var inputEl = document.getElementById('label-search');
        var suggestionsDiv = document.getElementById('label-suggestions');

        if (!inputEl || !suggestionsDiv) return;

        var input = inputEl.value;
        suggestionsDiv.innerHTML = '';
        suggestionsDiv.style.display = 'none';

        if (input.trim() === '') {{
            updateNodes();
            return;
        }}

        var terms = input.split(',').map(term => term.trim());
        var lastTerm = terms[terms.length - 1].toLowerCase();

        if (!lastTerm) return;

        var matches = uniqueLabels
            .filter(label => label.toLowerCase().includes(lastTerm))
            .slice(0, 80);

        if (matches.length === 0) {{
            suggestionsDiv.style.display = 'none';
            return;
        }}

        matches.forEach(function(label) {{
            var div = document.createElement('div');
            div.className = 'suggestion-item';
            div.textContent = label;

            div.addEventListener('mousedown', function(event) {{
                event.preventDefault();

                var currentTerms = inputEl.value.split(',').slice(0, -1);
                currentTerms.push(label);

                inputEl.value = currentTerms.join(',') + ',';

                hideSuggestions();
                updateNodes();
            }});

            suggestionsDiv.appendChild(div);
        }});

        suggestionsDiv.style.display = 'block';
    }}

    document.addEventListener('mousedown', function(event) {{
        var wrapper = document.querySelector('.label-search-wrapper');

        if (!wrapper) return;

        if (!wrapper.contains(event.target)) {{
            hideSuggestions();
        }}
    }});

    function saveSelection() {{
        var currentNodes = nodes.get();
        var currentEdges = edges.get();

        var nodesJson = JSON.stringify(currentNodes, null, 2);
        var edgesJson = JSON.stringify(currentEdges, null, 2);

        var nodesBlob = new Blob([nodesJson], {{ type: 'application/json' }});
        var edgesBlob = new Blob([edgesJson], {{ type: 'application/json' }});

        var nodesUrl = URL.createObjectURL(nodesBlob);
        var edgesUrl = URL.createObjectURL(edgesBlob);

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

        URL.revokeObjectURL(nodesUrl);
        URL.revokeObjectURL(edgesUrl);
    }}

    function updateNodes(zoomCenter = null, zoomDirection = null) {{
        var maxDisplay = parseInt(document.getElementById('max-display-select').value) || {maximum_display};

        var colorSelect = getSelectedOptions(document.getElementById('color-select'));
        var shapeSelect = getSelectedOptions(document.getElementById('shape-select'));

        var sizeMin = parseFloat(document.getElementById('size-min').value) || 0;
        var sizeMaxValue = document.getElementById('size-max').value;
        var sizeMax = sizeMaxValue ? parseFloat(sizeMaxValue) : Infinity;

        var labelSearch = document.getElementById('label-search').value;

        var titleSelect = getSelectedOptions(document.getElementById('title-select'));

        var widthMinValue = document.getElementById('width-min').value;
        var widthMaxValue = document.getElementById('width-max').value;

        var widthMin = widthMinValue ? parseFloat(widthMinValue) : null;
        var widthMax = widthMaxValue ? parseFloat(widthMaxValue) : null;

        var edgeColorSelect = getSelectedOptions(document.getElementById('edge-color-select'));

        var filteredNodes = allNodes.slice();
        var filteredEdges = allEdges.slice();

        if (labelSearch.trim() !== '') {{
            previousNodes = nodes.get();
            previousEdges = edges.get();

            var searchTerms = labelSearch
                .split(',')
                .map(term => term.trim().toLowerCase())
                .filter(term => term !== '');

            var selectedNodes = allNodes.filter(function(node) {{
                return node.label && searchTerms.some(term => node.label.toLowerCase() === term);
            }});

            var neighborIds = new Set();

            selectedNodes.forEach(function(node) {{
                neighborIds.add(node.id);

                allEdges.forEach(function(edge) {{
                    if (edge.from === node.id) neighborIds.add(edge.to);
                    if (edge.to === node.id) neighborIds.add(edge.from);
                }});
            }});

            filteredNodes = allNodes.filter(function(node) {{
                return neighborIds.has(node.id);
            }});
        }}

        var validNodeIds = new Set();

        if (widthMin !== null || widthMax !== null) {{
            filteredEdges = allEdges.filter(function(edge) {{
                var widthMatch = true;

                if (widthMin !== null) widthMatch = widthMatch && edge.width >= widthMin;
                if (widthMax !== null) widthMatch = widthMatch && edge.width <= widthMax;

                return widthMatch;
            }});

            if (widthMin !== null && widthMin > 0) {{
                filteredEdges.forEach(function(edge) {{
                    validNodeIds.add(edge.from);
                    validNodeIds.add(edge.to);
                }});

                filteredNodes = filteredNodes.filter(function(node) {{
                    return validNodeIds.has(node.id)
                        || filteredEdges.some(edge => edge.from === node.id || edge.to === node.id);
                }});
            }}
        }}

        filteredNodes = filteredNodes.filter(function(node) {{
            var fullColor = typeof node.color === 'string'
                ? node.color
                : node.color.background;

            var fullShape = node.shape_label || node.shape;

            var colorMatch = colorSelect.includes('all')
                || colorSelect.some(function(cs) {{
                    return fullColor === cs || String(fullColor).startsWith(cs.split('-')[0]);
                }});

            var shapeMatch = shapeSelect.includes('all')
                || shapeSelect.includes(fullShape)
                || shapeSelect.includes(node.shape);

            var sizeMatch = node.size >= sizeMin && node.size <= sizeMax;

            var titleMatch = titleSelect.includes('all')
                || (node.title && titleSelect.includes(node.title));

            return colorMatch && shapeMatch && sizeMatch && titleMatch;
        }});

        filteredNodes.sort((a, b) => b.size - a.size);
        filteredNodes = filteredNodes.slice(0, maxDisplay);

        filteredEdges = allEdges.filter(function(edge) {{
            var fullEdgeColor = edge.color.color;

            var colorMatch = edgeColorSelect.includes('all')
                || edgeColorSelect.some(function(ecs) {{
                    return fullEdgeColor === ecs || String(fullEdgeColor).startsWith(ecs.split('-')[0]);
                }});

            var widthMatch = true;

            if (widthMin !== null) widthMatch = widthMatch && edge.width >= widthMin;
            if (widthMax !== null) widthMatch = widthMatch && edge.width <= widthMax;

            var nodeMatch = filteredNodes.some(n => n.id === edge.from)
                && filteredNodes.some(n => n.id === edge.to);

            return colorMatch && widthMatch && nodeMatch;
        }});

        document.getElementById('node-count').textContent = filteredNodes.length;
        document.getElementById('edge-count').textContent = filteredEdges.length;

        nodes.clear();
        nodes.add(filteredNodes);

        edges.clear();
        edges.add(filteredEdges);
    }}

    network.on("zoom", function(params) {{
        var scale = params.scale;

        if (scale > lastScale) {{
            if (params.pointer && params.pointer.DOM) {{
                var pointerDOM = params.pointer.DOM;
                var pointerCanvas = network.DOMtoCanvas(pointerDOM);
                lastZoomCenter = pointerCanvas;
            }}

            updateNodes(lastZoomCenter, 'in');

        }} else if (scale < lastScale) {{
            updateNodes(null, 'out');
        }}

        lastScale = scale;
    }});

    var labelSearchEl = document.getElementById('label-search');

    if (labelSearchEl) {{
        labelSearchEl.addEventListener('keydown', function(event) {{
            if (event.key === 'Enter') {{
                hideSuggestions();
                updateNodes();
            }}

            if (event.key === 'Escape') {{
                hideSuggestions();
            }}
        }});
    }}

    updateNodes();

    window.updateNodes = updateNodes;
    window.updateSuggestions = updateSuggestions;
    window.saveSelection = saveSelection;
    </script>
    """.format(
        all_nodes_json=all_nodes_json,
        all_edges_json=all_edges_json,
        nodes_json=nodes_json,
        edges_json=edges_json,
        maximum_display=maximum_display
    )


    subtitle_html = ""

    if network_subtitle is not None and str(network_subtitle).strip() != "":
        subtitle_html = f'<h3 id="diagram-subtitle">{network_subtitle}</h3>'

    free_text_html = ""

    if freeText is not None and str(freeText).strip() != "":
        free_text_html = f"""
        <div id="free-text-box">
            {html.escape(str(freeText))}
        </div>
        """
    # ------------------------------------------------------------------
    # Final HTML
    # ------------------------------------------------------------------
    html_code = f"""
    <html>
    <head>
    <meta charset="utf-8">

    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>

    <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css"
        crossorigin="anonymous"
        referrerpolicy="no-referrer"
    />

    <script type="text/javascript">
        function togglePanel(panelId, event) {{
            if (event) {{
                event.preventDefault();
                event.stopPropagation();
            }}

            var panel = document.getElementById(panelId);

            if (!panel) {{
                console.error("Panel not found: " + panelId);
                return;
            }}

            var hidden = window.getComputedStyle(panel).display === 'none';

            if (hidden) {{
                if (panelId === 'plotly-panel') {{
                    panel.style.display = 'flex';

                    setTimeout(function() {{
                        if (window.Plotly) {{
                            panel.querySelectorAll('.plotly-graph-div').forEach(function(div) {{
                                try {{
                                    Plotly.Plots.resize(div);
                                }} catch (err) {{
                                    console.warn(err);
                                }}
                            }});
                        }}
                    }}, 50);
                }} else {{
                    panel.style.display = 'block';
                }}
            }} else {{
                panel.style.display = 'none';
            }}
        }}
    </script>

    <style type="text/css">
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: Inter, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background-color: #e0e0e0;
            position: relative;
            overflow: hidden;
        }}

        #mynetwork {{
            width: 100vw;
            height: 100vh;
            border: 1px solid lightgray;
            background-color: #f9f9f9;
            transition: opacity 0.5s ease;
        }}


        #free-text-box {{
            position: absolute;
            right: 5px;
            bottom: 5px;
            z-index: 110;

            display: inline-block;
            width: fit-content;
            max-width: none;

            background: transparent;
            color: #222;

            padding: 0;
            margin: 0;

            border: none;
            border-radius: 0;
            box-shadow: none;

            font-size: 15px;
            line-height: 1.45;
            text-align: center;

            white-space: pre-wrap;
            overflow-wrap: anywhere;
            word-break: normal;
        }}


        #diagram-title {{
            position: absolute;
            top: 10px;
            left: 70px;
            z-index: 100;
            background-color: rgba(255, 255, 255, 0.88);
            padding: 10px 15px;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.14);
            font-size: 24px;
            color: #333;
            cursor: move;
            user-select: none;
        }}

        #diagram-subtitle {{
            position: absolute;
            top: 80px;
            left: 50px;
            z-index: 100;
            background-color: rgba(255, 255, 255, 0.88);
            padding: 8px 13px;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.14);
            font-size: 17px;
            font-weight: 500;
            color: #444;
            cursor: move;
            user-select: none;
            margin: 0;
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

        /* Top-right controls */
        #config-container {{
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 120;
            display: flex;
            flex-direction: column;
            gap: 10px;
            width: 340px;
            max-width: calc(100vw - 40px);
            max-height: calc(100vh - 40px);
            overflow: hidden;
            padding: 0;
        }}

        .config-section {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            width: 100%;
            min-height: 0;
        }}

        .config-panel {{
            background-color: white;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #ccc;
            box-shadow: 0 3px 10px rgba(0,0,0,0.16);

            height: calc(50vh - 60px);
            max-height: calc(50vh - 60px);
            overflow-y: auto;
            overflow-x: hidden;
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
            position: static;
            transform: none;
            z-index: auto;

            display: flex;
            flex-direction: column;
            align-items: stretch;
            gap: 8px;

            width: 100%;
        }}


        #description-table {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);

            width: 75vw;
            height: 70vh;
            max-width: 1100px;
            max-height: 800px;

            background-color: white;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.28);

            z-index: 220;

            overflow: hidden;
            resize: both;
        }}

        #description-popup-header {{
            height: 42px;
            background-color: #f2f2f2;
            border-bottom: 1px solid #ccc;

            display: flex;
            align-items: center;
            justify-content: space-between;

            padding: 8px 12px;
            font-weight: bold;
            color: #333;
        }}

        #description-popup-header button {{
            background: transparent;
            border: none;
            font-size: 16px;
            cursor: pointer;
        }}

        #description-popup-content {{
            height: calc(100% - 42px);
            overflow: auto;
            padding: 12px;
        }}

        #description-table table {{
            border-collapse: collapse;
            width: 100%;
            min-width: 700px;
        }}

        #description-table th,
        #description-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }}

        #description-table th {{
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
            z-index: 1;
        }}





        #save-selection {{
            background-color: white;
            color: #333;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.22);
            width: 100%;
        }}

        #save-selection:hover,
        .legend:hover {{
            background-color: #f3f3f3;
        }}

        #physics-config {{
            background-color: white;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #ccc;
        }}

        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 13px;
            width: 100%;
        }}

        .filter-group label {{
            font-size: 14px;
            font-weight: 650;
            color: #333;
        }}

        .filter-group input,
        .filter-group select {{
            width: 100%;
            box-sizing: border-box;
            border: 1px solid #aaa;
            border-radius: 5px;
            padding: 6px 8px;
            font-size: 14px;
            background-color: #fff;
        }}

        .filter-group select {{
            min-height: 34px;
        }}

        .size-inputs {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            width: 100%;
        }}

        .legend {{
            cursor: pointer;
            background-color: rgba(255, 255, 255, 0.94);
            padding: 9px 13px;
            border-radius: 6px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.14);
            font-size: 14px;
            font-weight: bold;
            color: #333;
            text-align: center;
            white-space: nowrap;
            user-select: none;
            border: 1px solid rgba(0,0,0,0.06);
        }}

        .config-toggle {{
            width: auto;
            align-self: flex-end;
            padding: 6px 10px;
            font-size: 13px;
            line-height: 1.2;
        }}

        .save-row-toggle {{
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        #save-button-container .legend {{
            width: 100%;
        }}

        .panel-hidden {{
            display: none;
        }}



        #color-select,
        #shape-select,
        #title-select,
        #edge-color-select {{
            height: 100px;
        }}

        #node-edge-count {{
            background-color: rgba(255, 255, 255, 0.94);
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: bold;
        }}

        /* Improved Node Label Search */
        .label-search-wrapper {{
            position: relative;
            width: 100%;
        }}

        #label-search {{
            width: 100%;
            height: 38px;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 7px 9px;
            font-size: 14px;
            background-color: #fff;
            outline: none;
        }}

        #label-search:focus {{
            border-color: #222;
            box-shadow: 0 0 0 2px rgba(0,0,0,0.08);
        }}

        #label-suggestions {{
            position: absolute;
            top: calc(100% + 3px);
            left: 0;
            right: 0;
            width: 100%;
            background-color: white;
            border: 1px solid #bbb;
            border-radius: 5px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.22);
            max-height: 210px;
            overflow-y: auto;
            z-index: 10000;
            display: none;
        }}

        .suggestion-item {{
            padding: 7px 10px;
            cursor: pointer;
            font-size: 14px;
            line-height: 1.35;
            color: #222;
            background-color: #fff;
            border-bottom: 1px solid #eee;
            word-break: break-word;
        }}

        .suggestion-item:last-child {{
            border-bottom: none;
        }}

        .suggestion-item:hover {{
            background-color: #eeeeee;
        }}

        #plotly-panel {{
            position: absolute;
            top: 80px;
            right: 80px;
            width: 700px;
            height: 450px;
            min-width: 320px;
            min-height: 240px;
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            z-index: 200;
            flex-direction: column;
            overflow: hidden;
            resize: both;
        }}

        #plotly-header {{
            background-color: #f2f2f2;
            padding: 6px 10px;
            cursor: move;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
            user-select: none;
            border-bottom: 1px solid #ccc;
        }}

        #plotly-header button {{
            background: transparent;
            border: none;
            font-size: 16px;
            cursor: pointer;
            z-index: 201;
            pointer-events: auto;
        }}

        #plotly-content {{
            flex: 1;
            width: 100%;
            height: 100%;
            min-height: 0;
            overflow: hidden;
        }}

        #plotly-content > div,
        #plotly-content .plotly-graph-div {{
            width: 100% !important;
            height: 100% !important;
        }}

    </style>
    </head>

    <body>
        <h2 id="diagram-title">{network_title}</h2>
        {subtitle_html}
        <div id="mynetwork"></div>
        {free_text_html}
        {plotly_panel_html}

        <div id="loading-bar">
            <div id="loading-progress"></div>
            <span id="loading-percentage">0%</span>
        </div>

        <div id="config-container">

            <div class="config-section">
                <div class="legend config-toggle" onclick="togglePanel('node-config', event)">
                    Node &amp; Edge 
                </div>

                <div id="node-config" class="panel-hidden config-panel">
                    <div class="filter-group">
                        <label for="label-search">Node Label Search</label>

                        <div class="label-search-wrapper">
                            <input
                                type="text"
                                id="label-search"
                                placeholder="Enter labels, e.g., Node1,Node2"
                                autocomplete="off"
                                autocorrect="off"
                                autocapitalize="off"
                                spellcheck="false"
                                oninput="updateSuggestions()"
                            >
                            <div id="label-suggestions"></div>
                        </div>
                    </div>

                    <div class="filter-group">
                        <label for="max-display-select">Maximum Nodes to Display</label>
                        <select id="max-display-select" onchange="updateNodes()">
                            {max_display_options}
                        </select>
                    </div>

                    <div class="filter-group">
                        <label for="color-select">Node Color</label>
                        <select id="color-select" multiple onchange="updateNodes()">
                            <option value="all" selected>All</option>
                            {color_options}
                        </select>
                    </div>

                    <div class="filter-group">
                        <label for="shape-select">Node Shape</label>
                        <select id="shape-select" multiple onchange="updateNodes()">
                            <option value="all" selected>All</option>
                            {shape_options}
                        </select>
                    </div>

                    <div class="filter-group">
                        <label>Node Size ({min_size}-{max_size})</label>
                        <div class="size-inputs">
                            <input
                                type="number"
                                id="size-min"
                                value="{min_default_node_size}"
                                placeholder="Min"
                                min="0"
                                oninput="updateNodes()"
                            >
                            <input
                                type="number"
                                id="size-max"
                                placeholder="Max"
                                min="0"
                                oninput="updateNodes()"
                            >
                        </div>
                    </div>

                    <div class="filter-group">
                        <label for="title-select">Node Title/Class</label>
                        <select id="title-select" multiple onchange="updateNodes()">
                            <option value="all" selected>All</option>
                            {title_options}
                        </select>
                    </div>

                    <div class="filter-group">
                        <label>Edge Width ({min_width}-{max_width})</label>
                        <div class="size-inputs">
                            <input
                                type="number"
                                id="width-min"
                                value="{min_default_edge_width}"
                                placeholder="Min"
                                min="0"
                                oninput="updateNodes()"
                            >
                            <input
                                type="number"
                                id="width-max"
                                placeholder="Max"
                                min="0"
                                oninput="updateNodes()"
                            >
                        </div>
                    </div>

                    <div class="filter-group">
                        <label for="edge-color-select">Edge Color</label>
                        <select id="edge-color-select" multiple onchange="updateNodes()">
                            <option value="all" selected>All</option>
                            {edge_color_options}
                        </select>
                    </div>
                </div>
            </div>

            <div class="config-section">
                <div class="legend config-toggle" onclick="togglePanel('physics-config', event)">
                    Physics
                </div>

                <div id="physics-config" class="panel-hidden config-panel"></div>
            </div>
        </div>

        <div id="description-container">
            <div id="node-edge-count" class="legend">
                Nodes: <span id="node-count">0</span>, Edges: <span id="edge-count">0</span>
            </div>

            <div class="legend" onclick="togglePanel('description-table', event)">
                Diagram Description
            </div>

            <div id="save-button-container">
                <button id="save-selection" onclick="saveSelection()">Save Selection</button>
                {plotly_toggle_html}
            </div>
        </div>

        <div id="description-table" class="panel-hidden">
            <div id="description-popup-header">
                <span>{description_title}</span>
                <button type="button" onclick="togglePanel('description-table', event)" title="Close">✕</button>
            </div>

            <div id="description-popup-content">
                <div class="table-group">
                    <table>
                        <thead>
                            <tr>
                                {table_headers}
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>


        {drag_script}
        {script_code}
        {plotly_drag_script}
    </body>
    </html>
    """

    # ------------------------------------------------------------------
    # Write and optionally open HTML
    from pathlib import Path
    if writeHTML is None:
        writeHTML = 'network.html'

    folder_path = Path(f"{Path(__file__).parent.resolve()}/netOutPut/")
    folder_path.mkdir(parents=True, exist_ok=True)
    writeOut = f"{folder_path}/{writeHTML}"

    

    with open(writeOut, "w", encoding="utf-8") as f:
        f.write(html_code)
   
    print(f"Generated {writeOut} successfully!")
    
    if browserView:
        import webbrowser
        webbrowser.open(writeOut)
    return None

if __name__ == "__main__":

    
    gipuzkoa_path = "https://github.com/Atsaniik/digitalBusinessUEF/blob/main/img/Joensuu_logo.png"
    turku_path = "https://github.com/Atsaniik/digitalBusinessUEF/blob/main/img/Kuopio_logo.png"
    
    turku_path2 = r"C:\Users\pengyang\phd\21st TourMIS 2026_Vienna\github_dbs\img\Joensuu_logo.png"
    gipuzkoa_path2 = r"C:\Users\pengyang\phd\21st TourMIS 2026_Vienna\github_dbs\img\Kuopio_logo.png"
    
    turku_img64 = base64_from_loc(turku_path2)
    gipuzkoa_img64 = base64_from_loc(gipuzkoa_path2)

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
    visnet(nodes=nodes, edges=edges, network_title= None, browserView=True, writeHTML=None, min_default_node_size=1, min_default_edge_width=0, maximum_display=10)



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

    visnet(nodes=nodes2, edges=edges2, network_title='Large Network', browserView=True, writeHTML='test_large.html', min_default_node_size=1, min_default_edge_width=1, maximum_display=100)