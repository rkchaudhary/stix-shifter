from stix_shifter_utils.utils.entry_point_base import EntryPointBase
from .stix_transmission.maas360_api_client import APIClient
from .stix_transmission.maas360_delete_connector import MaaS360DeleteConnector
from .stix_transmission.maas360_ping_connector import MaaS360PingConnector
from .stix_transmission.maas360_query_connector import MaaS360QueryConnector
from .stix_transmission.maas360_results_connector import MaaS360ResultsConnector
from .stix_transmission.maas360_status_connector import MaaS360StatusConnector


class EntryPoint(EntryPointBase):

    # python main.py translate async_dummy query '{}' "[ipv4-addr:value = '127.0.0.1']"
    # python main.py translate async_dummy:dialect1 query '{}' "[ipv4-addr:value = '127.0.0.1']"
    # python main.py translate async_dummy:dialect2 query '{}' "[ipv4-addr:value = '127.0.0.1']"

    def __init__(self, connection={}, configuration={}, options={}):
        super().__init__(options)
        if connection:
            api_client = APIClient(connection, configuration)
            ping_connector = MaaS360PingConnector(api_client)
            query_connector = MaaS360QueryConnector(api_client)
            status_connector = MaaS360StatusConnector(api_client)
            results_connector = MaaS360ResultsConnector(api_client)
            delete_connector = MaaS360DeleteConnector(api_client)

            self.set_ping_connector(ping_connector)
            self.set_query_connector(query_connector)
            self.set_status_connector(status_connector)
            self.set_results_connector(results_connector)
            self.set_delete_connector(delete_connector)
        else:
            self.setup_translation_simple('default')