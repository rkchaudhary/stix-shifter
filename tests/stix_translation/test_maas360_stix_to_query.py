from stix_shifter.stix_translation import stix_translation
import unittest

translation = stix_translation.StixTranslation()


class TestStixToQuery(unittest.TestCase):
    """
    class to perform unit test case guardium translate query
    """

    def _test_query_assertions(self, query, queries):
        """
        to assert the each query in the list against expected result
        """
        self.assertIsInstance(query, dict)
        self.assertIsInstance(query['queries'], list)
        for index, each_query in enumerate(query.get('queries'), start=0):
            print(each_query)
            print("---------")
            #self.assertEqual(each_query, queries[index])
            self.assertEqual(True, each_query in queries)

    def test_pattern_translation_basic(self):
        stix_pattern = "[email-addr:value = 'rkchaudhary@ibm.com'] AND [x-com-ibm-mdm-devices:device_id = 'ApplF2LV13JPHFM2'] START t'2018-06-01T00:00:00.009Z' STOP t'2019-11-01T01:11:11.009Z'"
        query = translation.translate('maas360', 'query', '{}', stix_pattern)
        print(query)

    def test_pattern_translation_twoOps(self):
        stix_pattern = "[email-addr:value = 'rkchaudhary@ibm.com' OR user-account:user_id = 'rkchaudhary'] START t'2018-06-01T00:00:00.009Z' STOP t'2019-11-01T01:11:11.009Z'"
        query = translation.translate('maas360', 'query', '{}', stix_pattern)
        print(query)

    def test_pattern_translation_signle_custom(self):
        stix_pattern = "[x-com-ibm-mdm-devices:device_id = 'ApplF2LV13JPHFM2'] START t'2018-06-01T00:00:00.009Z' STOP t'2019-11-01T01:11:11.009Z'"
        query = translation.translate('maas360', 'query', '{}', stix_pattern)
        print(query)