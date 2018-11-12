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

It reads a YAML file from disk and populates it with the given jinja variables
and loads the yaml variables into memory.
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

  def _init(self, file_name, **jinja_variables):
    """Populates the config object with variables defined in file_name.

    It renders jinja_variables into a YAML file and then loads the file into
    _items

    Args:
      file_name: Name of yaml file to load.
      **jinja_variables: jinja variables to render inside of the yaml file.

    Raises:
      ConfigAlreadyInitializedError: if global config is already initialized.
          You must call `tear_down` before being able to `init` again.
      OSError: if file_name does not exist or is a directory.
      jinja2.exceptions.UndefinedError: if the yaml file requires jinja
          variables that are not included in jinja_variables.
      yaml.scanner.ScannerError: if the yaml file is formatted incorrectly.
    """
    if self._items is not None:
      raise ConfigAlreadyInitializedError()

    if not os.path.isfile(file_name):
      raise IOError('File not found: %s' % file_name)

    # Parse the file path
    directory = os.path.dirname(file_name)
    file_name = os.path.basename(file_name)

    # Load the template
    jinja_loader = jinja2.FileSystemLoader(directory)
    jinja_env = jinja2.Environment(
        loader=jinja_loader, undefined=jinja2.StrictUndefined)
    template = jinja_env.get_template(file_name)

    # Create the hash from the template and variables (set to {} if empty file)
    yaml_text = template.render(jinja_variables)
    self._items = yaml.safe_load(yaml_text) or {}

  def get(self, *keys: Text):
    """Gets the value for given configuration key.

    If there is more than one key passed, each key will be searched
    as a nested property inside the parent key.

    Warning:
      `get` should not be called in any thread until `init` has completed.

    For example:
      Given a YAML file with content:
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
    """Cleanup for config object. Used for testing.

    This is useful if you want to initialize config multiple times.
    """
    self._items = None


class ConfigNotInitializedError(Exception):
  pass


class ConfigAlreadyInitializedError(Exception):
  pass


def init(file_name, **jinja_variables):
  CONFIG._init(file_name, **jinja_variables)  # pylint: disable=protected-access


# Global Config instance
CONFIG = _Config()
