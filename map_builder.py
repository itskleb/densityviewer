import folium as fl
import geopandas as gpd
import pandas as pd
import ast
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title='Youth Density',page_icon="random",layout='wide')
st.title('Youth Density Map')
_map = fl.Map(location=[40.71,-74.0],zoom_start=10,tiles='CartoDB Positron')

tracts = gpd.read_file('NY_Tracts.geojson')
ythcnt = pd.read_csv('ythcnt.csv')
units = pd.read_csv('unit_locations.csv')
units['lat_lon'] = units['lat_lon'].apply(lambda x: ast.literal_eval(x))
#tracts_youth = tracts.join(ythcnt,on='GEOID',rsuffix='youth')
tracts['GEOID'] = tracts['GEOID'].astype(str)
ythcnt['GEOID'] = ythcnt['GEOID'].astype(str)
tracts = tracts.set_index('GEOID').join(ythcnt.set_index('GEOID'),rsuffix='ythcnt')
tracts.reset_index(inplace=True)

feat_group = fl.FeatureGroup(name='Traditional Locations')
sr_group = fl.FeatureGroup(name='SR Locations')
exp_group = fl.FeatureGroup(name='Exploring Locations')

district = st.sidebar.selectbox('District',['Bronx','Brooklyn','Manhattan',
                                            'Queens','Staten Island',
                                            'Scoutreach','Exploring'])
dist_dict = {'Bronx':['Bronx County',15],'Brooklyn':['Kings County',21,23],
            'Manhattan':['New York County',30],'Queens':['Queens County',45,42,44],
            'Staten Island':['Richmond County',50],
            'Scoutreach':tracts.NAMELSADCO.unique().tolist().append([19,23,43]),
            'Exploring':tracts.NAMELSADCO.unique().tolist().append([33,95,96])}

choro = fl.Choropleth(
                        geo_data=tracts[tracts['NAMELSADCO'].isin(dist_dict[district])],
                        data=ythcnt,
                        columns=['GEOID', 'scouts_per_tract'],  #Here we tell folium to get the county fips and plot new_cases_7days metric for each county
                        key_on='feature.properties.GEOID', #Here we grab the geometries/county boundaries from the geojson file using the key 'coty_code' which is the same as county fips #use the custom scale we created for legend
                        fill_color='YlOrRd',
                        bins=[0,1,2.5,5,10,15],
                        nan_fill_color="White", #Use white color if there is no data available for the county
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name='Youth in each Tract', #title of the legend
                        highlight=True,
                        line_color='black',
                        name='Percentage of Scouts')

choro.geojson.add_child(fl.GeoJsonPopup(fields=['GEOID','scouts_per_tract','total_pop',
                                                'female_scouts','male_scouts'],
                                        aliases=['Tract ','Percent of Scouts: ','Total Youth: ',
                                                 'Number of Female Scouts: ', 'Number of Male Scouts: '],
                                        sticky=True))
units = units[units['distID'].isin(dist_dict[district])]
for unit in units.itertuples():
    lat, lon = unit.lat_lon

    disp = fl.Popup('Unit: ' + unit.Unit_Name+'\n\nYouth: '
                    +str(unit.Youth)+'\n\nAddress: '
                    +unit.full_address,max_width='500%')

    if unit.distID in [19,43,23]:
        fl.CircleMarker(location=[lon,lat],
                        popup=disp,
                        radius = 1,
                        width = 0,
                        color='green').add_to(sr_group)
    elif unit.distID in [95,96,33]:
        fl.CircleMarker(location=[lon,lat],
                        popup=disp,
                        radius = 1,
                        width = 0,
                        color='black').add_to(exp_group)
    else:
        fl.CircleMarker(location=[lon,lat],
                            popup=disp,
                            radius = 1,
                            width = 0,
                            color='blue').add_to(feat_group)

choro.add_to(_map)
sr_group.add_to(_map)
exp_group.add_to(_map)
feat_group.add_to(_map)
fl.LayerControl().add_to(_map)
_map.keep_in_front(feat_group,sr_group,exp_group)


st_folium(_map,returned_objects=[])
#_map.save('gnyc_map.html')
