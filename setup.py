##==============================================================================
## Copyright 2013 Samuele Santi
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##==============================================================================

from setuptools import setup, find_packages

version = '0.1'

setup(
    name='LulzHistory',
    version=version,
    packages=find_packages(),
    url='http://rshk.github.io/lulz-history',
    license='Apache License, Version 2.0, January 2004',
    author='Samuele Santi',
    author_email='samuele@samuelesanti.com',
    description='',
    long_description='',
    install_requires=[
        'flask',
        'flask-restful',
        'requests',
        'rauth',
    ],
    entry_points={
        'console_scripts': [
            'lulz-history = LulzHistory.server:run_from_command_line',
        ],
    },
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 2.7",
        "Environment :: Web Environment",
    ],
    zip_safe=False,
    include_package_data=True,
)
