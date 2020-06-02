from stix_shifter_utils.stix_transmission.utils.RestApiClient import RestApiClient


class APIClient():
    PING_ENDPOINT = '/monitor.htm'
    QUERY_ENDPOINT = '/query'
    RESULT_ENDPOINT = '/results/'
    STATUS_ENDPOINT = '/status/'
    DELETE_QUERY_ENDPOINT = '/delete'
    PING_TIMEOUT_IN_SECONDS = 10

    def __init__(self, connection, configuration):
        # Uncomment when implementing data source API client.
        self.connection = connection
        self.configuration = configuration

        self.endpoint_start = '/api'
        auth = configuration.get('auth')
        headers = dict()
        headers['X-Auth-Token'] = auth.get('token')
        self.host_port = connection.get('host')
        url_modifier_function = self.url_modifier_function

        # Setup proxy datasource if needed
        self.setup_proxy_datasource()

        self.client = RestApiClient(connection.get('host'),
                                    None,
                                    connection.get('cert', None),
                                    headers,
                                    url_modifier_function,
                                    cert_verify=connection.get('cert_verify', False)
                                    )

    # Placeholder client to allow dummy transmission calls.
    # Remove when implementing data source API client.
    # self.client = "data source API client"

    def url_modifier_function(self, server_ip, endpoint, actual_headers):
        return "http://" + server_ip + endpoint

    def ping_data_source(self):
        endpoint = self.endpoint_start + self.PING_ENDPOINT
        return self.client.call_api(endpoint, "GET")

    def create_search(self, query_expression):

        headers = dict()
        headers['Content-type'] = 'application/json'
        endpoint = self.endpoint_start + self.QUERY_ENDPOINT
        data = query_expression
        # data = data.encode('utf-8')
        return self.client.call_api(endpoint, 'POST', headers, data=data)

    def get_search_status(self, search_id):
        endpoint = self.endpoint_start + self.STATUS_ENDPOINT + search_id

        return self.client.call_api(endpoint, "GET")

    def get_search_results(self, search_id, range_start=None, range_end=None):
        headers = dict()
        headers['Accept'] = 'application/json'
        endpoint = self.endpoint_start + self.RESULT_ENDPOINT + search_id
        params = dict()
        params['output'] = 'json'
        params['stats'] = '1'
        params['start'] = range_start
        params['count'] = range_end - range_start
        return self.client.call_api(endpoint, 'GET', headers, urldata=params)

    def delete_search(self, search_id):
        # Optional since this may not be supported by the data source API
        # Delete the search
        return {"code": 200, "success": True}

    def setup_proxy_datasource(self):
        proxy = self.connection.get('proxy')
        if proxy is not None:
            proxy_url = proxy.get('url')
            proxy_auth = proxy.get('auth')
            if (proxy_url is not None and proxy_auth is not None):
                self.headers['proxy'] = proxy_url
                self.headers['proxy-authorization'] = 'Basic ' + proxy_auth
            if proxy.get('x_forward_proxy', None) is not None:
                self.headers['x-forward-url'] = 'https://' + \
                                                self.host_port + '/'  # + endpoint, is set by 'add_endpoint_to_url_header'
                host_port = proxy.get('x_forward_proxy')
                if proxy.get('x_forward_proxy_auth', None) is not None:
                    self.headers['x-forward-auth'] = proxy.get(
                        'x_forward_proxy_auth')
                self.headers['user-agent'] = 'UDS'
