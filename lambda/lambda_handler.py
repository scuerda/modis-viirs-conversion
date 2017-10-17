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

def handler(event, context):
    """ Lambda handler """

    today = datetime.datetime.now()

    ts = '{day}_{month}_{year}_{hour}'.format(
        day=today.day,
        month=today.month,
        year=today.year,
        hour=today.hour)

    bucket = 'active-fire-data'
    modis_url = 'https://firms.modaps.eosdis.nasa.gov/active_fire/c6/shapes/zips/MODIS_C6_USA_contiguous_and_Hawaii_7d.zip'
    viirs_url = 'https://firms.modaps.eosdis.nasa.gov/active_fire/viirs/shapes/zips/VNP14IMGTDL_NRT_USA_contiguous_and_Hawaii_7d.zip'

    # Get and convert modis

    urlretrieve(viirs_url, '/tmp/modis.zip')

    shape_file_name = [f for f in zipfile.ZipFile('/tmp/modis.zip').namelist() if f.split('.')[1] == 'shp'][0]

    vi_file = '/vsizip//tmp/modis.zip/{}'.format(shape_file_name)
    drv = ogr.GetDriverByName('ESRI Shapefile')
    modis_data = drv.Open(vi_file, 0)
    l = modis_data.GetLayer()

    features = [json.loads(f.ExportToJson()) for f in l]

    modis = {
        "type": "FeatureCollection",
        "features": features,
    }

    upload_path = '/tmp/modis.geojson'

    with open(upload_path, "w") as f:
    	f.write(json.dumps(features))

    s3_client.upload_file(upload_path, bucket, 'modis_latest.geojson')
    s3_client.upload_file(upload_path, bucket, 'modis_{ts}.geojson'.format(ts=ts))
    
    # # Get and convert viirs
    urlretrieve(viirs_url, '/tmp/viirs.zip')
    shape_file_name = [f for f in zipfile.ZipFile('/tmp/viirs.zip').namelist() if f.split('.')[1] == 'shp'][0]
    vi_file = '/vsizip//tmp/viirs.zip/{}'.format(shape_file_name)
    drv = ogr.GetDriverByName('ESRI Shapefile')
    data = drv.Open(vi_file, 0)
    l = data.GetLayer()

    features = [json.loads(f.ExportToJson()) for f in l]

    viirs = {
        "type": "FeatureCollection",
        "features": features,
    }

    upload_path = '/tmp/viirs_latest.geojson'
    with open(upload_path, "w") as f:
        f.write(json.dumps(features))

    s3_client.upload_file(upload_path, bucket, 'viirs_latest.geojson')
    s3_client.upload_file(upload_path, bucket, 'viirs_{ts}.geojson'.format(ts=ts))
    return { "modis_converted": True, "viirs_converted": True }
