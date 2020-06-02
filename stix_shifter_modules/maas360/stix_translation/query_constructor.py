from stix_shifter_utils.stix_translation.src.patterns.pattern_objects import ObservationExpression, ComparisonExpression, \
    ComparisonExpressionOperators, ComparisonComparators, Pattern, \
    CombinedComparisonExpression, CombinedObservationExpression, ObservationOperators
from stix_shifter_utils.stix_translation.src.utils.transformers import TimestampToMilliseconds
from stix_shifter_utils.stix_translation.src.json_to_stix import observable
from stix_shifter_utils.stix_translation.src.utils import transformers
import re
import json
import datetime
import copy
from os import path

# Source and destination reference mapping for ip and mac addresses.
# Change the keys to match the data source fields. The value array indicates the possible data type that can come into from field.
# REFERENCE_DATA_TYPES = {"QUERY_FROM_DATE": ["start"],
#                        "QUERY_TO_DATE": ["end"],"OSUser":["%"],"DBUser":"newuser",
#                        "SHOW_ALIASES":["TRUE","FALSE"],"REMOTE_SOURCE":["%"]}
DEFAULT_DAYS_BACK = 2


class QueryStringPatternTranslator:
    # Change comparator values to match with supported data source operators
    comparator_lookup = {
        ComparisonExpressionOperators.And: "AND",
        ComparisonExpressionOperators.Or: "OR",
        #        ComparisonComparators.GreaterThan: ">",
        #        ComparisonComparators.GreaterThanOrEqual: ">=",
        #        ComparisonComparators.LessThan: "<",
        #        ComparisonComparators.LessThanOrEqual: "<=",
        ComparisonComparators.Equal: "=",
        #        ComparisonComparators.NotEqual: "!=",
        #        ComparisonComparators.Like: "LIKE",
        #        ComparisonComparators.In: "IN",
        #        ComparisonComparators.Matches: 'LIKE',
        # ComparisonComparators.IsSubSet: '',
        # ComparisonComparators.IsSuperSet: '',
        ObservationOperators.Or: 'AND',
        # Treat AND's as OR's -- Unsure how two ObsExps wouldn't cancel each other out.
        ObservationOperators.And: 'AND'
    }

    def __init__(self, pattern: Pattern, data_model_mapper):
        self.dmm = data_model_mapper
        self.pattern = pattern
        # Now report_params_passed is a JSON object which is pointing to an array of JSON Objects (report_params_array)
        self.report_params_passed = {}
        self.report_params_array = []
        self.report_params_array_size = 0
        self.translated = self.parse_expression(pattern)
        self.transformers = transformers.get_all_transformers()

    def set_report_params_passed(self, params_array):
        self.report_params_array = params_array
        self.report_params_array_size = len(params_array)
        return

    def transform_report_call_to_json(self, report_call):
        # Convert the report call (string) into an array of JSON.  Note, inside each json obj multiple key/value parmeter are "OR"
        # Where as each key/value parameter from two json objects are "AND"
        # Put quote around key
        # print(report_call)
        regex = r"([a-zA-Z_]+)(\s=)"
        out_str = re.sub(regex, r"'\1' :", report_call, 0)

        # Create the Json structure
        regex1 = r"\(|\)"
        out_str = re.sub(regex1, "", out_str, 0)
        regex2 = r"\sAND\s"
        out_str = "{" + re.sub(regex2, "} AND {", out_str, 0) + "}"
        regex3 = r"START"
        out_str = re.sub(regex3, "} AND {START ", out_str, 0)
        # treat START and STOP parameters too
        regex4 = r"(START|STOP)"
        out_str = re.sub(regex4, r"'\1' : ", out_str, 0)
        regex5 = r"([Z\'\s]+STOP)"
        out_str = re.sub(regex5, r"'} AND {'STOP", out_str, 0)
        regex6 = r"(T|P)\'[\s\:t]+"
        out_str = re.sub(regex6, r"\1' : ", out_str, 0)

        # Finalize the structure -- replace by comma and then it becomes string containing
        # an array of Json objects
        regex7 = r"\sOR|\sAND"
        out_str = re.sub(regex7, r",", out_str, 0)

        # Single quotes have to be replaced by double quotes in order to make it as an Json obj
        regex8 = r"'"
        out_str = "[" + re.sub(regex8, '"', out_str, 0) + "]"

        return json.loads(out_str)


    def build_array_of_maas360_report_params(self, result_array, result_position, current_result_object, params_array, current_position):
        param_list_size = len(params_array)
        if current_result_object is None:
            current_result_object = {}
        if current_position is None:
            current_position = 0
        else:
            current_position = current_position + 1

        if current_position < param_list_size:
            param_json_object = params_array[current_position]
            for param in param_json_object:
                # Keep a copy of current_result_object before any modification from this invocation
                cp_current_result_object = copy.deepcopy(current_result_object)
                # Insert the param in the current_result_object
                if param not in cp_current_result_object:
                    cp_current_result_object[param] = param_json_object[param]
                    if (current_position + 1) < param_list_size:
                        result_array = self.build_array_of_maas360_report_params(result_array, result_position, cp_current_result_object, params_array, current_position)
                    else:
                        result_array.append(cp_current_result_object)
                        result_position = result_position + 1
        return result_array

    def get_report_params(self):
        reports_in_query = []
        for report_param_index in range(self.report_params_array_size):
            self.report_params_passed = self.report_params_array[report_param_index]
            data_category = (self.report_params_passed).get("datacategory", None)
            if(data_category is not None):
                if data_category not in self.REPORT_DEF:
                    report_definitions = None
                else:
                    report_definitions = copy.deepcopy(self.REPORT_DEF[data_category])
            else:
                report_definitions = self.generate_report_definitions()
            # substitute Params
            reports_in_query = self.substitute_params_passed(report_definitions, reports_in_query)

        return reports_in_query
# Report Defintions list

    @staticmethod
    def _format_set(values) -> str:
        gen = values.element_iterator()
        return "({})".format(' OR '.join([QueryStringPatternTranslator._escape_value(value) for value in gen]))

    @staticmethod
    def _format_match(value) -> str:
        raw = QueryStringPatternTranslator._escape_value(value)
        if raw[0] == "^":
            raw = raw[1:]
        else:
            raw = ".*" + raw
        if raw[-1] == "$":
            raw = raw[0:-1]
        else:
            raw = raw + ".*"
        return "\'{}\'".format(raw)

    @staticmethod
    def _format_equality(value) -> str:
        return '\'{}\''.format(value)

    @staticmethod
    def _format_like(value) -> str:
        value = "'%{value}%'".format(value=value)
        return QueryStringPatternTranslator._escape_value(value)

    @staticmethod
    def _escape_value(value, comparator=None) -> str:
        if isinstance(value, str):
            return '{}'.format(value.replace('\\', '\\\\').replace('\"', '\\"').replace('(', '\\(').replace(')', '\\)'))
        else:
            return value

    @staticmethod
    def _negate_comparison(comparison_string):
        return "NOT({})".format(comparison_string)

    @staticmethod
    def _check_value_type(value):
        value = str(value)
        for key, pattern in observable.REGEX.items():
            if key != 'date' and bool(re.search(pattern, value)):
                return key
        return None

    @staticmethod
    def _parse_mapped_fields(self, expression, value, comparator, stix_field, mapped_fields_array):
        comparison_string = ""
        is_reference_value = self._is_reference_value(stix_field)
        # Need to use expression.value to match against regex since the passed-in value has already been formated.
        value_type = self._check_value_type(expression.value) if is_reference_value else None
        mapped_fields_count = 1 if is_reference_value else len(mapped_fields_array)

        for mapped_field in mapped_fields_array:
            if is_reference_value:
                parsed_reference = self._parse_reference(self, stix_field, value_type, mapped_field, value, comparator)
                if not parsed_reference:
                    continue
                comparison_string += parsed_reference
            else:
                comparison_string += "{mapped_field} {comparator} {value}".format(mapped_field=mapped_field, comparator=comparator, value=value)
                #self.report_params_passed[mapped_field] = str(value).replace("'","",10)

            if (mapped_fields_count > 1):
                comparison_string += " OR "
                mapped_fields_count -= 1

        return comparison_string

    @staticmethod
    def _lookup_comparison_operator(self, expression_operator):
        if expression_operator not in self.comparator_lookup:
            raise NotImplementedError(
                "Comparison operator {} unsupported for Dummy connector".format(expression_operator.name))
        return self.comparator_lookup[expression_operator]

    @staticmethod
    def _is_reference_value(stix_field):
        return stix_field == 'src_ref.value' or stix_field == 'dst_ref.value'

    def _parse_expression(self, expression, qualifier=None) -> str:
        if isinstance(expression, ComparisonExpression):  # Base Case
            # Resolve STIX Object Path to a field in the target Data Model
            stix_object, stix_field = expression.object_path.split(':')
            # Multiple data source fields may map to the same STIX Object
            mapped_fields_array = self.dmm.map_field(stix_object, stix_field)
            # Resolve the comparison symbol to use in the query string (usually just ':')
            comparator = self._lookup_comparison_operator(self, expression.comparator)

            if stix_field == 'start' or stix_field == 'end':
                transformer = TimestampToMilliseconds()
                expression.value = transformer.transform(expression.value)

            # Some values are formatted differently based on how they're being compared
            if expression.comparator == ComparisonComparators.Matches:  # needs forward slashes
                value = self._format_match(expression.value)
            # should be (x, y, z, ...)
            elif expression.comparator == ComparisonComparators.In:
                value = self._format_set(expression.value)
            elif expression.comparator == ComparisonComparators.Equal or expression.comparator == ComparisonComparators.NotEqual:
                # Should be in single-quotes
                value = self._format_equality(expression.value)
            # '%' -> '*' wildcard, '_' -> '?' single wildcard
            elif expression.comparator == ComparisonComparators.Like:
                value = self._format_like(expression.value)
            else:
                value = self._escape_value(expression.value)

            comparison_string = self._parse_mapped_fields(self, expression, value, comparator, stix_field,
                                                          mapped_fields_array)
            if (len(mapped_fields_array) > 1 and not self._is_reference_value(stix_field)):
                # More than one data source field maps to the STIX attribute, so group comparisons together.
                grouped_comparison_string = "(" + comparison_string + ")"
                comparison_string = grouped_comparison_string

            if expression.negated:
                comparison_string = self._negate_comparison(comparison_string)
            if qualifier is not None:
                return "{} {}".format(comparison_string, qualifier)
            else:
                return "{}".format(comparison_string)

        elif isinstance(expression, CombinedComparisonExpression):
            operator = self._lookup_comparison_operator(self, expression.operator)
            expression_01 = self._parse_expression(expression.expr1)
            expression_02 = self._parse_expression(expression.expr2)
            if not expression_01 or not expression_02:
                return ''
            if isinstance(expression.expr1, CombinedComparisonExpression):
                expression_01 = "({})".format(expression_01)
            if isinstance(expression.expr2, CombinedComparisonExpression):
                expression_02 = "({})".format(expression_02)
            query_string = "{} {} {}".format(expression_01, operator, expression_02)
            if qualifier is not None:
                return "{} {}".format(query_string, qualifier)
            else:
                return "{}".format(query_string)
        elif isinstance(expression, ObservationExpression):
            return self._parse_expression(expression.comparison_expression, qualifier)
        elif hasattr(expression, 'qualifier') and hasattr(expression, 'observation_expression'):
            if isinstance(expression.observation_expression, CombinedObservationExpression):
                operator = self._lookup_comparison_operator(self, expression.observation_expression.operator)
                expression_01 = self._parse_expression(expression.observation_expression.expr1)
                # qualifier only needs to be passed into the parse expression once since it will be the same for both expressions
                expression_02 = self._parse_expression(expression.observation_expression.expr2, expression.qualifier)
                return "{} {} {}".format(expression_01, operator, expression_02)
            else:
                return self._parse_expression(expression.observation_expression.comparison_expression,
                                              expression.qualifier)
        elif isinstance(expression, CombinedObservationExpression):
            operator = self._lookup_comparison_operator(self, expression.operator)
            expression_01 = self._parse_expression(expression.expr1)
            expression_02 = self._parse_expression(expression.expr2)
            if expression_01 and expression_02:
                return "({}) {} ({})".format(expression_01, operator, expression_02)
            elif expression_01:
                return "{}".format(expression_01)
            elif expression_02:
                return "{}".format(expression_02)
            else:
                return ''
        elif isinstance(expression, Pattern):
            return "{expr}".format(expr=self._parse_expression(expression.expression))
        else:
            raise RuntimeError("Unknown Recursion Case for expression={}, type(expression)={}".format(
                expression, type(expression)))

    def parse_expression(self, pattern: Pattern):
        return self._parse_expression(pattern)


def translate_pattern(pattern: Pattern, data_model_mapping, options):

    # Converting query object to datasource query
    # timerange set to 24 hours for Guardium; timerange is provided in minutes (as delta)
    # RKC pattern: Pattern[ObservationExpression(ComparisonExpression(x-com-guardium:remotesource ComparisonComparators.Equal rkchaudhary.ibm.com)) StartStopQualifier(STARTt'2018-06-01T00:00:00.009Z'STOPt'2019-11-01T01:11:11.009Z', start=t'2018-06-01T00:00:00.009Z', stop=t'2019-11-01T01:11:11.009Z')]
    maas360_query_translator = QueryStringPatternTranslator(pattern, data_model_mapping)
    report_call = maas360_query_translator.translated

    # RKC Report call:  'REMOTE_SOURCE = \'rkchaudhary.ibm.com\' START t\'2018-06-01T00:00:00.009Z\' STOP t\'2019-11-01T01:11:11.009Z\''
    # translate the structure of report_call
    print(report_call)
    json_report_call = maas360_query_translator.transform_report_call_to_json(report_call)
    # RKC: json_report_call: [{'REMOTE_SOURCE': 'rkchaudhary.ibm.com'}, {'START': '2018-06-01T00:00:00.009'}, {'STOP': '2019-11-01T01:11:11.009Z'}]
    result_array = []
    result_position = 0
    output_array = maas360_query_translator.build_array_of_maas360_report_params(result_array, result_position, None, json_report_call, None)

    return output_array
