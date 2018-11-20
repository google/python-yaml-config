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
"""This module provides generic configuration handling.

It reads a yaml file from disk or yaml string, populates the yaml with the given
jinja variables, and loads the yaml variables into memory.
"""
import copy
import os
from typing import Text

import jinja2
import yaml


class _Config(object):
  """Config class to read configurations."""

  def __init__(self):
    self._items = None

  def _init(self, yaml_string, **jinja_variables):
    """Populates the config object with variables defined in yaml_string.

    It renders jinja_variables into a YAML string and then loads the yaml into
    _items

    Args:
      yaml_string: yaml text to load.
      **jinja_variables: jinja variables to render inside of the yaml text.

    Raises:
      ConfigAlreadyInitializedError: if global config is already initialized.
          You must call `tear_down` before being able to `init` again.
      jinja2.exceptions.UndefinedError: if the yaml text requires jinja
          variables that are not included in jinja_variables.
      yaml.scanner.ScannerError: if the yaml text is formatted incorrectly.
    """
    if self._items is not None:
      raise ConfigAlreadyInitializedError()

    # Load the template
    template = jinja2.Environment(
        loader=jinja2.BaseLoader,
        undefined=jinja2.StrictUndefined).from_string(yaml_string)

    # Create the hash from the template and variables (set to {} if empty yaml)
    yaml_text = template.render(jinja_variables)
    self._items = yaml.safe_load(yaml_text) or {}

  def has_key(self, *keys: Text):
    """Returns a boolean indicating whether the key is defined in the config."""
    try:
      self.get(*keys)
      return True
    except ValueError:
      return False

  def get(self, *keys: Text):
    """Gets the value for given configuration key.

    If there is more than one key passed, each key will be searched
    as a nested property inside the parent key.

    Warning:
      `get` should not be called in any thread until `init` has completed.

    For example:
      Given a YAML string with content:
      PARENT:
        CHILD: val

      `get('PARENT', 'CHILD')` would return `val`.
      `get('PARENT')` would return the dictionary {'CHILD': 'val'}
      `get()` would return the full dictionary {'PARENT', {'CHILD': 'val'}}

    Args:
      *keys: keys tuple

    Returns:
      Configuration value corresponding to keys.

    Raises:
      ValueError: if key does not exists.
      ConfigNotInitializedError: if the global config hasn't been
          initialized yet.
    """
    if self._items is None:
      raise ConfigNotInitializedError()

    value = self._items
    for key in keys:
      if key not in value:
        raise ValueError('{} is not found in config.'.format(key))

      value = value.get(key)

    return copy.deepcopy(value)

  def _tear_down(self):
    """Cleanup for config object.

    Used for testing.

    This is useful if you want to initialize config multiple times.
    """
    self._items = None


class ConfigNotInitializedError(Exception):
  pass


class ConfigAlreadyInitializedError(Exception):
  pass


def init_from_file(file_name, **jinja_variables):
  """Populates global config with contents of file_name.

  Args:
    file_name: Name of file with yaml config.
    **jinja_variables: Variables to render in yaml config.

  Raises:
    OSError: if file_name does not exist or is a directory.
    ConfigAlreadyInitializedError: if global config is already initialized.
        You must call `tear_down` before being able to `init` again.
    jinja2.exceptions.UndefinedError: if the yaml file requires jinja
        variables that are not included in jinja_variables.
    yaml.scanner.ScannerError: if the yaml file is formatted incorrectly.
  """
  if not os.path.isfile(file_name):
    raise IOError('File not found: %s' % file_name)

  with open(file_name, 'r') as f:
    contents = ''.join(f.readlines())

  init(contents, **jinja_variables)


def init(yaml_string, **jinja_variables):
  """Initialize the global config from a yaml string."""
  CONFIG._init(yaml_string, **jinja_variables)  # pylint: disable=protected-access


# Global Config instance
CONFIG = _Config()
