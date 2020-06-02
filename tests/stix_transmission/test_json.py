import json

def load_json(self, json_str={}):
    connection_dict = json.load(json_str)
    print(connection_dict)

if __name__ == "__main__":
    json_str = '{"host":"python-flask-docker-git-sample-app2.apps.rkc-openshift.os.fyre.ibm.com", "port":"443"}'
    load_json(json_str)