import folium as fl
import geopandas as gpd
import pandas as pd
import ast
import streamlit as st
from streamlit_folium import st_folium, folium_static
#import fitz
import pdfkit
from PIL import Image
from io import BytesIO



st.set_page_config(page_title='Youth Density',page_icon="chart-with-upwards-trend")
st.title('GNYC Youth Density Map')


"""def convert_map_png(folium_map, file_name):
  mapName = file_name

  # Get HTML File of Map
  folium_map.save(mapName + '.html')
  htmlfile = mapName + '.html'

  # Convert Map from HTML to PDF, Delay to Allow Rendering
  options = {'javascript-delay': 500,
    'page-size': 'Letter',
    'margin-top': '0.0in',
    'margin-right': '0.0in',
    'margin-bottom': '0.0in',
    'margin-left': '0.0in',
    'encoding': "UTF-8",
    'custom-header': [
        ('Accept-Encoding', 'gzip')
    ]}
  pdfkit.from_file(htmlfile,  (mapName + '.pdf'), options=options)
  pdffile = mapName + '.pdf'

  # Convert Map from PDF to PNG
  doc = fitz.open(pdffile)
  page = doc.load_page(0)
  pix = page.get_pixmap()
  output = mapName + '.png'
  pix.save(output)
  pngfile = mapName + '.png'
  doc.close()

  # Crop Out Map Image
  pilImage = Image.open(pngfile)

  croppedImage = pilImage.crop((0,0,287,287)) # Adjust this if your map renders differently on PDF

  return croppedImage"""


tracts = gpd.read_file('NY_Tracts.geojson')
ythcnt = pd.read_csv('ythcnt.csv')
units = pd.read_csv('unit_locations.csv')
hoods = gpd.read_file('nyc_neighborhoods.geojson')
units['lat_lon'] = units['lat_lon'].apply(lambda x: ast.literal_eval(x))
#tracts_youth = tracts.join(ythcnt,on='GEOID',rsuffix='youth')
tracts['GEOID'] = tracts['GEOID'].astype(str)
ythcnt['GEOID'] = ythcnt['GEOID'].astype(str)
tracts = tracts.set_index('GEOID').join(ythcnt.set_index('GEOID'),rsuffix='ythcnt')
tracts.reset_index(inplace=True)

feat_group = fl.FeatureGroup(name='Traditional Locations')
sr_group = fl.FeatureGroup(name='SR Locations')
exp_group = fl.FeatureGroup(name='Exploring Locations')
age_mod = {'Cub Level':['cub_per_tract',[0,1,2.5,5,10,23],'cub_youth_total','female_cub_scouts','male_cub_scouts'],
            'ScoutsBSA Level':['troop_per_tract',[0,1,2.5,5,10,23],'troop_youth_total','female_troop_scouts','male_troop_scouts']}

district = st.sidebar.selectbox('District',['All','Bronx','Brooklyn','Manhattan',
                                            'Queens','Staten Island',
                                            'Scoutreach','Exploring'])
map_type = st.sidebar.selectbox('Map Type',['Density','YOY Change'])
program_mod = st.sidebar.checkbox('Adjust Program Data?')
if program_mod:
    program = st.sidebar.selectbox('Age Range',['Cub Level','ScoutsBSA Level'])
    a_mod = age_mod[program][0]
    bin = age_mod[program][1]
    totes_youth = age_mod[program][2]
    f_youth = age_mod[program][3]
    m_youth = age_mod[program][4]
else:
    a_mod = 'scouts_per_tract'
    bin = [0,1,2.5,5,10,15]
    totes_youth = 'total_pop'
    f_youth = 'female_scouts'
    m_youth = 'male_scouts'
sr_check = False
exp_check = False
if district in ['Bronx','Brooklyn','Manhattan','Queens']:
    sr_check = st.sidebar.checkbox('Add Scoutreach?')

if district in ['Bronx','Brooklyn','Manhattan','Queens','Staten Island']:
    exp_check = st.sidebar.checkbox('Add Exploring?')



all_items = [10]
sr_items = [10]
exp_items = [10]
all_items.extend(tracts.NAMELSADCO.unique().tolist())
all_items.extend(units.distID.unique().tolist())
sr_items.extend(tracts.NAMELSADCO.unique().tolist())
sr_items.extend([19,23,43])
exp_items.extend(tracts.NAMELSADCO.unique().tolist())
exp_items.extend([33,95,96])

dist_dict = {'All':all_items,
            'Bronx':[12,'Bronx County',15],'Brooklyn':[11,'Kings County',21,22],
            'Manhattan':[11,'New York County',30],'Queens':[10,'Queens County',45,42,44],
            'Staten Island':[11,'Richmond County',50],
            'Scoutreach':sr_items,
            'Exploring':exp_items}




if len(dist_dict[district]) < 6:
    geoids_yth = ythcnt[ythcnt['GEOID'].isin(tracts[tracts['NAMELSADCO']==dist_dict[district][1]].GEOID.unique().tolist())]
else:
    geoids_yth = ythcnt
if exp_check:
    temp = dist_dict[district]
    temp.extend([95,96,33])
    dist_dict.update({district:temp})

if sr_check:
    temp = dist_dict[district]
    if str(temp[-1])[0] == '1':
        temp.append(19)
    elif str(temp[-1])[0] == '2':
        temp.append(23)
    elif str(temp[-1])[0] == '4':
        temp.append(43)
    else:
        temp.extend([19,23,43])
    dist_dict.update({district:temp})

units = units[units['distID'].isin(dist_dict[district])]


_map = fl.Map(location=[units.lat.mean(),units.lon.mean()],
                    zoom_start=dist_dict[district][0],
                    tiles='CartoDB Positron')


#change_map = fl.Map(location=[units.lat.mean(),units.lon.mean()],
#                zoom_start=dist_dict[district][0],
#                tiles='CartoDB Positron')
if map_type == 'Density':
    choro = fl.Choropleth(
                            geo_data=tracts[tracts['NAMELSADCO'].isin(dist_dict[district])],
                            data=ythcnt,
                            columns=['GEOID', a_mod],  #Here we tell folium to get the county fips and plot new_cases_7days metric for each county
                            key_on='feature.properties.GEOID', #Here we grab the geometries/county boundaries from the geojson file using the key 'coty_code' which is the same as county fips #use the custom scale we created for legend
                            fill_color='YlOrRd',
                            bins=bin,
                            nan_fill_color="White",
                            nan_fill_opacity=0.0, #Use white color if there is no data available for the county
                            fill_opacity=0.7,
                            line_opacity=0.2,
                            legend_name='Percent of TAY in Scouting', #title of the legend
                            highlight=True,
                            line_color='black',
                            name='Percentage of Scouts')

    choro.geojson.add_child(fl.GeoJsonPopup(fields=['GEOID',a_mod,totes_youth,
                                                    f_youth,m_youth],
                                            aliases=['Tract ','Percent of Scouts: ','Total Youth: ',
                                                     'Female Scouts: ', 'Male Scouts: '],
                                            sticky=True))
else:
    choro = fl.Choropleth(
                        geo_data=tracts[tracts['NAMELSADCO'].isin(dist_dict[district])],
                        data=ythcnt,
                        columns=['GEOID', '2023_difference_per_tract'],  #Here we tell folium to get the county fips and plot new_cases_7days metric for each county
                        key_on='feature.properties.GEOID', #Here we grab the geometries/county boundaries from the geojson file using the key 'coty_code' which is the same as county fips #use the custom scale we created for legend
                        fill_color='RdYlGn',
                        bins = [-8,-5,-2,-1,-0.5,0,0.5,1,2,5,10],
                        #bins=list(ythcnt['2023_difference_per_tract'].quantile([0,0.25,0.5,0.75,1])),
                        nan_fill_color="White",
                        nan_fill_opacity=0.0, #Use white color if there is no data available for the county
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name='Difference to 2022', #title of the legend
                        highlight=True,
                        line_color='black',
                        name='Change vs. 2022')
    choro.geojson.add_child(fl.GeoJsonPopup(fields=['GEOID',a_mod,totes_youth,
                                                    f_youth,m_youth,'2023_difference_per_tract'],
                                            aliases=['Tract ','Percent of Scouts: ','Total Youth: ',
                                                     'Female Scouts: ', 'Male Scouts: ','YOY Change: '],
                                            sticky=True))

if program_mod:
    if program == 'Cub Level':
        units = units[units['UnitType'] == 'Pack']
    elif program == 'ScoutsBSA Level':
        units = units[units['UnitType'].isin(['Crew','Troop','Ship','Club','Post'])]

for unit in units.itertuples():
    lat, lon = unit.lat_lon

    disp = fl.Popup('Unit: ' + unit.Unit+'\n\nYouth: '
                    +str(unit.Youth)+'\n\nAddress: '
                    +unit.full_address,max_width='500%')

    if unit.distID in [19,43,23]:
        fl.CircleMarker(location=[lon,lat],
                        popup=disp,
                        radius = 2,
                        width = 0,
                        color='red').add_to(sr_group)
    elif unit.distID in [95,96,33]:
        fl.CircleMarker(location=[lon,lat],
                        popup=disp,
                        radius = 2,
                        width = 0,
                        color='black').add_to(exp_group)
    else:
        fl.CircleMarker(location=[unit.lat,unit.lon],
                            popup=disp,
                            radius = 2,
                            width = 0,
                            color='blue').add_to(feat_group)

locals = fl.FeatureGroup(name='Neighborhoods',show=False)
style = {'fillColor':'#000000','color':'#000000', 'weight':1}

for _ , item in hoods.iterrows():
    if district in ['All','Scoutreach','Exploring']:
        neigh = fl.GeoJson(data=item['geometry'], name='Neighborhoods',style_function= lambda x:style)
        fl.Popup(item['neighborhood']).add_to(neigh)
        neigh.add_to(locals)
    elif item['borough'] == district:
        neigh = fl.GeoJson(data=item['geometry'], name='Neighborhoods',style_function= lambda x:style)
        fl.Popup(item['neighborhood']).add_to(neigh)
        neigh.add_to(locals)
    else:
        pass
locals.add_to(_map)

choro.add_to(_map)
#choro_diff.add_to(change_map)
if sr_check or district in ['All','Scoutreach']:
    sr_group.add_to(_map)
#    sr_group.add_to(change_map)
if exp_check or district in ['All','Exploring']:
    exp_group.add_to(_map)
#    exp_group.add_to(change_map)
feat_group.add_to(_map)
#feat_group.add_to(change_map)

_map.keep_in_front(feat_group,sr_group,exp_group)
fl.LayerControl().add_to(_map)


tab1, tab2 = st.tabs(['Metrics',f'{map_type} Map'])

with tab1:
    col1, col2, col3 = st.columns(3,gap='small')
    col4, col5, col6 = st.columns(3,gap='small')
    col7, col8, col9 = st.columns(3,gap='small')


    col1.metric('Total Scouts',int(geoids_yth[f_youth].sum()+geoids_yth[m_youth].sum()))
    col2.metric('Female Scouts',int(geoids_yth[f_youth].sum()))
    col3.metric('Male Scouts',int(geoids_yth[m_youth].sum()))
    col4.metric('Percent of Youth Served',f'{round(((geoids_yth[f_youth].sum()+geoids_yth[m_youth].sum())/geoids_yth[totes_youth].sum())*100,2)}%')
    col5.metric('Percent of Female Youth Served',f"{round((geoids_yth[f_youth].sum()/geoids_yth['female_troop_total'].sum())*100,2)}%")
    col6.metric('Percent of Male Youth Served',f"{round((geoids_yth[m_youth].sum()/geoids_yth['male_troop_total'].sum())*100,2)}%")
    col7.metric('Total Units',len(units))
    #st.write('Top Identified Census Tracts for NAC')
    #st.table(geoids_yth.sort_values(by=['scouts_per_tract'])[['GEOID','scouts_per_tract','num_scouts','total_pop','female_scouts','male_scouts']].head(10))
with tab2:
    st_map = folium_static(_map,height=500,width=700)

    """pngmap = convert_map_png(_map,'gnyc_density_map')
    buf=BytesIO()
    pngmap.save(buf,format="PNG")
    byte_im = buf.getvalue()"""
    dwnld = st.download_button(label='Download Map Image',
                                data=byte_im,
                                file_name='gnyc_density_map.png',
                                mime='image/png')


#with tab3:
    #fl.LayerControl().add_to(change_map)
    #st_change_map = folium_static(change_map,height=350,width=500)


#_map.save('gnyc_map.html')
