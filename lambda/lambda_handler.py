import os
import sys
import logging
import boto3
import datetime
import zipfile
from urllib import urlretrieve
import json

# add path to included packages
path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(path, 'lib/python2.7/site-packages'))

# commented out to avoid duplicate logs in lambda
# logger.addHandler(logging.StreamHandler())

from osgeo import ogr

s3_client = boto3.client('s3')
bucket = 'active-fire-data'


def upload_and_convert(url, name_prefix, timestamp):
    tmp_name = '/tmp/{}.zip'.format(name_prefix)
    urlretrieve(url, tmp_name)
    shape_file_name = [f for f in zipfile.ZipFile(tmp_name).namelist() if f.split('.')[1] == 'shp'][0]

    shape_file = '/vsizip//{}/{}'.format(tmp_name, shape_file_name) 

    drv = ogr.GetDriverByName('ESRI Shapefile')
    data = drv.Open(shape_file, 0)
    l = data.GetLayer()

    features = [json.loads(f.ExportToJson()) for f in l]

    geojson_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    upload_path = '/tmp/{}_latest.geojson'.format(name_prefix)
    with open(upload_path, 'w') as f:
        f.write(json.dumps(geojson_collection))

    try:
        s3_client.upload_file(upload_path, bucket, '{}_latest.geojson'.format(name_prefix))
        s3_client.upload_file(upload_path, bucket, '{}_{}.geojson'.format(name_prefix, timestamp))
    except Exception:
        return False
    return True

def handler(event, context):
    """ Lambda handler """

    today = datetime.datetime.now()

    ts = '{day}_{month}_{year}_{hour}'.format(
        day=today.day,
        month=today.month,
        year=today.year,
        hour=today.hour)

    usgs_url = 'https://rmgsc.cr.usgs.gov/outgoing/GeoMAC/current_year_fire_data/current_year_all_states/active_perimeters_dd83.zip'
    viirs_url = 'https://firms.modaps.eosdis.nasa.gov/active_fire/viirs/shapes/zips/VNP14IMGTDL_NRT_USA_contiguous_and_Hawaii_7d.zip'
    modis_url = 'https://firms.modaps.eosdis.nasa.gov/active_fire/c6/shapes/zips/MODIS_C6_USA_contiguous_and_Hawaii_7d.zip'
    
    usgs_result = upload_and_convert(usgs_url, 'usgs', ts)
    viirs_result = upload_and_convert(viirs_url, 'viirs', ts)
    modis_result = upload_and_convert(modis_url, 'modis', ts)
    
    return { "modis_converted": modis_result, "viirs_converted": viirs_result, "usgs_converted": usgs_result }
