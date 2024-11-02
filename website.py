
import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
from datetime import datetime, timedelta
import googlemaps

import dotenv

import plotly.express as px
import plotly.graph_objects as go

import plotly.io as pio
pio.renderers.default = 'browser'

pio.renderers.default = 'browser'

st.set_page_config(layout="wide")
#st.set_option('deprecation.showPyplotGlobalUse', False)

#def long_running_function(param1, param2):
#    return

def page1():

    df = pd.read_csv('person_projec_dataframe.csv')

    st.header("Hourly Weather Forecast Tool")

    selected_city = st.selectbox("Select a city", df['city_ascii, state_id'].unique())
    st.write("Selected City:", selected_city)

    selected_row = df[df['city_ascii, state_id'] == selected_city].iloc[0]
            
    # Initializes lat and lon of selected wind farm through CSV
    selected_lat = selected_row['lat']

    selected_lon = selected_row['lng']
    
    def weather_alerts(selected_lat, selected_lon):

        r = requests.get('https://httpbin.org/user-agent')
        useragent = json.loads(r.text)['user-agent']
        headers = {'User-agent': useragent}

        # Get URL for weather alerts

        url = f'''https://api.weather.gov/alerts/active?status=actual&message_type=alert&point={selected_lat}%2C{selected_lon}&urgency=Immediate,Expected,Future&severity=Extreme,Severe,Moderate,Minor&certainty=Observed,Likely,Possible&limit=50'''

        r = requests.get(url, headers = headers)
        myjson = json.loads(r.text) 

        df_alerts = pd.json_normalize(myjson['features'])
        
        def make_button(df_alerts, i):
            df_sel = df_alerts.loc[i]

            event = df_sel['properties.event']
            description = df_sel['properties.description']

            #st.button(df_sel['properties.event'], key = i, type="primary")

            if st.button(event, key=f'button_{i}'):
                st.write(description)
                
        if len(df_alerts) == 0:
            st.write(':green[**NO WEATHER ALERTS**]')

        else:
            st.write(':red[**WEATHER ALERTS**]')
            alerts_len = len(df_alerts)

            for i in range(alerts_len):

                make_button(df_alerts, i)
  
    weather_alerts(selected_lat, selected_lon)      

    options = st.multiselect('Select variables to plot:', ['Temperature','Prob. of Precipitation', 'Wind Speed', 
    'Sky Cover', 'Heat Index', 'Visibility', 'Wind Gust'], default = ['Temperature','Prob. of Precipitation', 'Wind Speed', 
                        'Sky Cover'])
        
    def weather_forecast(selected_lat, selected_lon, options):
        
        def get_data(selected_lat, selected_lon):
            
            r = requests.get('https://httpbin.org/user-agent')
            useragent = json.loads(r.text)['user-agent']
            headers = {'User-agent': useragent}

            # Get URL for hourly forecast data and hourly grid data

            url = f"https://api.weather.gov/points/{selected_lat},{selected_lon}"
            r = requests.get(url, headers = headers)

            myjson = json.loads(r.text)
            df_url_info = pd.json_normalize(myjson['properties'])

            hourlyURL = df_url_info['forecastHourly'].iloc[0]   
            hourlyURL_grid = df_url_info['forecastGridData'].iloc[0] 

            # Obtain actual hourly forecast data

            r = requests.get(hourlyURL, headers = headers)
            r_g = requests.get(hourlyURL_grid, headers = headers)


            myjson = json.loads(r.text)
            myjson_g = json.loads(r_g.text)

            df1 = pd.json_normalize(myjson['properties']['periods'])

            return df1, myjson_g
        
        df, myjson_g = get_data(selected_lat, selected_lon)

        # Obtain grid hourly data for sky cover, heat index, etc. 

        def make_hourly_plot(title, yaxis, var_to_plot, color):

            fig = go.Figure()

            fig.update_layout(title = f'<b> {title} Forecast <b> ', 
                        title_font_size= 20, xaxis_title = 'Date', 
                        yaxis_title = f'{yaxis}', title_font_color = 'black',
                        title_font_weight = "bold")
            fig.update_layout(height=350, width = 1100, legend=dict(font=dict(size= 20)))
            fig.update_layout(xaxis = dict(title_font = dict(size=16), tickfont = dict(size=14)))
            fig.update_layout(yaxis = dict(title_font = dict(size=16), tickfont = dict(size=14)))
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='grey')
            fig.update_xaxes(showgrid = True, gridcolor='grey', griddash='dash', minor_griddash="dot") 
            fig.update_layout(plot_bgcolor='white') 

            fig.add_trace(go.Scatter(x=df['startTime'], y=var_to_plot,
                                line=dict(color=color, width=4)))

            st.plotly_chart(fig)

        make_hourly_plot('Temperature','Temperature (F)',df['temperature'],'red' )
        make_hourly_plot('Probability of Precipitation','%',df['probabilityOfPrecipitation.value'],'green' )
        make_hourly_plot('Wind Speed','Wind Speed (mph)',df['windSpeed'],'black' )

        def norm_g_data(myjson_g):
        
            df0 = pd.json_normalize(myjson_g['properties']['skyCover']['values'])
            df1 = pd.json_normalize(myjson_g['properties']['windGust']['values'])
            df2 = pd.json_normalize(myjson_g['properties']['snowfallAmount']['values'])
            df3 = pd.json_normalize(myjson_g['properties']['heatIndex']['values'])
            df4 = pd.json_normalize(myjson_g['properties']['windChill']['values'])

            def convert_time(var_name):

                var_name['validTime'] = var_name['validTime'].str.extract(r'^(.*?)/')
                var_name['validTime'] = pd.to_datetime(var_name['validTime'])
                return var_name

            df_skycover = convert_time(df0)
            df_windgust = convert_time(df1)
            df_snowfall = convert_time(df2)
            df_heat_index = convert_time(df3)
            df_heat_index['value'] = (df_heat_index['value'] * 9/5) + 32
            df_wind_chill = convert_time(df4)
        
            return df_skycover, df_windgust, df_snowfall, df_heat_index, df_wind_chill
        
        df_skycover, df_windgust, df_snowfall, df_heat_index, df_wind_chill = norm_g_data(myjson_g)

        if 'Sky Cover' in options:
            make_hourly_plot('Skycover', 'Skycover %', df_skycover['value'], 'blue')
        if 'Wind Gust' in options:
            make_hourly_plot('Wind Gust', 'Wind Gust (mph)', df_windgust['value'], 'purple')
        if 'Heat Index' in options:
            make_hourly_plot('Heat Index', 'Temperature (F)', df_heat_index['value'], 'red')
            
    weather_forecast(selected_lat, selected_lon, options)

def phone():

    df = pd.read_csv('person_projec_dataframe.csv')

    st.header("Hourly Route Planning Weather Forecast Tool")

    def menu_selection():

        with st.form("Route Weather Planner"):
            st.write("Route Weather Planner")
            selected_city = st.selectbox("Select a starting point", df['city_ascii, state_id'].unique())
            st.write("Selected City:", selected_city)

            selected_city1 = st.selectbox("Select destination", df['city_ascii, state_id'].unique())
            st.write("Selected City:", selected_city1)

            # date selection 
            today = datetime.now()
            simplified_today = today.replace(minute=0, second=0, microsecond=0)

            times = []

            for i in range(1,24):
                t = simplified_today + timedelta(hours=i)
                t_mod = t.strftime("%Y-%m-%d %I %p")
                times.append(t_mod)

            date_select = st.selectbox("Select a departure time", times)
            st.write("Selected Departure Time:", date_select)

            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")

            selected_starting_point = None
            selected_destination = None
            selected_departure = None

        if submitted:
            selected_starting_point = selected_city
            selected_destination = selected_city1
            selected_departure = date_select

        df['city_state'] = df['city_ascii, state_id']

        start_coord = df.query('city_state == @selected_city')
        start_lat = float(start_coord['lat'].iloc[0])
        start_lon = float(start_coord['lng'].iloc[0])

        end_coord = df.query('city_state == @selected_city1')
        end_lat = float(end_coord['lat'].iloc[0])
        end_lon = float(end_coord['lng'].iloc[0])

        return selected_starting_point, selected_destination, selected_departure, start_lat, start_lon,end_lat,end_lon

    selected_starting_point, selected_destination, selected_departure, start_lat, start_lon, end_lat, end_lon = menu_selection() 

    def route_info(selected_starting_point, selected_destination, selected_departure, start_lat, start_lng, end_lat, end_lng):
        
        MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZmlyc3RpbndlYXRoZXIiLCJhIjoiY20ydjlpY215MDl4NjJqb2l1ZjBwbXo2NSJ9.vt3Xx08GULpig9DYBb5o0A'

        selected_departure_time = datetime.strptime(selected_departure, "%Y-%m-%d %I %p")
    
        start_point = [start_lon, start_lat] 
        end_point = [end_lon, end_lat] 

        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start_point[0]},{start_point[1]};{end_point[0]},{end_point[1]}"
        params = {
            'geometries': 'geojson',
            'overview': 'full',
            'steps': 'true',
            'access_token': MAPBOX_ACCESS_TOKEN,
            'depart_at': selected_departure_time
        }

        response = requests.get(url, params=params)
        data = response.json()

        # Parse the response to get duration and coordinates
        route = data['routes'][0]
        total_duration = route['duration']  # Total duration in seconds
        interval = 3600  # 60 minutes in seconds

        coordinates_every_60 = []
        current_time = 0

        for leg in route['legs']:
            for step in leg['steps']:
                
                step_duration = step['duration']
                step_coords = step['geometry']['coordinates']
                
                for i, coord in enumerate(step_coords):
                    # Calculate cumulative travel time to this point
                    cumulative_time = current_time + (step_duration / len(step_coords)) * i
                    
                    # If the cumulative time is close to the next interval, add the coordinate
                    if cumulative_time >= interval * len(coordinates_every_60):
                        coordinates_every_60.append({
                            'lat': coord[1],
                            'lon': coord[0],
                            'time': str(timedelta(seconds=cumulative_time))
                        })
                
                current_time += step_duration  # Update time for the next step

        closest_rows = pd.DataFrame(coordinates_every_60)
        st.text('hi')
        st.text(closest_rows)


    if selected_starting_point != None:
        route_info_df = route_info(selected_starting_point, selected_destination, selected_departure, start_lat, start_lon, end_lat, end_lon)

    def collect_weather_data():
        print('hi')

    def map_plot(selected_starting_point, selected_destination):
        
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <title>Display navigation directions</title>
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
        <link href="https://api.mapbox.com/mapbox-gl-js/v3.7.0/mapbox-gl.css" rel="stylesheet">
        <script src="https://api.mapbox.com/mapbox-gl-js/v3.7.0/mapbox-gl.js"></script>
        <style>
        html, body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        </style>
        </head>
        <body>
        <script src="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-directions/v4.3.1/mapbox-gl-directions.js"></script>
        <link rel="stylesheet" href="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-directions/v4.3.1/mapbox-gl-directions.css" type="text/css">
        <div id="map"></div>

        <script>
            mapboxgl.accessToken = 'pk.eyJ1IjoiZmlyc3RpbndlYXRoZXIiLCJhIjoiY20ydjlpY215MDl4NjJqb2l1ZjBwbXo2NSJ9.vt3Xx08GULpig9DYBb5o0A';
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/streets-v12',
                center: [-79.4512, 43.6568],
                zoom: 4
            }});

            // Initialize the MapboxDirections control with driving only
            const directions = new MapboxDirections({{
                accessToken: mapboxgl.accessToken,
                profile: 'mapbox/driving',
                controls: {{profileSwitcher: false}}
            }});

            // Add the directions control to the map
            map.addControl(directions, 'top-left');

            // Set origin and destination
            //directions.setOrigin([-77.99233,38.33267]);
            //directions.setDestination([-77.42824,38.89672]);

            map.on('load', () => {{
            directions.setOrigin('{selected_starting_point}');
            directions.setDestination('{selected_destination}');
            directions.query();
            }});

            // Immediately call query() after setting both points to render the route
            directions.query();

        </script>

        </body>
        </html>
        """

        st.components.v1.html(html_code, height=600, scrolling=False)


    if selected_starting_point != None: 
        map_plot(selected_starting_point, selected_destination)
        
    
        
# Defines streamlit page names
page_names_to_funcs = {
    #"Weather Forecast": page1,
    "test2": phone
}

# Initializes streamlit sidebar to select desired page
demo_name = st.sidebar.selectbox('Select tab',page_names_to_funcs.keys())

# Runs selected page
page_names_to_funcs[demo_name]()
