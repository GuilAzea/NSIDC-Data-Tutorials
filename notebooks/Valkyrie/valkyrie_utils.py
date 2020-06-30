import ipywidgets as widgets
import pandas as pd
import requests
from datetime import datetime,date
from ipyleaflet import Map, projections, basemaps, DrawControl
from cmr import GranuleQuery

start_date = datetime(1993, 1, 1)
end_date = datetime(2020, 5, 1)
datasets_cmr = []
datasets_valkyrie = []


dates = pd.date_range(start_date, end_date, freq='D')
options = [(date.strftime(' %Y-%m-%d '), date) for date in dates]
index = (0, len(options)-1)

dc = DrawControl(circlemarker={},
                 polyline={},
                 polygon={},
                 rectangle = {
                    "shapeOptions": {
                        "fillColor": "#fca45d",
                        "color": "#fca45d",
                        "fillOpacity": 0.5
                    }
})



north_3413 = {
    'name': 'EPSG:3413',
    'custom': True,
    'proj4def': '+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs',
    'origin': [-4194304, 4194304],
    'bounds': [
        [-4194304, -4194304],
        [4194304, 4194304]
    ],
    'resolutions': [
        16384.0,
        8192.0,
        4096.0,
        2048.0,
        1024.0,
        512.0,
        256.0
    ]
}

south_3031 = {
    'name': 'EPSG:3031',
    'custom': True,
    'proj4def': '+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs',
    'origin': [-4194304, 4194304],
    'bounds': [
        [-4194304, -4194304],
        [4194304, 4194304]
    ],
    'resolutions': [
        16384.0,
        8192.0,
        4096.0,
        2048.0,
        1024.0,
        512.0,
        256.0
    ]
}

date_range_slider = widgets.SelectionRangeSlider(
    options=options,
    index=index,
    description='Date Range',
    orientation='horizontal',
    layout={'width': '100%'}
)

dataset = widgets.SelectMultiple(
    options=['ATM', 'GLAH06', 'ILVIS2'],
    value=['ATM'],
    rows=4,
    description='Datasets',
    disabled=False
)


hemisphere = {
    'north': {
        'base_map': basemaps.NASAGIBS.BlueMarble3413,
        'projection': north_3413,
        'center': (90,0)
    },
    'south': {
        'base_map': basemaps.NASAGIBS.BlueMarble3031,
        'projection': south_3031,
        'center': (-90,0)
    }
}

ITRF = widgets.Dropdown(
    options=['', 'ITRF2000', 'ITRF2008', 'ITRF2014'],
    description='ITRF:',
    disabled=False,
)


def bounding_box(points):
    x_coordinates, y_coordinates = zip(*points)

    return [(min(x_coordinates), min(y_coordinates)), (max(x_coordinates), max(y_coordinates))]

def build_params():
    if dc.last_draw['geometry'] is None:
        print('You need to select an area using the box tool')
        return None
    coords = [list(coord) for coord in bounding_box(dc.last_draw['geometry']['coordinates'][0])]
    bbox = f'{coords[0][0]},{coords[0][1]},{coords[1][0]},{coords[1][1]}'
    d1 = date_range_slider.value[0].date()
    d2 = date_range_slider.value[1].date()
#     if (d2-d1).days > 180:
#         print('Remember this is a tutorial, if you want more than a year of data please contact NSIDC support')
#         print('...Adjust the time range slider and try again!')
#         return None
    start = d1.strftime('%Y-%m-%d')
    end = d2.strftime('%Y-%m-%d')

    params = {
        'time_range': f'{start},{end}',
        'bbox': bbox
    }
    if ITRF.value != '' :
        params['itrf'] = ITRF.value
    return params

def query_cmr(b):
    granules = []
    datasets_cmr = []
    datasets_valkyrie = []
    d1 = date_range_slider.value[0].date()
    d2 = date_range_slider.value[1].date()
    if dc.last_draw['geometry'] is None:
        print('You need to select an area using the box tool')
        return None
    coords = [list(coord) for coord in bounding_box(dc.last_draw['geometry']['coordinates'][0])]
    bbox = (coords[0][0],coords[0][1],coords[1][0],coords[1][1])
    if 'ATM' in dataset.value:
        datasets_cmr.extend([{'name':'ILATM1B'},{'name':'BLATM1B'}])
        datasets_valkyrie.append('ATM1B')
    if 'GLAH06' in dataset.value:
        datasets_cmr.append({'name':'GLAH06'})
        datasets_valkyrie.append('GLAH06')
    if 'ILVIS2' in dataset.value:
        datasets_cmr.append({'name': 'ILVIS2', 'version': '002'})
        datasets_valkyrie.append('ILVIS2')

    for d in datasets_cmr:
        cmr_api = GranuleQuery()
        g = cmr_api.parameters(
            short_name=d['name'],
            temporal=(d1,d2),
            bounding_box = bbox).hits()
        granules.append({d['name']: g})
    if b is not None:
        print(granules)
    return granules

granule_count =  widgets.Button(description="Get Granule Count", )
granule_count.on_click(query_cmr)


def ui(region):
    h = hemisphere[region]
    base_map = Map(
        center=h['center'],
        zoom=1,
        basemap=h['base_map'],
        crs=h['projection'])
    base_map.add_control(dc)
    display(dataset, ITRF, date_range_slider, base_map, granule_count)


region = widgets.Dropdown(
    options=['south', 'north'],
    description='Hemisphere:',
    disabled=False,
)

def post_orders(params):
    responses = []
    datasets_valkyrie = []
    if 'ATM' in dataset.value:
        datasets_valkyrie.append('ATM1B')
    if 'GLAH06' in dataset.value:
        datasets_valkyrie.append('GLAH06')
    if 'ILVIS2' in dataset.value:
        datasets_valkyrie.append('ILVIS2')
    for d in datasets_valkyrie:
        base_url = f'http://staging.valkyrie-vm.apps.nsidc.org/1.0/{d}'
        response = requests.post(base_url, params=params)
        # now we are going to return the response from Valkyrie
        responses.append({d: response.json()})
    return responses
