# python3
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for config_loader.config."""
import abc
import contextlib
import tempfile

from absl.testing import absltest
import jinja2
import yaml

from yaml_config_loader import config


@contextlib.contextmanager
def config_file(content):
  with tempfile.NamedTemporaryFile() as temp:
    temp.write(bytes(content, 'utf-8'))
    temp.flush()
    yield temp.name


class TestGlobalConfig(abc.ABC):
  """Test Global Config."""

  @abc.abstractmethod
  def config_init(self, contents, **jinja_variables):
    pass

  def tearDown(self):
    config.CONFIG._tear_down()

  def test_init_works_for_valid_yaml(self):
    self.config_init('KEY: VAL')
    self.assertEqual(config.CONFIG.get(), {'KEY': 'VAL'})

  def test_init_works_for_valid_multiline_yaml(self):
    self.config_init('KEYS:\n  KEY1: VAL1\n  KEY2: VAL2')
    self.assertEqual(config.CONFIG.get(),
                     {'KEYS': {
                         'KEY1': 'VAL1',
                         'KEY2': 'VAL2'
                     }})

  def test_init_renders_jinja_variables_in_value(self):
    self.config_init('key: {{ jinja_var }}', jinja_var='multiple word value')
    self.assertEqual(config.CONFIG.get(), {'key': 'multiple word value'})

  def test_init_renders_jinja_variables_in_keys(self):
    self.config_init(
        '{{ jinja_one }}: {{ jinja_two }}', jinja_one='key', jinja_two='val')
    self.assertEqual(config.CONFIG.get(), {'key': 'val'})

  def test_init_fails_on_jinja_error(self):
    with self.assertRaises(jinja2.exceptions.UndefinedError):
      self.config_init('{{ jinja_one }}: {{ jinja_two }}', jinja_one='key')

  def test_init_ignores_extra_jinja_args(self):
    self.config_init(
        '{{ jinja_one }}: {{ jinja_two }}',
        jinja_one='key',
        jinja_two='val',
        jinja_three='extra')
    self.assertEqual(config.CONFIG.get(), {'key': 'val'})

  def test_init_fails_for_invalid_yaml(self):
    with self.assertRaises(yaml.scanner.ScannerError):
      self.config_init('invalid : yaml : file')

  def test_init_fails_for_invalid_file_name(self):
    with self.assertRaises(IOError):
      config.init_from_file('non_existant_file.yaml')

  def test_init_multiple_times(self):
    self.config_init('KEY: VAL')
    with self.assertRaises(config.ConfigAlreadyInitializedError):
      self.config_init('KEY: VAL')

  def test_init_loads_empty_string(self):
    self.config_init('')
    self.assertEqual(config.CONFIG.get(), {})

  def test_init_recognizes_empty_string_loaded(self):
    self.config_init('')
    with self.assertRaises(config.ConfigAlreadyInitializedError):
      self.config_init('')


class TestGlobalConfigWithInit(TestGlobalConfig, absltest.TestCase):

  def config_init(self, contents, **jinja_variables):
    config.init(contents, **jinja_variables)


class TestGlobalConfigWithInitFromFile(TestGlobalConfig, absltest.TestCase):

  def config_init(self, contents, **jinja_variables):
    with config_file(contents) as file_name:
      config.init_from_file(file_name, **jinja_variables)


class ConfigTest(absltest.TestCase):
  """Test Config."""

  def setUp(self):
    self._conf = config._Config()

  def test_get_before_init_raises_error(self):
    self.assertIsNone(self._conf._items)
    with self.assertRaises(config.ConfigNotInitializedError):
      self._conf.get('KEY')

  def test_get_key_not_exist(self):
    self._conf._items = {}
    with self.assertRaises(ValueError):
      self._conf.get('BAD_KEY')

  def test_get_key_no_arg(self):
    self._conf._items = {'KEY': 'VAL'}

    self.assertEqual({'KEY': 'VAL'}, self._conf.get())

  def test_get_key(self):
    self._conf._items = {'KEY': 'VAL'}

    self.assertEqual('VAL', self._conf.get('KEY'))

  def test_get_nested_key(self):
    self._conf._items = {'PARENT': {'CHILD': 'VAL'}}

    self.assertEqual('VAL', self._conf.get('PARENT', 'CHILD'))

  def test_get_partial_key(self):
    self._conf._items = {'PARENT': {'CHILD': 'VAL'}}

    self.assertEqual({'CHILD': 'VAL'}, self._conf.get('PARENT'))

  def test_get_key_immutable(self):
    self._conf._items = {'PARENT': {'CHILD': 'VAL'}}

    # modify returned dictionary
    self._conf.get('PARENT')['CHILD'] = 'INJECTING_MY_VAL'

    # verify original config is unchanged
    self.assertEqual('VAL', self._conf.get('PARENT', 'CHILD'))
