from __future__ import print_function

import json

import six
import yaml
import shlex

from st2common.models.system.action import ShellScriptAction
from st2tests.pack_resource import BasePackResourceTestCase

from lib.ansible_base import AnsibleBaseRunner


class TestActionsLibAnsibleBaseRunner(BasePackResourceTestCase):

    # from the ActiveDirectory test of a python action
    def load_yaml(self, filename):
        return yaml.safe_load(self.get_fixture_content(filename))

    def setUp(self):
        super(TestActionsLibAnsibleBaseRunner, self).setUp()

    def test_init(self):
        args = ['ansible_base.py', '--arg1', '--arg2', 'value2', '--arg3=value3']
        ansible_base_runner = AnsibleBaseRunner(args)
        self.assertEqual(ansible_base_runner.args, args[1:])

    def test_censor_extra_vars_key_value(self):
        arg = '--extra-vars=ansible_user=admin ansible_password=secret'

        censored = AnsibleBaseRunner._censor_extra_vars_arg(arg)

        self.assertEqual(
            censored,
            '--extra-vars=ansible_user=admin ansible_password=********'
        )

    def test_censor_extra_vars_json_nested(self):
        extra_vars = {
            'ansible_password': 'secret',
            'nested': [{'db_pass': 'another-secret', 'visible': 'value'}]
        }
        arg = '--extra-vars=' + json.dumps(extra_vars)

        censored = AnsibleBaseRunner._censor_extra_vars_arg(arg)
        censored_vars = json.loads(censored.split('=', 1)[1])

        self.assertEqual(censored_vars['ansible_password'], '********')
        self.assertEqual(censored_vars['nested'][0]['db_pass'], '********')
        self.assertEqual(censored_vars['nested'][0]['visible'], 'value')

    # AnsibleBaseRunner._parse_extra_vars()

    @staticmethod
    def generate_arg(st2_arg, value):
        dummy_action = ShellScriptAction('', '', '')

        # noinspection PyProtectedMember
        arg = dummy_action._get_script_arguments(named_args={st2_arg: value})
        arg = ' '.join(shlex.split(arg))

        return arg

    def check_arg_parse(self, arg_name, test_case, expected_ansible_args):
        args = ['ansible_base.py', self.generate_arg(arg_name, test_case)]
        ansible_base_runner = AnsibleBaseRunner(args)
        self.assertCountEqual(expected_ansible_args, ansible_base_runner.args)

    def test_parse_extra_vars_key_value(self):
        arg = '--extra_vars'
        test = ['key1=value1', 'key2=value2']
        expected = ['--extra-vars=' + ' '.join(test)]

        self.check_arg_parse(arg, test, expected)

    def test_parse_extra_vars_at_file(self):
        arg = '--extra_vars'
        test = ['@/path/to/vars_file.yaml', '@/other/path/vars_file.json']
        expected = ['--extra-vars=' + case for case in test]

        self.check_arg_parse(arg, test, expected)

    def test_parse_extra_vars_at_file_and_key_value(self):
        arg = '--extra_vars'
        test = ['@/path/to/vars_file.yaml', 'key1=value1']
        expected = ['--extra-vars=' + case for case in test]

        self.check_arg_parse(arg, test, expected)

    def extra_vars_yaml_fixture(self, test_name):
        arg = '--extra_vars'
        test_yaml = self.load_yaml('extra_vars.yaml')
        test = next(t for t in test_yaml if t['name'] == test_name)
        case = test['test']
        expected = ['--extra-vars={}'.format(e) for e in test['expected']]
        self.check_arg_parse(arg, case, expected)

    def test_parse_extra_vars_yaml_key_value(self):
        self.extra_vars_yaml_fixture('key_value')

    def test_parse_extra_vars_yaml_at_file(self):
        self.extra_vars_yaml_fixture('at_file')

    def test_parse_extra_vars_yaml_key_value_and_at_file(self):
        self.extra_vars_yaml_fixture('key_value_and_at_file')

    def extra_vars_json_yaml_fixture(self, test_name):
        arg = '--extra_vars'
        test_yaml = self.load_yaml('extra_vars_json.yaml')
        test = next(t for t in test_yaml if t['name'] == test_name)
        case = test['test']
        expected = ['--extra-vars={}'.format(json.dumps(e)) for e in case]
        self.check_arg_parse(arg, case, expected)

    def test_parse_extra_vars_json_yaml_dict(self):
        self.extra_vars_json_yaml_fixture('dict')

    def test_parse_extra_vars_json_yaml_dict_with_list(self):
        self.extra_vars_json_yaml_fixture('dict_with_list')

    def test_parse_extra_vars_json_yaml_dict_dict(self):
        self.extra_vars_json_yaml_fixture('dict_dict')

    def test_parse_extra_vars_json_yaml_dict_multi(self):
        self.extra_vars_json_yaml_fixture('dict_multi')

    def test_parse_extra_vars_json_yaml_dict_with_list_multi(self):
        self.extra_vars_json_yaml_fixture('dict_with_list_multi')

    def test_parse_extra_vars_json_yaml_dict_dict_multi(self):
        self.extra_vars_json_yaml_fixture('dict_dict_multi')

    def extra_vars_complex_yaml_fixture(self, test_name):
        arg = '--extra_vars'
        test_yaml = self.load_yaml('extra_vars_complex.yaml')
        test = next(t for t in test_yaml if t['name'] == test_name)
        case = test['test']
        # this does not preserve the order exactly, but it shows that elements are correctly parsed
        expected = ['--extra-vars={}'.format(e)
                    for e in test['expected'] if isinstance(e, six.string_types)]
        expected.extend(['--extra-vars={}'.format(json.dumps(e))
                         for e in test['expected'] if isinstance(e, dict)])
        self.check_arg_parse(arg, case, expected)

    def test_parse_extra_vars_complex_yaml_arbitrarily_complex(self):
        self.extra_vars_complex_yaml_fixture('arbitrarily_complex')
