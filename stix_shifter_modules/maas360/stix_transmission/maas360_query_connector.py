from stix_shifter_utils.modules.base.stix_transmission.base_query_connector import BaseQueryConnector
from stix_shifter_utils.utils.error_response import ErrorResponder
import json

class MaaS360QueryConnector(BaseQueryConnector):
    def __init__(self, api_client):
        self.api_client = api_client

    def create_query_connection(self, query):
        try:
            response = self.api_client.create_search(query)
            response_code = response.code
            response_txt = response.read().decode('utf-8')
            response_dict = json.loads(response_txt)
            # Construct a response object
            return_obj = dict()
            if response_code == 200:
                return_obj['search_id'] = response_dict['search_id']
                return_obj['success'] = response_dict['success']
            else:
                ErrorResponder.fill_error(return_obj, response_dict, ['message'])
            return return_obj
        except Exception as err:
            print('error when creating search: {}'.format(err))
            raise
