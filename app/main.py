import os
import io
from typing import Optional, List, Any
from pymongo import MongoClient
from bson.objectid import ObjectId
# import pandas as pd
# import numpy as np
from fastapi import FastAPI, Response, Query
from pydantic import BaseModel
import yaml
import datetime
from fastapi.responses import JSONResponse
# import pickle
import orjson
from bson import json_util
import zstandard as zstd
from enum import Enum
from fastapi.encoders import jsonable_encoder


base_dir = os.path.realpath(os.path.dirname(__file__))

with open(os.path.join(base_dir, 'parameters.yml')) as param:
    param = yaml.safe_load(param)

db_dict = param['db']

## For testing
# db_dict.update({'HOST': '127.0.0.1'})


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


# class Dataset(BaseModel):
#     feature: str
#     parameter: str
#     method: str
#     processing_code: str
#     owner: str
#     aggregation_statistic: str
#     frequency_interval: str
#     utc_offset: str
#     units: Optional[str] = None
#     license: Optional[str] = None
#     result_type: Optional[str] = None

    # name: str
    # description: Optional[str] = None
    # price: float
    # tax: Optional[float] = None

class Polygon(BaseModel):
    type: str
    coordinates: List

class Compress(str, Enum):
    zstd = 'zstd'


base_url = '/tethys/data/'

app = FastAPI(default_response_class=ORJSONResponse)

client = MongoClient(db_dict['HOST'], password=db_dict['PASSWORD'], username=db_dict['USERNAME'], authSource=db_dict['DATABASE'])
db = client[db_dict['DATABASE']]


@app.get(base_url + 'datasets')
async def get_datasets():
    q_dict = {}
    ds_coll = db['dataset']
    ds1 = list(ds_coll.find(q_dict))
    for ds in ds1:
        ds['dataset_id'] = str(ds.pop('_id'))

    return ds1


@app.post(base_url + 'sampling_sites')
async def get_sites(dataset_id: str, polygon: Optional[Polygon] = None, compression: Optional[Compress] = None):
    ds_coll = db['dataset']
    try:
        ds_id = ds_coll.find({'_id': ObjectId(dataset_id)}, {'_id': 1}).limit(1)[0]['_id']
    except:
        raise ValueError('No dataset with those input parameters.')

    site_ds_coll = db['site_dataset']
    site_ds1 = list(site_ds_coll.find({'dataset_id': ds_id}, {'site_id': 1, 'stats': 1, 'modified_date': 1}))

    site_ids = [s['site_id'] for s in site_ds1]

    site_coll = db['sampling_site']
    sites1 = list(site_coll.find({'_id': {'$in': site_ids}}, {'modified_date': 0}))

    for s in sites1:
        site_id = s['_id']
        [s.update(ds) for ds in site_ds1 if site_id == ds['site_id']]
        s.pop('_id')
        # s.pop('site_id')
        s['site_id'] = str(s['site_id'])

    if compression == 'zstd':
        cctx = zstd.ZstdCompressor(level=1)
        b_ts1 = orjson.dumps(sites1)
        c_obj = cctx.compress(b_ts1)

        return Response(c_obj, media_type='application/zstd')
    else:
        return sites1


@app.get(base_url + 'time_series_results')
async def get_data(dataset_id: str, site_id: str, from_date: Optional[datetime.datetime] = None, to_date: Optional[datetime.datetime] = None, from_modified_date: Optional[datetime.datetime] = None, to_modified_date: Optional[datetime.datetime] = None, properties: Optional[bool] = False, modified_date: Optional[bool] = False, compression: Optional[Compress] = None):
    q_dict = {'dataset_id': ObjectId(dataset_id), 'site_id': ObjectId(site_id), 'from_date': {}, 'modified_date': {}}
    f_dict = {'_id': 0, 'site_id': 0, 'dataset_id': 0, 'properties': 0, 'modified_date': 0}
    if from_date is not None:
        q_dict['from_date'].update({'$gte': from_date})
    if to_date is not None:
        q_dict['from_date'].update({'$lte': to_date})
    if not q_dict['from_date']:
        q_dict.pop('from_date')
    if from_modified_date is not None:
        q_dict['modified_date'].update({'$gte': from_modified_date})
    if to_modified_date is not None:
        q_dict['modified_date'].update({'$lte': to_modified_date})
    if not q_dict['modified_date']:
        q_dict.pop('modified_date')
    if properties:
        f_dict.pop('properties')
    if modified_date:
        f_dict.pop('modified_date')
    ts_coll = db['time_series_result']

    ts1 = list(ts_coll.find(q_dict, f_dict))

    # df1 = pd.DataFrame(ts1)
    # sio = io.StringIO()
    # df1.to_csv(sio, index=False)
    if compression == 'zstd':
        cctx = zstd.ZstdCompressor(level=1)
        b_ts1 = orjson.dumps(ts1)
        c_obj = cctx.compress(b_ts1)

        return Response(c_obj, media_type='application/zstd')
    else:
        return ts1



# dataset_id = '5f4626eb8319d1e2529a1d85'

# r1 = requests.get('http://tethys-ts.duckdns.org/tethys/data/time_series_result?dataset_id=5f12547a2fae6caf4324a86a&site_id=5f125cff2fae6caf4322baa7&from_date=2020-01-01T00%3A00&compression=zstd')
#
#
# ddtx = zstd.ZstdDecompressor()
#
# j1 = json.loads(ddtx.decompress(r1.content))
#
# to_date = '2020-04-01T00:00'
# from_date = '2020-01-01T00:00'
# dataset_id = '5f112670e07ba4f248b22969'
# site_id = '5f112673e07ba4f248b2296a'
#
#
#
# dataset = {
#     "feature": "atmosphere",
#     "parameter": "precipitation",
#     "method": "sensor_recording",
#     "processing_code": "1",
#     "owner": "ECan",
#     "aggregation_statistic": "cumulative",
#     "frequency_interval": "1H",
#     "utc_offset": "0H",
#     "units": "mm",
#     "license": "https://creativecommons.org/licenses/by/4.0/",
#     "result_type": "time_series"
#   }
#
#
# q_dict = {
#     "feature": "atmosphere",
#     "parameter": "precipitation",
#     "method": "sensor_recording",
#     "processing_code": "1",
#     "owner": "ECan",
#     "aggregation_statistic": "cumulative",
#     "frequency_interval": "1H",
#     "utc_offset": "0H"
#   }
