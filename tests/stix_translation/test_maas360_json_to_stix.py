import json
import unittest
from stix_shifter_utils.stix_translation.src.utils import transformers
from stix_shifter_utils.stix_translation.src.json_to_stix import json_to_stix_translator
from stix_shifter_modules.maas360.entry_point import EntryPoint


entry_point = EntryPoint()
map_file = open(entry_point.get_results_translator().default_mapping_file_path).read()
map_data = json.loads(map_file)
data_source = {
    "type": "identity",
    "id": "identity--3532c56d-ga72-58be-a2ad-7a56f4c9c6d7",
    "name": "maas360",
    "identity_class": "events"
}
options = {}


class TestMaaS360APIResultsToStix(unittest.TestCase):
    """
    class to perform unit test case for azure_sentinel translate results
    """

    @staticmethod
    def get_first(itr, constraint):
        """
        return the obj in the itr if constraint is true
        """
        return next(
            (obj for obj in itr if constraint(obj)),
            None
        )

    @staticmethod
    def get_first_of_type(itr, typ):
        """
        to check whether the object belongs to respective stix object
        """
        return TestMaaS360APIResultsToStix.get_first(itr, lambda o: isinstance(o, dict) and o.get('type') == typ)

    def test_common_prop(self):
        """
        to test the common stix object properties
        """
        data = {
                    'fl_user_id': 'rkchaudhary', #common prop
                    'fl_email_add': 'rkchaudhary@ibm.com', #common prop
                    'fl_device_id': 'ApplF2LV13JPHFM2', #custom prop
                    'fl_imei': 'b73e5ba8-34d5-495a-9901-06bdb84cf13e', #custom prop
                    'fl_device_platform': 'iOS', #custom prop
                    #'createdDateTime': '2019-12-04T09:38:05.2024952Z', #custom prop
                    'fl_managed_status': 'Enrolled', #custom prop
                    #'last_reported': '2019-12-04T09:37:54.6939357Z', #custom prop
                    #'eventDateTime': '2019-12-04T09:37:54.6939357Z',
                    #'lastModifiedDateTime': '2019-12-04T09:38:06.7571701Z' #custom prop
                }
        result_bundle = json_to_stix_translator.convert_to_stix(
            data_source, map_data, [data], transformers.get_all_transformers(), options)
        assert result_bundle['type'] == 'bundle'
        result_bundle_objects = result_bundle['objects']

        result_bundle_identity = result_bundle_objects[0]
        assert result_bundle_identity['type'] == data_source['type']
        assert result_bundle_identity['id'] == data_source['id']
        assert result_bundle_identity['name'] == data_source['name']
        assert result_bundle_identity['identity_class'] == data_source['identity_class']

        observed_data = result_bundle_objects[1]
        assert observed_data['id'] is not None
        assert observed_data['type'] == "observed-data"
        assert observed_data['created_by_ref'] == result_bundle_identity['id']

        assert observed_data['modified'] is not None
        assert observed_data['created'] is not None

        print(observed_data)

