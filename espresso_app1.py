import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_html_components as html
#import plotly.graph_objs as go
import plotly_express as px
import flask
import pandas as pd
import dash_auth
import sqlite3
from urllib.parse import quote
#import dash_bootstrap_components as dbc

# db
con = sqlite3.connect('data/espresso.db',check_same_thread=False)

# gunicorn test1:server -b 0.0.0.0:4000 &>log &
server = flask.Flask(__name__)

# app config
#@server.route('/assets/favicon.ico')
#def favicon():
#    return flask.send_from_directory('/data/favicon.ico')
    

app = dash.Dash(__name__, server=server, url_base_pathname='/espresso/', external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css'])
app.title = 'Espresso'
app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# landing page
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/espresso/human':
        return human
    elif pathname == '/espresso/mouse':
        return mouse
    elif pathname == '/espresso/corr':
        return corr    
    else:
        return index

# menu
#menu= '![adipocyte](/assets/adipocyte.jpg) &nbsp; [Home](/) | [Human](/human) | [Mouse](/mouse) | [Correlation](/corr)'   
menu = html.Nav([ 
html.A(href='/assets/adipocyte.jpg',className="navbar-brand"),
html.A('Espresso',href='/espresso',className="navbar-brand"),
html.A('Human',href='/espresso/human',className="nav-link" ),
html.A('Mouse',href='/espresso/mouse',className="nav-link"),
html.A('Correlation',href='/espresso/corr',className="nav-link"),
], className="navbar navbar-expand-lg navbar-light", style={"background-color": "#e3f2fd", "margin-bottom": 20 } )


# footer  
#foot0= dcc.Markdown('© 2020 Copyright [Umesh Ghoshdastider](mailto:gumesh@ethz.ch) @ [Wolfrum Lab](http://www.tnb.ethz.ch/)')

foot=html.Footer([ 
html.Label('© 2019 Copyright: ', style={"padding-right":10 }),
html.A('Umesh Ghoshdastider',href='mailto:gumesh@ethz.ch'),
], className="page-footer text-center", style={"background-color": "#e3f2fd", "padding":10 } )
   
index=html.Div([ menu, 
dcc.Markdown('''
#### RNA-seq Data Visualization

[Human gene expression](/espresso/human)

[Mouse gene expression](/espresso/mouse)

[Human gene expression correlation](/espresso/corr)

''', className="container"), foot ],   )


## CORRELATIOn

# annotation
an=pd.read_csv('data/meta2.csv',index_col=1)[['graph','name']]

# human
g=pd.read_sql('select gene from human_gene', con).gene.tolist()

# clinical data
c=pd.read_csv('data/clinical1.csv',index_col=0)
col='age	height (m)	weight (kg)	BMI (kg/m2)	waist (cm)	body fat (%)	T3 (3,3 - 6,5)	T4 (10,5 - 22,7)	TSH (0,35 - 5,1)'.split('\t')
#c=c[sorted(c.columns)]

corr = html.Div([
	menu,
	html.H4('Human gene expression correlation with clinical features', style={"padding-left": 20}),
	html.Div([

	# gene
	html.Label('Select Gene'),
	dcc.Dropdown(id='gene', options=[{'label': j, 'value': j} for j in g], value='UCP1', searchable=True ),
	
	# clinical data
	html.P(),	
	html.Label('Select Phenotype'),
	dcc.Dropdown(id='cl', options=[{'label': j, 'value': j} for j in col], searchable=True, value='BMI (kg/m2)' ),
	
	html.P(),
	html.Label('Select Fat Type'),
	dcc.RadioItems(id='ty', options=[{'label': j, 'value': j} for j in ['brown','white']], value='brown'),
	
	# 
	html.P(),
    html.Label('Gene Expression Scale'),
	dcc.RadioItems(id='scale', options=[{'label': j, 'value': j} for j in ['log2','linear']], value='log2'),
		
	# download
	html.P(),
	html.A('Download Data', id='download', download="human_rpkm.csv", href="", target="_blank"),
	html.P(),
	
	html.A('Study Description', href="https://docs.google.com/document/d/1fwv9FCBJqt6_U0EVPvDyw9kFr9kk0kEsItgve-BwUxc/edit?usp=sharing", target="_blank"),

	html.P(),
	#dcc.Markdown('Created by [Umesh Ghoshdastider](mailto:gumesh@ethz.ch)'),
	
	], style={"width": "20%", "float": "left", "padding-left": 20},),	
        
    
    # graphs
    html.Div([
    dcc.Graph(id='graph0'),

    ], style={"width": "80%", "display": "inline-block"}),
    foot,], )

# graph 1
@app.callback( [ Output('download', 'href'), Output('graph0', 'figure') ],  [Input('gene', 'value'), Input('scale', 'value'), Input('cl', 'value'), Input('ty', 'value')] )
def graph(gene,scale,cl,ty):
	
	# get data
	e=pd.read_sql("select * from human_fpkm e,human_gene g, human_sample s where e.gene_id=g.gene_id and e.sample_id=s.sample_id and g.gene='"+gene+"'", con)
	
	# extract samples
	e=e.set_index('sample').loc[c[ty]]
	e=e.join(c.set_index(ty))
	
	if scale=='log2':
		e.fpkm=pd.np.log2(e.fpkm+1)	
	
	# corr
	d=e[['fpkm',cl]].dropna()
	cor1=d.corr('pearson').iloc[0,1]
	cor2=d.corr('spearman').iloc[0,1]
	title='Pearson Corr: %.2f, Spearman Corr: %.2f'%(cor1,cor2)
	
	download = "data:text/csv," + quote(d.to_csv() )
	
	fig0 = px.scatter(d, x='fpkm', y= cl, title=title, trendline='ols', marginal_y='box', marginal_x='box',)	
	
	
	return download, fig0

## HUMAN

human = html.Div([
	menu,
	html.H4('Gene Expression in Human', style={"padding-left": 20}),
	html.Div([

	html.Label('Select Gene(s)'),
	dcc.Dropdown(id='gene', options=[{'label': j, 'value': j} for j in g], value=['UCP1','AXL'], searchable=True, multi=True ),
	
	html.P(),
    html.Label('Scale'),
	dcc.RadioItems(id='scale', options=[{'label': j, 'value': j} for j in ['log2','linear']], value='linear'),
	
	# download
	html.P(),
	html.A('Download Data', id='download1', download="human_rpkm.csv", href="", target="_blank"),
	html.P(),
	
	dcc.Markdown('[Study Description](https://docs.google.com/document/d/1fwv9FCBJqt6_U0EVPvDyw9kFr9kk0kEsItgve-BwUxc)'),

	#dcc.Markdown('Created by [Umesh Ghoshdastider](mailto:gumesh@ethz.ch)'),
	
	], style={"width": "20%", "float": "left", "padding-left": 20},),	        
    
    # graphs
    html.Div([
    dcc.Graph(id='graph1'),
    dcc.Graph(id='graph2'),
    dcc.Graph(id='graph3'),
    dcc.Graph(id='graph4'),
    dcc.Graph(id='graph5'),

    ], style={"width": "80%", "display": "inline-block"}),
    foot,], )

# 
@app.callback( [ Output('download1', 'href'), Output('graph1', 'figure'), Output('graph2', 'figure'), Output('graph3', 'figure'), Output('graph4', 'figure'), Output('graph5', 'figure') ],  [Input('gene', 'value'), Input('scale', 'value')] )
def graph(gene, scale):
	# get data
	e=pd.read_sql("select * from human_fpkm e,human_gene g, human_sample s where e.gene_id=g.gene_id and e.sample_id=s.sample_id and g.gene in ('"+ "','".join(gene) +"')", con)
	
	# add anno
	e=e.set_index('sample').join(an).reset_index()
	
	if scale=='log2':
		e.fpkm=pd.np.log2(e.fpkm+1)	
	
	download = "data:text/csv," + quote(e.to_csv() )
	fig1 = px.bar(e[e.graph==1], x='fpkm', y= 'name', color='gene', orientation='h', height=600, title='Human supraclavicular BAT & subcutaneous WAT')
	fig2 = px.bar(e[e.graph==2], x='fpkm', y= 'name', color='gene', orientation='h', height=400, title='Human hMADS cells')
	fig3 = px.bar(e[e.graph==3], x='fpkm', y= 'name', color='gene', orientation='h', height=400,title='Human periadrenal BAT')
	fig4 = px.bar(e[e.graph==4], x='fpkm', y= 'name', color='gene', orientation='h', height=400,title='Differentiated Human multipotent adipose-derived stem cells transfected with control siRNA')
	fig5 = px.bar(e[e.graph==5], x='fpkm', y= 'name', color='gene', orientation='h', height=1200,title='Human deep neck BAT & subcutaneous WAT')
	
	return download, fig1, fig2, fig3, fig4, fig5
	
## MOUSE
# human
g1=pd.read_sql('select gene from mouse_gene', con).gene.tolist()

mouse = html.Div([
	menu,
	html.H4('Gene Expression in Mouse', style={"padding-left": 20}),
	html.Div([

	html.Label('Select Gene(s)'),
	dcc.Dropdown(id='gene', options=[{'label': j, 'value': j} for j in g1], value=['Ucp1','Axl'], searchable=True, multi=True ),
	
	html.P(),
    html.Label('Scale'),
	dcc.RadioItems(id='scale', options=[{'label': j, 'value': j} for j in ['log2','linear']], value='linear',),
	
	# download
	html.P(),
	html.A('Download Data', id='download2', download="mouse_rpkm.csv", href="", target="_blank"),
	html.P(),
	
	dcc.Markdown('[Study Description](https://docs.google.com/document/d/1fwv9FCBJqt6_U0EVPvDyw9kFr9kk0kEsItgve-BwUxc)'),

	#dcc.Markdown('Created by [Umesh Ghoshdastider](mailto:gumesh@ethz.ch)'),
	
	], style={"width": "20%", "float": "left", "padding-left": 20},),	        
    
    # graphs
    html.Div([
    dcc.Graph(id='graph6'),
    dcc.Graph(id='graph7'),
    dcc.Graph(id='graph8'),
    dcc.Graph(id='graph9'),
    dcc.Graph(id='graph10'),
    dcc.Graph(id='graph11'),
    dcc.Graph(id='graph12'),
    
    ], style={"width": "80%", "display": "inline-block"}),
foot], )

# graph 1
@app.callback( [ Output('download2', 'href'), Output('graph6', 'figure'), Output('graph7', 'figure'), Output('graph8', 'figure'), Output('graph9', 'figure'), Output('graph10', 'figure') , Output('graph11', 'figure'), Output('graph12', 'figure') ],  [Input('gene', 'value'), Input('scale', 'value')] )
def graph(gene, scale):
	# get data
	e=pd.read_sql("select * from mouse_fpkm e,mouse_gene g, mouse_sample s where e.gene_id=g.gene_id and e.sample_id=s.sample_id and g.gene in ('"+ "','".join(gene) +"')", con)
	
	# add anno
	e=e.set_index('sample').join(an).reset_index()
	
	if scale=='log2':
		e.fpkm=pd.np.log2(e.fpkm+1)	
	
	download = "data:text/csv," + quote(e.to_csv() )
	fig6 = px.bar(e[e.graph==6], x='fpkm', y= 'name', color='gene', orientation='h', height=600, title='BAT Paternal Cold Exposure')
	fig7 = px.bar(e[e.graph==7], x='fpkm', y= 'name', color='gene', orientation='h', height=400, title='Young vs old BAT')
	fig8 = px.bar(e[e.graph==8], x='fpkm', y= 'name', color='gene', orientation='h', height=400,title='VIS GFP')
	fig9 = px.bar(e[e.graph==9], x='fpkm', y= 'name', color='gene', orientation='h', height=800,title='Thermoneutrality of BAT and iWAT at 22C and 30C')
	fig10 = px.bar(e[e.graph==10], x='fpkm', y= 'name', color='gene', orientation='h', height=800,title='BAT Paternal Cold Exposure (more samples)')
	fig11 = px.bar(e[e.graph==11], x='fpkm', y= 'name', color='gene', orientation='h', height=400,title='Differentiated immortalized mouse brown pre-adipocytes transfected with CEBPg siRNA')
	fig12 = px.bar(e[e.graph==12], x='fpkm', y= 'name', color='gene', orientation='h', height=800,title='Differentiated immortalized mouse brown pre-adipocytes transfected with CEBPg siRNA')
	
	return download, fig6, fig7, fig8, fig9, fig10, fig11, fig12

if __name__ == '__main__':
    app.run_server(debug=True)
#    app.run_server()
