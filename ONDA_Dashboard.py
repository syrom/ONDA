#!/usr/bin/env python
# coding: utf-8

# # ONDA: Organisational Network Discovery & Analysis

# # 0) Versioning

# # 1) Package Import

# In[1]:


from jupyter_dash import JupyterDash
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


# In[2]:


import networkx as nx
import plotly.graph_objs as go
import pandas as pd
from colour import Color


# # 2) Variable declartations (global)

# In[3]:


new_line = '\n'


# # 3) Definitions

# ## 3a) Class definitions

# In[ ]:





# ## 3b) Function Definitions

# In[4]:


def f_define_plot(nodes_data, edges_data, cl_node_description, cl_node_org, cl_node_type):
## Step1: Filter data frame down to the desired data (aka nodes)

    # BEFORE FIRST QUERY !!!! Otherwise problem thru C and P values in Orga-field, filtering out these nodes
    # as prepartation for check in loop, further extend list with all nodes in the aux_set1 which have node_org that is NOT in the criterium list
    cl_node_org_extended = cl_node_org + ['C', 'P'] # Criterium List must be extended by acronyms for comptence and project as they CAN potentially be
                                                    # included in the node_type criterium list and would erroneously be filtered out again here
    # add 'H' (Hierarchy) in any case to the list of selected node types; otherwise, pure setting to Project or Competence do not trace back
    # to the individuals represented in the H-entries
    if 'H' not in cl_node_type:
        cl_node_type.append('H')    
    # define query string
    s_query = 'NODE_TYPE in @cl_node_type and NODE_DESC in @cl_node_description and NODE_ORG in @cl_node_org_extended'
    df_nodes_filtered = df_nodes.query(s_query)

    l_nodes_aux1 = df_nodes_filtered.NODES.to_list()

    # Creating a set of edges where either SOURCE or TARGET node is equal to filtered nodes:
    # CAUTION: This set can still contain nodes that GO BEYOND THE FILTER CRITERIA  defined in the node types list
    # as ANY edge leading to one of the filtered nodes qualifies a non-filtered node to enter the set
    aux_set1 = set()
    for index in range(0,len(df_edges)):
        if (df_edges['SOURCE'][index] in l_nodes_aux1 or df_edges['TARGET'][index] in l_nodes_aux1):
            aux_set1.add(df_edges['SOURCE'][index])
            aux_set1.add(df_edges['TARGET'][index])

    # Determine which edges and nodes qualifiy to be represented in the graph according to the settings.
    # Cleaning the set from all nodes that have a node type or belong to an organisation other than those defined in the node type and node orga filter list:
    # as prepartation for check in loop, further extend list with all nodes in the aux_set1 which have node_org that is NOT in the criterium list
    # create a list with all nodes in the aux_set1 which have node class or ORG that is NOT in the criterium list
    l_aux = []
    for i in aux_set1:
        if df_nodes.query('NODES == @i').empty:
            continue
        else:
            if df_nodes.query('NODES == @i').iloc[0].NODE_DESC not in cl_node_description:
                l_aux.append(i)
            if df_nodes.query('NODES == @i').iloc[0].NODE_ORG not in cl_node_org_extended:
                l_aux.append(i)

    # cycle thru the list and remove these "unqualified" nodes from the set
    for i in l_aux:
        aux_set1.remove(i)
    aux_set1 # Now only contains nodes as definded by the filter criterium lists

    # define a dfs with all edges and nodes that are to be visualized
    # The difference vs. the "filtered" list is that this df also contains nodes that the filtered nodes connect to but which, otherwise, correspond
    # to the filter criteria
    # edges are more complicated, as they may contain unwanted elements, either as SOURCE or TARGET
    df_edges_graph =df_edges[(df_edges.SOURCE.isin(aux_set1) | df_edges.TARGET.isin(aux_set1)) & df_edges.TYPE.isin(cl_node_type)]
    aux_set_source = {nodes for nodes in df_edges_graph.SOURCE}
    aux_set_target = {nodes for nodes in df_edges_graph.TARGET}
    # combinining the two sets, containing all nodes that were in the filtered df_edge_graph
    aux_set2 = aux_set_source | aux_set_target

    # create the difference between the two sets: result shows again potentially "undesirable" nodes
    aux_set3 = aux_set2 - aux_set1

    # finally, we must differentiate: nodes on the H-Level should be included (showing persons that other persons corresponding to 
    # the filter criterium are connected to. Those, we do want to see - but not Projects or Competences that are not explicitly
    # mentioned in the filter criteria
    # Determining which nodes from aux_set3 are NOT Hierarchy elements:
    l_aux = []
    for i in aux_set3:
        if df_nodes.query('NODES == @i').empty:
            continue
        else:
            if df_nodes.query('NODES == @i').iloc[0].NODE_TYPE == 'H':
                l_aux.append(i)
    # cycle thru the list and remove these "unqualified" nodes from the set
    for i in l_aux:
        aux_set3.remove(i) 

    # using aux_set3 now to remove any row from the edges-df which contains the undesirable nodes, either as Source or as Target
    df_edges_graph = df_edges_graph[~df_edges_graph.SOURCE.isin(aux_set3)]
    df_edges_graph = df_edges_graph[~df_edges_graph.TARGET.isin(aux_set3)]

    # now for the df for all nodes that should appear in the graph:
    # As we have treated H and P/C-nodes differently if they have entered as source or target of one of the selected nodes,
    # we also must update the set used to filter the node-df: aux_set2 may contain more H-nodes, e.g. additional sources or targets.
    aux_set4 = aux_set2 - aux_set3
    df_nodes_graph = df_nodes[df_nodes.NODES.isin(aux_set4)]
    

## Step 2: Building Network using NetworkX
    # The network (G-object) is initially build with the FILTERED edge and node information  

    #############################################################################################################________________________________
    G = nx.from_pandas_edgelist(df_edges_graph, 'SOURCE', 'TARGET', ['SOURCE','TARGET', 'VALUE', 'TYPE', 'DPMT'], create_using=nx.MultiDiGraph())
    #############################################################################################################________________________________

    # Workaround to the indexing problem with the NODES-column: copy the NODES name information to a column with a new name, allowing to serve the 
    # original column as index
    df_nodes_graph['aux_name'] = df_nodes_graph['NODES']

    # setting several node attributes (to be used as hovertext-info when hovering the mouse over the node in the graph)
    nx.set_node_attributes(G, df_nodes_graph.set_index('NODES')['aux_name'].to_dict(), 'NODE_NAME')
    nx.set_node_attributes(G, df_nodes_graph.set_index('NODES')['NODE_TYPE'].to_dict(), 'NODE_TYPE')
    nx.set_node_attributes(G, df_nodes_graph.set_index('NODES')['NODE_DESC'].to_dict(), 'NODE_DESC')
    nx.set_node_attributes(G, df_nodes_graph.set_index('NODES')['NODE_ORG'].to_dict(), 'NODE_ORG')

    # Determine 'look' of the graph
    ################################
    pos = nx.layout.spring_layout(G)
    ################################

    # feed positioning info derived from the layout-method to the graph nodes
    for node in G.nodes:
        G.nodes[node]['pos'] = list(pos[node])

## Step3: Define "trace" of nodes for the plotly object
    traceRecode = []

    ### Setting up the the basic structure of the Scatter object
    ### The initially empty lists from the initialization will be successively filled !!!
    node_trace = go.Scatter(x=[], y=[], hovertext=[], text=[], mode='markers+text', textposition="middle center",
        hoverinfo="text", marker={'size': 30})   
    #    hoverinfo="text", marker={'size': 50, 'color': 'LightSkyBlue'})                                            # further room to experiment with network look

    index = 0
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        hovertext = "NODE_NAME: " + str(G.nodes[node]['NODE_NAME']) + "<br>" + "NODE_DESC: " + str(G.nodes[node]['NODE_DESC']
            ) + "<br>" + "NODE_TYPE: " + str(G.nodes[node]['NODE_TYPE']) + "<br>" + "NODE_ORG: " + str(G.nodes[node]['NODE_ORG'])
        text = G.nodes[node]['NODE_NAME']
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['hovertext'] += tuple([hovertext])
        node_trace['text'] += tuple([text])
        index = index + 1
    ### appending color info for nodes
    ### Probably 10.000 ways to do this more intelligently, e.g. via
    ### a) integrating this step in the loop above or
    ### b) using a predefined dictionary to map colors (with "red" as default value)
    l_node_color = []
    for node in G.nodes():
        if G.nodes[node]['NODE_TYPE'] == "H":
            node_color = "grey"
        elif G.nodes[node]['NODE_TYPE'] == "P":
            node_color = "blue"
        elif G.nodes[node]['NODE_TYPE'] == "C":
            node_color = "green"
        else:
            node_color = "red"
        l_node_color.append(node_color)
    node_trace.marker.color = l_node_color

    traceRecode.append(node_trace)

## Step 4: Define "trace" of edges for the plotly object
    colors = ['black']
    index = 0
    for edge in G.edges:
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        weight = float(G.edges[edge]['VALUE'])    # Could also be e.g. "LEVEL"
        trace = go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
                           mode='lines',
                           line={'width': weight},
                           marker=dict(color=colors),
                           line_shape='spline',
                           opacity=1)
        traceRecode.append(trace)
        index = index + 1

## Step5: Define layout for Plotly graph
    figure = go.Figure(
        data = traceRecode,
        layout = go.Layout(showlegend=False, hovermode='closest',
                    margin={'b': 4, 'l': 4, 'r': 4, 't': 4},
                    xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                    yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                    height=800,
                    clickmode='event+select'
                    ))
    return figure


# # 4) Actual Program

# ## 4a) Data Import

# In[5]:


#df_nodes = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')
df_nodes = pd.read_csv(r'nodes.csv', sep=';')
df_edges = pd.read_csv(r'edges.csv', sep=';')


# ## 4b) Instantiate initial values for the graph settings

# In[6]:


l_initial_node_type = ['H']

l_initial_node_desc = ['H_GA']

l_initial_org = df_nodes['NODE_ORG'].unique().tolist()
l_initial_org.remove('C')   # Competences must be removed from ORG list
l_initial_org.remove('P')   # Projects must be removed from ORG list
# C and P could cause confusion; they are added back in the filtering for the graph, as these nodes (and edges eminating from them)
# are independent from the ORG unit. Or, in other word: Projects and Competences are independent of any ORG units
#l_initial_org


# ## 4c) Building the dashboard layout

# In[7]:


# app = JupyterDash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app = JupyterDash(__name__, external_stylesheets=[dbc.themes.LUX])  # easy to change overall look - just try out other themes


# In[8]:


body = html.Div([
   html.H1("ONDA: Organisational Network Discovery and Analysis")
       
   , dbc.Row([dbc.Col(html.Div([dbc.Label("Displayed the following Node Types"),dbc.Checklist(options=[{"label": "Hierarchy", "value": "H" },
    {"label": "Projects", "value": "P"},{"label": "Competences", "value": "C"}], value=["H"], id="f_select_node_type", inline=True, switch=True,),]),width=4)
   , dbc.Col(html.Div([dbc.Label("Display the Nodes for the following organizational units: "),
                       dcc.Dropdown(options=[{'label': i, 'value': i} for i in l_initial_org], value = l_initial_org,
                                    id = 'f_select_org',multi=True)]), width=4)])

   , dbc.Row(dbc.Col(html.Div(dbc.Progress(value=100, color="info"))))  # Progress bar "perverted" to horizontal divider / ruler
       
   , dbc.Row(dbc.Col(html.Div([dbc.Label("Display the following Node Classes"),
                       dcc.Dropdown(options=[{'label': i, 'value': i} for i in l_initial_node_desc], placeholder = 'Select from the Node Classes (options depending on selected Node Type(s)', value = l_initial_node_desc,
                                    id = 'f_select_node_class',multi=True)])))    

   , dbc.Row(dbc.Col(html.Div(dbc.Progress(value=100, color="info"))))  # Progress bar "perverted" to horizontal divider / ruler

   ####################################################################################################################################### graph component
   , dbc.Row(dbc.Col(html.Div(dcc.Graph(id="ONDA", figure=f_define_plot(df_nodes, df_edges, l_initial_node_type, l_initial_node_desc, l_initial_org)))))
   #######################################################################################################################################
   ])


# ## 4d) define the callback functions for the interactive graph input components

# In[9]:


# actually productive code: pushing the change in the network_type selection to trigger
# a corresponding change in the targets selection (only targets shown which have belong to the chosen network type(s)
@app.callback(
    dash.dependencies.Output(component_id='f_select_node_class', component_property='options'),        # component_property changed from "children"
    [dash.dependencies.Input(component_id='f_select_node_type', component_property='value')])
def update_node_classes(f_select_node_type):
    current_node_type = f_select_node_type
    df_aux = df_nodes[df_nodes.NODE_TYPE.isin(current_node_type)]
    return [{'label': i, 'value': i} for i in df_aux.NODE_DESC.unique()]


# In[10]:


###################################callback for actual graph update
@app.callback(
    dash.dependencies.Output('ONDA', 'figure'),
    [dash.dependencies.Input('f_select_node_class', 'value'), dash.dependencies.Input('f_select_org', 'value')])

def update_output (f_class, f_org):
#    nodes_data = df_nodes
#    edges_data = df_edges
    cl_node_description = f_class
    cl_node_org = f_org
    ################## node-types to be displayed not dynamically updated from selector switch, but derived from the current node-class selection !
    aux_set2 = set()
    for node_class in cl_node_description:
        if df_nodes.query('NODE_DESC == @node_class').empty:
            continue
        else:
            aux_set2.add(df_nodes.query('NODE_DESC == @node_class').iloc[0].NODE_TYPE)
    cl_node_type = list(aux_set2)
    ##################
    return f_define_plot(df_nodes, df_edges, cl_node_description, cl_node_org, cl_node_type)


# ## 4e) Run the dashboard

# In[11]:


app.layout = html.Div([body])


# In[12]:


# app.run_server(debug = True)
app.run_server(mode="jupyterlab", debug = True)
# if __name__ == "__main__":
#    app.run_server(debug = True)


# In[14]:


# Line to terminate DASH-dashboard in tab:
# app._terminate_server_for_port("localhost", 8050) 


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




