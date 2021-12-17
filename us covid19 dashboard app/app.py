import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import datetime
import plotly.express as px

#for graph 2
from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)


app = dash.Dash(__name__)


covid_df = pd.read_csv("vax_us_county.csv",
                      usecols = ['Date',"FIPS",'Recip_County', 'Recip_State','Administered_Dose1_Pop_Pct', 'Series_Complete_Pop_Pct'], parse_dates = ["Date"])


us_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI',
       'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI',
       'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC',
       'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT',
       'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
covid_df = covid_df[covid_df.Recip_State.isin(us_states)]



#stripping datetime value to numbers format
covid_df['dates'] = covid_df['Date'].apply(lambda x: int(x.strftime("%Y%m%d")))
#sort dates before mapping
covid_df.sort_values(by = 'dates', ascending = True, inplace = True)

#create dictionary for mapping, unique dates for numbers
mapping = {item:i for i, item in enumerate(covid_df["dates"].unique())}
#map dates to numbers in a new column
covid_df["numbers"] = covid_df["dates"].apply(lambda x: mapping[x])


#state df to map state to state code for df3
state_abbrev = pd.read_csv("state_abbrev")
state_dict = dict(zip(state_abbrev.State, state_abbrev.Code))


covid_df3 = pd.read_csv("us_county_trans.csv",
                       usecols = ['state_name', 'county_name' ,'report_date', 'cases_per_100K_7_day_count_change','percent_test_results_reported_positive_last_7_days'],
                       na_values = "suppressed")

#make new column for state codes
covid_df3['code'] = covid_df3.state_name.map(state_dict)
#filter out non-states
covid_df3 = covid_df3[covid_df3.code.isin(us_states)]
covid_df3.dropna(inplace = True)
#dict to map state and county
dropdowndict = covid_df3.groupby('code')['county_name'].apply(list).to_dict()

#convert dates
covid_df3['dates'] = pd.to_datetime(covid_df3.report_date, format ='%Y/%m/%d')
covid_df3.sort_values(by = 'dates', inplace = True)


#####THE APP####
app.layout = html.Div([


    html.H1(
        children='Final Project - STAT430',
        style={
            'textAlign': 'center',
        }
    ),

    #start of graph 1
    dcc.RadioItems(
        id = 'dose',
        options = [
        {'label': 'Fully Vaccinated', 'value':"Series_Complete_Pop_Pct"},
        {'label': 'One Dose', 'value':"Administered_Dose1_Pop_Pct"}],
        value = 'Series_Complete_Pop_Pct'),


    dcc.Graph(id='graph'),

    dcc.Slider(
        id = 'date_slider',
        min=covid_df['numbers'].min(), #the first date
        max=covid_df['numbers'].max(), #the last date
        value=covid_df['numbers'].min(), #default: the first
        step = 1,
        tooltip={"placement": "bottom", "always_visible": True}
        ),
    #END OF GRAPH 1



    #start of graph2
    html.Div([
        dcc.Dropdown(
            id='state_dropdown',
            options = [{'label':state, 'value':state} for state in dropdowndict.keys()],
            value = 'IL'
            ),

        dcc.RadioItems(
        id = 'vaccination_radio2',
        options = [
        {'label': 'Fully Vaccinated', 'value':"Series_Complete_Pop_Pct"},
        {'label': 'One Dose', 'value':"Administered_Dose1_Pop_Pct"}],
        value = 'Series_Complete_Pop_Pct'),

        dcc.Graph(id='graph2'),

        dcc.Slider(
        id = 'date_slider2',
        min=covid_df['numbers'].min(), #the first date
        max=covid_df['numbers'].max(), #the last date
        value=covid_df['numbers'].min(), #default: the first
        step = 1,
        tooltip={"placement": "bottom", "always_visible": True}
        ),
        ]),

        #start of graph 3
    html.Div([
        dcc.Dropdown(
            id = 'county_dropdown',
            value = 'Champaign County'
            ),

        dcc.Graph(id = 'graph3')

        ]),

    #graph4

    html.Div([


        dcc.Graph(id = 'graph4')


        ])
    
])


#callback for graph 1
@app.callback(
    Output('graph', 'figure'),
    Input('dose', 'value'),
    Input('date_slider', 'value'))

#update figure 1 
def update_figure1(vax_stat, date_slider):

    #filter by date
    filtered = covid_df[covid_df.numbers == date_slider]


    one_group = filtered.groupby("Recip_State")['Administered_Dose1_Pop_Pct'].agg('mean').reset_index()
    full_group = filtered.groupby("Recip_State")['Series_Complete_Pop_Pct'].agg('mean').reset_index()


    if vax_stat == "Series_Complete_Pop_Pct":
        fig = go.Figure(data=go.Choropleth(
            locations=full_group['Recip_State'], # Spatial coordinates
            z = full_group['Series_Complete_Pop_Pct'].astype(float), # Data to be color-coded
            locationmode = 'USA-states', # set of locations match entries in `locations`
            colorscale = 'Greens',
            colorbar_title = "Percentage of Vaccinations (%)",
        ))

        fig.update_layout(
            title_text = 'Covid Vaccinations Percentage by State',
            geo_scope='usa', # limite map scope to USA
        )
    else:
        fig = go.Figure(data=go.Choropleth(
            locations=one_group['Recip_State'], # Spatial coordinates
            z = one_group['Administered_Dose1_Pop_Pct'].astype(float), # Data to be color-coded
            locationmode = 'USA-states', # set of locations match entries in `locations`
            colorscale = 'Greens',
            colorbar_title = "Percentage of Vaccinations (%)",
        ))

        fig.update_layout(
            title_text = 'Covid Vaccinations Percentage by County',
            geo_scope='usa', # limite map scope to USA
        )

    return fig


#callback for graph 2
@app.callback(
    Output('graph2', 'figure'),
    Input('vaccination_radio2', 'value'),
    Input('state_dropdown', 'value'),
    Input('date_slider2', 'value')
    )


#update map depending on inputs
def update_figure2(vaccination_radio2, state_dropdown, date_slider2):

    #filter by state and county
    filter_two = covid_df[(covid_df.Recip_State == state_dropdown) & (covid_df.numbers == date_slider2)]

    if vaccination_radio2 == 'Series_Complete_Pop_Pct':
        fig2 = px.choropleth(filter_two, geojson = counties, locations = 'FIPS', color = 'Series_Complete_Pop_Pct', color_continuous_scale="Plotly3", range_color = (0,100), scope = 'usa',
            labels={'Series_Complete_Pop_Pct': "Percentage of Vaccinations (%)"})
        fig2.update_layout(
                title_text = 'Covid Vaccinations Percentage by State',
                )
        fig2.update_geos(fitbounds="locations", visible=False)

    else: 
        fig2 = px.choropleth(filter_two, geojson = counties, locations = 'FIPS', color = 'Administered_Dose1_Pop_Pct', color_continuous_scale="Plotly3", range_color = (0,100), scope = 'usa',
            labels={'Administered_Dose1_Pop_Pct': "Percentage of Vaccinations (%)"})
    
        fig2.update_layout(
                title_text = 'Covid Vaccinations Percentage by County',
                )
        fig2.update_geos(fitbounds="locations", visible=False)

    return fig2



#change county depending on state
@app.callback(
    dash.dependencies.Output('county_dropdown', 'options'),
    [dash.dependencies.Input('state_dropdown', 'value')]
)

#function to update county output depending on state input
def update_date_dropdown(name):
    return [{'label': i, 'value': i} for i in dropdowndict[name]]


#callback for graph3
@app.callback(
    Output('graph3', 'figure'),
    Input('state_dropdown', 'value'),
    Input('county_dropdown', 'value'))

#function for graph3

def update_figure3(state_dropdown, county_dropdown):
    filtered = covid_df3[(covid_df3.code == state_dropdown) & (covid_df3.county_name == county_dropdown)]

    fig3 = px.line(filtered, x='dates', y='percent_test_results_reported_positive_last_7_days', title='7 Day Moving Averages')

    fig3.update_xaxes(rangeslider_visible=True)
    return fig3



#callback for graph4
@app.callback(
    Output('graph4', 'figure'),
    Input('state_dropdown', 'value'),
    Input('county_dropdown', 'value'))

def update_figure4(state_dropdown, county_dropdown):
    filtered = covid_df3[(covid_df3.code == state_dropdown) & (covid_df3.county_name == county_dropdown)]

    fig4 = px.line(filtered, x='dates', y='cases_per_100K_7_day_count_change', title='7 Day Moving Averages - Daily Cases')

    fig4.update_xaxes(rangeslider_visible=True)
    return fig4


if __name__ == '__main__':
    app.run_server(debug=True)
