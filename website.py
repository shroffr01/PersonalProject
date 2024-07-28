
import streamlit as st
import numpy as np
import pandas as pd
import numpy as np
import requests
import json
import os
import datetime

import plotly.express as px
import plotly.graph_objects as go

import plotly.io as pio
pio.renderers.default = 'browser'

pio.renderers.default = 'browser'

st.set_page_config(layout="wide")
st.set_option('deprecation.showPyplotGlobalUse', False)

#@st.cache_data
#def long_running_function(param1, param2):
#    return

def page1():

    df = pd.read_csv('person_projec_dataframe.csv')

    selected_city = st.selectbox("Select a city", df['city_ascii, state_id'].unique())
    st.write("Selected City:", selected_city)

    selected_row = df[df['city_ascii, state_id'] == selected_city].iloc[0]
            
    # Initializes lat and lon of selected wind farm through CSV
    selected_lat = selected_row['lat']

    selected_lon = selected_row['lng']
    
    def weather_forecast(selected_lat, selected_lon):
        #st.write('hi')
        r = requests.get('https://httpbin.org/user-agent')
        useragent = json.loads(r.text)['user-agent']
        headers = {'User-agent': useragent}

        # Get URL for hourly forecast data and hourly grid data

        url = f"https://api.weather.gov/points/{selected_lat},{selected_lon}"
        r = requests.get(url, headers = headers)

        myjson = json.loads(r.text)
        df1 = pd.json_normalize(myjson['properties'])
        hourlyURL = df1['forecastHourly'].iloc[0]   
        hourlyURL_grid = df1['forecastGridData'].iloc[0] 

        # Obtain actual hourly forecast data

        r = requests.get(hourlyURL, headers = headers)

        myjson = json.loads(r.text)
        df1 = pd.json_normalize(myjson['properties']['periods'])

        # Obtain grid hourly data for sky cover, heat index, etc. 

        r_g = requests.get(hourlyURL_grid, headers = headers)

        myjson_g = json.loads(r_g.text)

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

            fig.add_trace(go.Scatter(x=df1['startTime'], y=var_to_plot,
                                line=dict(color=color, width=4)))

            st.plotly_chart(fig)

        make_hourly_plot('Temperature','Temperature (F)',df1['temperature'],'red' )
        make_hourly_plot('Probability of Precipitation','%',df1['probabilityOfPrecipitation.value'],'green' )
        make_hourly_plot('Wind Speed','Wind Speed (mph)',df1['windSpeed'],'black' )
        
        
        df_skycover = pd.json_normalize(myjson_g['properties']['skyCover']['values'])
        df_windgust = pd.json_normalize(myjson_g['properties']['windGust']['values'])
        df_snowfall = pd.json_normalize(myjson_g['properties']['snowfallAmount']['values'])
        df_heat_index = pd.json_normalize(myjson_g['properties']['heatIndex']['values'])
        df_wind_chill = pd.json_normalize(myjson_g['properties']['windChill']['values'])
        df_visibility = pd.json_normalize(myjson_g['properties']['visibility']['values'])

        def convert_time(var_name):

            var_name['validTime'] = var_name['validTime'].str.extract(r'^(.*?)/')
            var_name['validTime'] = pd.to_datetime(var_name['validTime'])
            return var_name

        df_skycover = convert_time(df_skycover)
        df_windgust = convert_time(df_windgust)
        df_snowfall = convert_time(df_snowfall)
        df_heat_index = convert_time(df_heat_index)
        df_wind_chill = convert_time(df_wind_chill)
        df_visibility = convert_time(df_visibility)  

        

        make_hourly_plot('Skycover', 'Skycover %', df_skycover['value'], 'blue')
        make_hourly_plot('Wind Gust', 'Wind Gust (mph)', df_windgust['value'], 'purple')
        make_hourly_plot('visibility', 'miles', df_visibility['value'], 'grey')
        make_hourly_plot('heatindex', 'Temperature (F)', df_heat_index['value'], 'red')
            
    weather_forecast(selected_lat, selected_lon)

def phone():
    st.write('bye')

# Defines streamlit page names
page_names_to_funcs = {
    "Weather Forecast": page1,
    "test2": phone
}

# Initializes streamlit sidebar to select desired page
demo_name = st.sidebar.selectbox('Select tab',page_names_to_funcs.keys())

# Runs selected page
page_names_to_funcs[demo_name]()
