
from base_modes.network_visual_save_base import *
from base_modes.netmap_base import *


def remove_duplicate_dicts(dict_list):
    """Remove duplicate dictionaries (deep equality) while preserving order."""
    seen = set()
    unique_list = []
    for d in dict_list:
        # Convert dict (with nested objects) to a JSON string so it's hashable
        key = json.dumps(d, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique_list.append(d)
    return unique_list




    

def visNET(nodes,edges,network_title='Atsaniik Network', browserView=True, writeHTML='atsaniik_newtork.html', description_df=None, description_title='Peng Atsaniik', min_default_node_size=1, min_default_edge_width=0, maximum_display=20):
    
    """ visualize your network with a save button to export selected nodes and edges to JSON files
    Args:
        nodes(Dataframe or List of dict): list of nodes dict e.g. {"id": 1, "label": "Start", "size": 30, "color": "red-spain", "shape": "dot-america", "title": "starting the point"}
        if the shape is image should be converted to base64 through base64_from_loc(image_local_address) or base64_from_url(image_url)
        edges(Dataframe or List of dict): list of edges dict e.g. {"from": 1, "to": 3, "width": 4, "color": {"color": "#C70039-europe"}, "arrows": "to", "title": "from 1 to 3"}
        description_df(dataframe): a dataframe with columns "Name", "Description"
        description_title(str): describe your network in short
        writeHTML(str): output HTML file name
        browserView(bool): whether to open the HTML in a browser
        min_default_node_size(float): minimum node size for initial display
        min_default_edge_width(float): minimum edge width for initial display
        maximum_display(int): maximum number of nodes to display at any time
    """
    
    
            
        
        
    if isinstance(nodes, pd.DataFrame) and isinstance(edges, pd.DataFrame):
        
        # Function to remove keys with NaN values
        def clean_dict(d):
            return {k: v for k, v in d.items() if not (isinstance(v, float) and pd.isna(v))}

        # Convert back to list of dicts and remove NaN key-value pairs
        nodes = [clean_dict(row) for row in nodes.to_dict(orient="records")]
        
        edges = [clean_dict(row) for row in edges.to_dict(orient="records")]
    


    elif (isinstance(nodes, list) and all(isinstance(i, dict) for i in nodes)
        and isinstance(edges, list) and all(isinstance(i, dict) for i in edges)):
        nodes = nodes
        edges = edges
        

    else:
        print("Nodes and Edges Should be either dataframe or list of dicts in the recommended format") 


    


    nodeIDchecks = []
    for node in nodes:
        nodeIDcheck = node['id']
        nodeIDchecks.append(nodeIDcheck)
    missingNodes = []      
    for edge in edges:
        edgeIDcheck = [edge['from'], edge['to']]
        missingNode = [{"id": x} for x in edgeIDcheck if x not in nodeIDchecks]
        if len(missingNode)>0:
            print(f'edge {edge['from']}-{edge['to']} missing nodes description:  {missingNode}')
        missingNodes.extend(missingNode)
    
    nodes_list1 = nodes + missingNodes

    nodes_list1 = remove_duplicate_dicts(nodes_list1)
    nodes_list1

    visnet(nodes_list1, edges, network_title=network_title,description_df=description_df, description_title=description_title, browserView= browserView, writeHTML=writeHTML, min_default_node_size= min_default_node_size, min_default_edge_width=min_default_edge_width, maximum_display=maximum_display)

def mapNET(nodes,edges, title="net map", output_html_file='simple.html', maximum_nodes=2):
        """
        nodes (dataframe or list of dicts):  {
            "node": "New York", "lat": 40.7128, "lon": -74.0060, "size": 15,
            "color": "red", "shape": "circle", "node_hover": "The Big Apple, USA"
        }, # shape: circle, triangle, square, star
        edges (dataframe or list of dicts):  {
            "node1": "New York", "node2": "Paris", "color": "darkblue", "width": 2,
            "style": "dashed", "arrow": False, "curve": True,
            "edge_hover": any text e.g. "Transatlantic flight"
            "default_size": node size 5
        },
        maximum_nodes: maximum nodes to display initially
        """
        
                    
        
        
        if isinstance(nodes, pd.DataFrame) and isinstance(edges, pd.DataFrame):
            
            # Function to remove keys with NaN values
            def clean_dict(d):
                return {k: v for k, v in d.items() if not (isinstance(v, float) and pd.isna(v))}

            # Convert back to list of dicts and remove NaN key-value pairs
            nodes = [clean_dict(row) for row in nodes.to_dict(orient="records")]
            
            edges = [clean_dict(row) for row in edges.to_dict(orient="records")]
        


        elif (isinstance(nodes, list) and all(isinstance(i, dict) for i in nodes)
            and isinstance(edges, list) and all(isinstance(i, dict) for i in edges)):
            nodes = nodes
            edges = edges
            

        else:
            print("Nodes and Edges Should be either dataframe or list of dicts in the recommended format") 
    
    
        
        netmap(nodes, edges, title=title, output_html_file=output_html_file, maximum_nodes=maximum_nodes)
        
        
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
    visNET(nodes, edges, network_title='small Network', browserView=True, writeHTML='test_small.html', min_default_node_size=1, min_default_edge_width=0, maximum_display=10)


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

    mapNET(cities, connections, title="net map", output_html_file='simple.html', maximum_nodes=2)