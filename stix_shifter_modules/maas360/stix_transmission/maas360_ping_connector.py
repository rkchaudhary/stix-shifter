from stix_shifter_utils.modules.base.stix_transmission.base_ping_connector import BasePingConnector
from stix_shifter_utils.utils.error_response import ErrorResponder
import json

class MaaS360PingConnector(BasePingConnector):
    def __init__(self, api_client):
        self.api_client = api_client

    def ping_connection(self):
        try:
            response = self.api_client.ping_data_source()
            response_code = response.code
            response_txt = response.read().decode('utf-8')
            response_dict = json.loads(response_txt)
            # Construct a response object
            return_obj = dict()
            if response_code == 200:
                return_obj['success'] = True
            else:
                ErrorResponder.fill_error(return_obj, response_dict, ['message'])
            return return_obj
        except Exception as err:
            print('error when pinging datasource {}:'.format(err))
            raise
