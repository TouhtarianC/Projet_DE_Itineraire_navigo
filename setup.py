import glob

from setuptools import setup, find_packages
import os
from pkg_resources import parse_requirements

# Allow to run setup.py from another directory.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

VERSION = '0.0.6'

# include data files in package
data_files = ['requirements.txt']
# data_files.extend(glob.glob('raft_core/py.typed', recursive=True))
data_files.extend(glob.glob('navigo/app/static/**/*.*', recursive=True))
data_files.extend(glob.glob('navigo/app/templates/*.*', recursive=True))


with open("README.md", "r", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

with open('requirements.txt') as requirements_file:
    install_requires = [str(requirement) for requirement in parse_requirements(requirements_file)]

setup(
    name='navigo',
    version=VERSION,
    url='https://gitlab.tech.orange/toscan/raft-core',
    author='SCA',
    author_email='toscan_team@list2.orange.com',
    description='Raft Core for sdwan & fast raft services',
    long_description=long_description,
    license='Orange',
    python_requires='>=3.10',
    packages=find_packages(
        exclude=(
            '.*',
            'EGG-INFO',
            '*.egg-info',
            '_trial*',
            '*.tests',
            '*.tests.*',
            'tests.*',
            'tests',
            'examples.*',
            'examples*',
            'venv'
            )
        ),
    data_files=data_files,
    include_package_data=True,
    install_requires=install_requires,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'navigo = navigo.app.main:main',
        ]
    }
)
