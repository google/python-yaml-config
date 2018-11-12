# python3
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""yaml_config_loader setup file."""
from setuptools import setup

setup(
    name='yaml-config-loader',
    version='0.1.0',
    description='Yaml configuration loader',
    maintainer='Greg Leeper',
    maintainer_email='gleeper@google.com',
    url='https://github.com/google/python-spanner-orm',
    packages=['config_loader'],
    install_requires=['pyyaml', 'jinja2'])
