# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
'''     
Command line interface for the carLogger transaction family.

Parses command line arguments and passes it to the carLoggerClient class
to process.
''' 

import argparse
import getpass
import logging
import os
import sys
import traceback
import pkg_resources

from colorlog import ColoredFormatter

from logger.carLogger_client import CarLoggerClient

DISTRIBUTION_NAME = 'carLogger'

DEFAULT_URL = 'http://sawtooth-rest-api-0:8008'

def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)
    clog.setLevel(logging.DEBUG)
    return clog

def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))

def add_create_parser(subparsers, parent_parser):
    '''Define the "create" command line parsing.'''
    parser = subparsers.add_parser(
        'create',
        help='create new vehicle with unique VIN',
        parents=[parent_parser])

    parser.add_argument(
        'VIN',
        type=str,
        help='new VIN number')

    parser.add_argument(
        'private_key',
        type=str,
        help='ypur private key')

    parser.add_argument(
        'work_date',
        type=str,
        help='date of the work')

    parser.add_argument(
        'brand',
        type=str,
        help='brand of the new car')

    parser.add_argument(
        'model',
        type=str,
        help='model of the new car')

    parser.add_argument(
        'description',
        default='',
        type=str,
        help='any text you want or empty string')

def add_add_parser(subparsers, parent_parser):
    '''Define the "add" command line parsing.'''
    parser = subparsers.add_parser(
        'add',
        help='add work to vehicle with VIN',
        parents=[parent_parser])

    parser.add_argument(
        'VIN',
        type=str,
        help='new VIN number')

    parser.add_argument(
        'private_key',
        type=str,
        help='ypur private key')

    parser.add_argument(
        'work_date',
        type=str,
        help='date of the work')

    parser.add_argument(
        'work',
        type=str,
        help='add work in x|y|z where numbers are repairs by code register')

    parser.add_argument(
        'km_status',
        type=int,
        help='number of kilometers on vehicle counter on day pf work')

    parser.add_argument(
        'description',
        type=str,
        help='any text you want or empty string')

def add_delete_parser(subparsers, parent_parser):
    '''Define the "delete" command line parsing.'''
    parser = subparsers.add_parser(
        'delete',
        help='delete work from vehicle with VIN',
        parents=[parent_parser])

    parser.add_argument(
        'VIN',
        type=str,
        help='VIN number of vehicle')

    parser.add_argument(
        'private_key',
        type=str,
        help='ypur private key')

    parser.add_argument(
        'work_date',
        type=str,
        help='date of the work')

    parser.add_argument(
        'work',
        type=str,
        help='add work in x|y|z where numbers are repairs by code register')

    parser.add_argument(
        'km_status',
        type=int,
        help='number of kilometers on vehicle counter on day pf work')

    parser.add_argument(
        'description',
        type=str,
        help='any text you want or empty string')

def add_history_parser(subparsers, parent_parser):
    '''Define the "history" command line parsing.'''
    parser = subparsers.add_parser(
        'history',
        help='shows history of vehicle',
        parents=[parent_parser])

    parser.add_argument(
        'VIN',
        type=str,
        help='VIN number of vehicle')

def create_parent_parser(prog_name):
    '''Define the -V/--version command line options.'''
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    '''Define the command line parsing for all the options and subcommands.'''
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to manage your car logger',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    subparsers.required = True

    add_create_parser(subparsers, parent_parser)
    add_add_parser(subparsers, parent_parser)
    add_delete_parser(subparsers, parent_parser)
    add_history_parser(subparsers, parent_parser)

    return parser

def do_create(args):
    '''Implements the "create" subcommand by calling the client class.'''
    keyfile = _get_keyfile('jack')
    print("Private key: {}".format(keyfile))
    company = args.private_key
    VIN = args.VIN
    client = CarLoggerClient(baseUrl=DEFAULT_URL, private_key=keyfile, vin=VIN)
    response = client.create(VIN, company, args.work_date, args.brand , args.model,  args.description)
    print("Response: {}".format(response))

def do_add(args):
    '''Implements the "add" subcommand by calling the client class.'''
    company = args.private_key
    keyfile = _get_keyfile('jack')
    VIN = args.VIN
    client = CarLoggerClient(baseUrl=DEFAULT_URL, private_key=keyfile, vin=VIN)
    response = client.add(VIN , company , args.work_date , args.work , args.km_status , args.description)

    print("Response: {}".format(response))

def do_delete(args):
    '''Implements the "add" subcommand by calling the client class.'''
    company = args.private_key
    keyfile = _get_keyfile('jack')
    VIN = args.VIN
    client = CarLoggerClient(baseUrl=DEFAULT_URL, private_key=keyfile, vin=VIN)
    response = client.delete(VIN , company , args.work_date , args.work , args.km_status , args.description)

    print("Response: {}".format(response))

def do_history(args):
    '''Implements the "balance" subcommand by calling the client class.'''
    keyfile = _get_keyfile('jack')
    VIN = args.VIN
    client = CarLoggerClient(baseUrl=DEFAULT_URL, private_key=keyfile, vin=VIN)
    data = client.history()

    if data is not None:
        print("\nHistory of vehicle with VIN: {} has history = {}\n".format(VIN, data.decode()))
    else:
        raise Exception("Data not found: {}".format(args.VIN))

def _get_keyfile(customerName):
    '''Get the private key for a customer.'''
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, customerName)

def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    '''Entry point function for the client CLI.'''
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    verbose_level = 0
    setup_loggers(verbose_level=verbose_level)

    # Get the commands from cli args and call corresponding handlers
    if args.command == 'create':
        do_create(args)
    elif args.command == 'add':
        do_add(args)
    elif args.command == 'delete':
        do_delete(args)
    elif args.command == 'history':
        do_history(args)
    else:
        raise Exception("Invalid command: {}".format(args.command))


def main_wrapper():
    try:
        main()
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

