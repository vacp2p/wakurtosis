#!/usr/bin/env python3

""" Dependencies """
import os, sys, logging, json, argparse

""" Globals """
G_APP_NAME = 'MakeWLSTargets'
G_LOG_LEVEL = 'INFO'
G_LOGGER = None
G_ENCLAVE_DUMP_PATH = 'enclave.dump'

""" Custom logging formatter """
class CustomFormatter(logging.Formatter):
    
    # Set different formats for every logging level
    time_name_stamp = "[%(asctime)s.%(msecs)03d] [" + G_APP_NAME + "]"
    FORMATS = {
        logging.ERROR: time_name_stamp + " ERROR in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.WARNING: time_name_stamp + " WARNING - %(msg)s",
        logging.CRITICAL: time_name_stamp + " CRITICAL in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.INFO:  time_name_stamp + " %(msg)s",
        logging.DEBUG: time_name_stamp + " %(funcName)s() %(msg)s",
        'DEFAULT': time_name_stamp + " %(msg)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        formatter = logging.Formatter(log_fmt, '%d-%m-%Y %H:%M:%S')
        return formatter.format(record)

def parse_targets(enclave_dump_path, waku_port=8545):

    targets = []

    G_LOGGER.info('Extracting Waku node addresses from Kurtosus enclance dump in %s' %enclave_dump_path)            

    for path_obj in os.walk(enclave_dump_path):
        if 'waku_' in path_obj[0]:
            with open(path_obj[0] + '/spec.json', "r") as read_file:
                spec_obj = json.load(read_file)
                network_settings = spec_obj['Config']['Labels']
                waku_address = network_settings['com.kurtosistech.private-ip']
                
                if len(waku_address) == 0:
                    G_LOGGER.info('No targets found in %s' %(path_obj[0]))
                else:
                    targets.append('%s:%s' %(waku_address, waku_port))

    G_LOGGER.info('Parsed %d Waku nodes' %len(targets))            

    return targets

def main():

    global G_LOGGER
    
    """ Init Logging """
    G_LOGGER = logging.getLogger(G_APP_NAME)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    G_LOGGER.addHandler(handler)
    
    G_LOGGER.info('Started')
    
    """ Parse args """
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--enclave', help='Wakurtosis enclave name', action='store_true', default='wakurtosis')
    args = parser.parse_args()

    """ Dump enclave info """
    # Delete previous dump if any
    os.system('rm -rf %s' %G_ENCLAVE_DUMP_PATH)
    # Generate new dump
    os.system('kurtosis enclave dump %s %s' %(args.enclave, G_ENCLAVE_DUMP_PATH))

    """ Parse targets """
    targets = parse_targets(G_ENCLAVE_DUMP_PATH)
    if len(targets) == 0:
        G_LOGGER.error('Cannot find valid targets. Aborting.')
        sys.exit(1)

    """ Export targets """
    with open('targets.json', 'w') as f:
        json.dump(targets, f)
    
    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
