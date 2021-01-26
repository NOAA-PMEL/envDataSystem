# from envdsys.envdaq.data import Data
# import uuid
import asyncio
import json

from shared.data.datafile import DataFile
from shared.data.message import Message
from django.conf import settings

class DataManager:
    _datafile_map = dict()

    async def send_data(path, data):

        try:
            # message = data["message"]
            message = Message()
            message.from_json(json.dumps(data))
            datafile = DataManager.get_datafile(path)
            if message and datafile:
                await datafile.write_message(message)
            else:
                print(f'DataManager.send_data: no DataFile at {path}')
        except:
            print('DataManager.send_data: data does not contain a message')

    def get_datafile(path):
        
        try:
            return DataManager._datafile_map[path]
        except KeyError:
            return None

    def open_datafile(path):

        if path not in DataManager._datafile_map:
            config = {
                'base_path': path
            }
            DataManager._datafile_map[path] = DataFile(config=config)

        if DataManager._datafile_map[path]:
            DataManager._datafile_map[path].open()

    def close_datafile(path):
        datafile = DataManager.get_datafile(path)
        if datafile:
            datafile.close()
            DataManager._datafile_map.pop(path)
