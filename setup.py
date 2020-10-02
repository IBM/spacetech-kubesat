# Copyright 2020 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages

setup(
    name="kubesat",
    version="0.3",
    url="https://github.com/IBM/spacetech-kubesat",
    packages=find_packages(
        exclude=[
            "test_utils",
            "test_utils.*"
        ]
    ),
    license="Apache License 2.0",
    keywords=[
        "space",
        "reinforcement learning"
    ],
    install_requires=[
        "aiohttp==3.6",
        "fastapi==0.58",
        "asyncio-nats-client==0.10",
        "aiologger==0.5",
        "jsonschema==3.2",
        "redis==3.5",
        "uvicorn==0.11.5",
        "numpy==1.19.0",
        "kubernetes"
    ]
)
