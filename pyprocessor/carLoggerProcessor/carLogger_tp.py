
'''
Transaction family class for carLogger.
'''

import hashlib
import logging
import time
import sys
import argparse
import json
import pkg_resources

from sawtooth_signing import create_context

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey
from sawtooth_signing import CryptoFactory

LOGGER = logging.getLogger(__name__)

FAMILY_NAME = "carLogger"

def _hash(data):
    '''Compute the SHA-512 hash and return the result as hex characters.'''
    return hashlib.sha512(data).hexdigest()

# Prefix for carLogger is the first six hex digits of SHA-512(TF name).
sw_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]

class VehicleLog:
    def __init__(self, VIN, worker, work_date, work='', brand='', model='', description='', mileage=0, timestamp=''):
        self.VIN = VIN
        self.worker = worker
        self.work_date = work_date
        self.work = work
        self.brand = brand
        self.model = model
        self.description = description
        self.mileage = mileage
        self.timestamp = timestamp

class CarLoggerTransactionHandler(TransactionHandler):
    '''                                                       
    Transaction Processor class for the carLogger transaction family.
                                                              
    This with the validator using the accept/get/set functions.
    It implements functions to add, delete and find transactions.
    '''

    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):
        '''This implements the apply function for this transaction handler.
                                                              
           This function does most of the work for this class by processing
           a single transaction for the carLogger transaction family.
        '''
        LOGGER.debug("start" )
        # Get the payload and extract carLogger-specific information.
        header = transaction.header
        from_key = header.signer_public_key
        payload_list = transaction.payload.decode().split(",")
        operation = payload_list[0]
        VIN = payload_list[1]
        signer = CryptoFactory(create_context('secp256k1')) \
            .new_signer(Secp256k1PrivateKey.from_hex(payload_list[2]))
        work_date = payload_list[3]
        company = signer.get_public_key().as_hex()
        log = VehicleLog(VIN=VIN, worker=company, work_date=work_date)
        # Perform the operation.
        LOGGER.info("Operation = "+ operation)
        if operation == "add":
            work = payload_list[4]
            km_status = payload_list[5]
            description = payload_list[6]
            log.work = work
            log.mileage = km_status
            log.description = description
            log.timestamp = str(time.strftime("%Y-%m-%d %H:%M"))
            self._add(context, log)
        elif operation == "delete":
            work = payload_list[4]
            km_status = payload_list[5]
            description = payload_list[6]
            log.mileage = km_status
            log.description = description
            log.timestamp = str(time.strftime("%Y-%m-%d %H:%M"))
            deleted_work=''
            for number in work.split("|"):
                deleted_work = deleted_work + str(-1*int(number))
            log.work = deleted_work
            self._delete(context, log)
        elif operation == "create":
            brand = payload_list[4]
            model = payload_list[5]
            description = payload_list[6]
            log.mileage = 0
            log.work = '0'
            log.description = description
            log.brand = brand
            log.model = model
            log.timestamp = str(time.strftime("%Y-%m-%d %H:%M"))
            self._create(context,log)
        else:
            LOGGER.info("Unhandled action. Operation should be add, delete, create or history")

    def _add(self, context, log):
        wallet_address = self._get_wallet_address(log.VIN)
        # wallet_address = self._get_wallet_address(company)
        LOGGER.info('Got the serial number {} and the wallet address {} '.format(log.VIN, wallet_address))
        current_entry = context.get_state([wallet_address])
        new_entry = json.dumps(log.__dict__, indent=4)
        LOGGER.info('Current entry{}'.format(current_entry))
        if current_entry == []:
            LOGGER.info('Serial number {} does not exist yet'.format(log.VIN))
        else:
            state_data = str(new_entry).encode('utf-8')
            addresses = context.set_state({wallet_address: state_data})
            if len(addresses) < 1:
                raise InternalError("State Error")

    def _delete(self, context, log):
        wallet_address = self._get_wallet_address(log.VIN)
        # wallet_address = self._get_wallet_address(company)
        LOGGER.info('Got the serial number {} and the wallet address {} '.format(log.VIN, wallet_address))
        current_entry = context.get_state([wallet_address])
        new_entry = json.dumps(log.__dict__, indent=4)
        LOGGER.info('Current entry{}'.format(current_entry))
        if current_entry == []:
            LOGGER.info('Serial number {} does not exist yet'.format(log.VIN))
        else:
            state_data = str(new_entry).encode('utf-8')
            addresses = context.set_state({wallet_address: state_data})
            if len(addresses) < 1:
                raise InternalError("State Error")

    def _create(self, context, log):
        wallet_address = self._get_wallet_address(log.VIN)
        LOGGER.info('Got the serial number {} and the wallet address {} '.format(log.VIN, wallet_address))
        current_entry = context.get_state([wallet_address])
        new_entry = json.dumps(log.__dict__, indent=4)
        LOGGER.info('Current entry{}'.format(current_entry))
        if current_entry != []:
             LOGGER.info('Serial number {} already in use. Try to add data or get different serial number'.format(log.VIN))
        else:
            state_data = str(new_entry).encode('utf-8')
            addresses = context.set_state({wallet_address: state_data})
            if len(addresses) < 1:
                raise InternalError("State Error")


    def _get_wallet_address(self, from_key):
        return _hash(FAMILY_NAME.encode('utf-8'))[0:6] + _hash(from_key.encode('utf-8'))[0:64]

    def getPublicKey(self, from_key):
        context = create_context('secp256k1')
        public_key = context.get_public_key(from_key)
        return public_key

def setup_loggers():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)


def parse_args(args):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '-C', '--connect',
        help='Endpoint for the validator connection')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Increase output sent to stderr')

    try:
        version = pkg_resources.get_distribution(FAMILY_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parser.add_argument(
        '-V', '--version',
        action='version',
        version=(FAMILY_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='print version information')

    return parser.parse_args(args)


def main(args=None):
    '''Entry-point function for the carLogger transaction walletprocessor.'''
    setup_loggers()
    if args is None:
        args = sys.argv[1:]
    opts = parse_args(args)
    try:
        # Register the transaction handler and start it.
        processor = TransactionProcessor(url=opts.connect)

        handler = CarLoggerTransactionHandler(sw_namespace)

        processor.add_handler(handler)

        processor.start()

    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        LOGGER.info(err)
        raise err
    except BaseException as err:
        LOGGER.info(err)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        LOGGER.info(err)

