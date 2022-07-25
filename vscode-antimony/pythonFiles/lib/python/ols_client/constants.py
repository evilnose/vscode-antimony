# -*- coding: utf-8 -*-

import json

import os

__all__ = [
    'CONFIG_DIRECTORY',
    'CONFIG_PATH',
    'BASE_URL',
]

CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.config', 'ols_client')

if not os.path.exists(CONFIG_DIRECTORY):
    os.makedirs(CONFIG_DIRECTORY)

CONFIG_PATH = os.path.join(CONFIG_DIRECTORY, 'config.json')


def write_config(configuration):
    """Helper to write the JSON configuration to a file"""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(configuration, f, indent=2, sort_keys=True)


def get_config():
    """Gets the configuration for this project from the default JSON file, or writes one if it doesn't exist

    :rtype: dict
    """
    if not os.path.exists(CONFIG_PATH):
        write_config({})

    with open(CONFIG_PATH) as f:
        return json.load(f)


config = get_config()
config.setdefault('BASE_URL', 'http://www.ebi.ac.uk/ols')

BASE_URL = config['BASE_URL']
