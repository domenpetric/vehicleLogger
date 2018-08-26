
'''
Transaction family class for carLogger.
'''

import hashlib
import logging

from sawtooth_signing import create_context

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor


LOGGER = logging.getLogger(__name__)

FAMILY_NAME = "carLogger"

def _hash(data):
    '''Compute the SHA-512 hash and return the result as hex characters.'''
    return hashlib.sha512(data).hexdigest()

# Prefix for carLogger is the first six hex digits of SHA-512(TF name).
sw_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]

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
        
        # Get the payload and extract carLogger-specific information.
        header = transaction.header
        payload_list = transaction.payload.decode().split(",")
        operation = payload_list[0]
        VIN = payload_list[1]
        private_key = payload_list[2]

        # Get the public key sent from the client.
        company = header.signer_public_key

        # Perform the operation.
        LOGGER.info("Operation = "+ operation)

        if getPublicKey(private_key) != company:
            raise InternalError("Private and public key do not match")
        if operation == "add":

            work_date = payload_list[3]
            work = payload_list[4]
            km_status = payload_list[5]

            self._add(context, VIN, company, work_date,work,km_status)
        elif operation == "delete":
            work_date = payload_list[3]
            work = payload_list[4]
            km_status = payload_list[5]
            deleted_work=''
            for number in work.split("|"):
                deleted_work = deleted_work + str(-1*int(number))
            work = deleted_work
            self._delete(context, VIN, company, work_date, work, km_status)
        elif operation == "create":
            work_date = payload_list[3]
            self._create(context, VIN, company, work_date)
        else:
            LOGGER.info("Unhandled action. Operation should be add, delete, create or history")

    def _add(self, context, VIN, company, work_date,work,km_status):
        wallet_address = self._get_wallet_address(VIN)
        LOGGER.info('Got the serial number {} and the wallet address {} '.format(VIN, wallet_address))
        current_entry = context.get_state([wallet_address])
        new_entry = VIN + ';' + company + ';' + work_date + ';' + work + ';' + str(km_status)
        LOGGER.info('Current entry{}'.format(current_entry))
        if current_entry != []:
            LOGGER.info('Serial number {} does not exist yet'.format(VIN))
        else:
            state_data = str(new_entry).encode('utf-8')
            addresses = context.set_state({wallet_address: state_data})
            if len(addresses) < 1:
                raise InternalError("State Error")

    def _delete(self, context, VIN, company, work_date,work,km_status):
        wallet_address = self._get_wallet_address(VIN)
        LOGGER.info('Got the serial number {} and the wallet address {} '.format(VIN, wallet_address))
        current_entry = context.get_state([wallet_address])
        new_entry = VIN + ';' + company + ';' + work_date + ';' + work + ';' + str(km_status)
        LOGGER.info('Current entry{}'.format(current_entry))
        if current_entry != []:
            LOGGER.info('Serial number {} does not exist yet'.format(VIN))
        else:
            state_data = str(new_entry).encode('utf-8')
            addresses = context.set_state({wallet_address: state_data})
            if len(addresses) < 1:
                raise InternalError("State Error")

    def _create(self, context, VIN, company, work_date):
        wallet_address = self._get_wallet_address(VIN)
        LOGGER.info('Got the serial number {} and the wallet address {} '.format(VIN, wallet_address))
        current_entry = context.get_state([wallet_address])
        new_entry = VIN + ';' + company+';' + work_date + ';0;0'
        LOGGER.info('Current entry{}'.format(current_entry))
        if current_entry != []:
            LOGGER.info('Serial number {} already in use. Try to add data or get different serial number'.format(VIN))
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

def main():
    '''Entry-point function for the carLogger transaction walletprocessor.'''
    setup_loggers()
    try:
        # Register the transaction handler and start it.
        processor = TransactionProcessor(url='tcp://validator:4004')

        handler = CarLoggerTransactionHandler(sw_namespace)

        processor.add_handler(handler)

        processor.start()

    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

