import sys
import os.path
import configparser
import argparse
import logging
import json
import storage
import engine
from engine.configurator import Configurator
from engine import Engine


JOBNAME = 'bearings-crawl'

# JSON_CONFIG = './input/book_crawl.json'
JSON_CONFIG = './input/bearing_crawl.json'
# JSON_CONFIG = './input/judged.json'
# JSON_CONFIG = './input/abf_bearing_crawl.json'
# JSON_CONFIG = './input/btshop_bearing_crawl.json'


def open_bearings_scenario(configfile):
    logging.info("Open new Bearings Schedule")
    combine_engine = Engine(configfile)
    job = combine_engine.db.get_job(name=JOBNAME)
    module = 'modules.abf_extract_fields'
    print('RESETTING module: ' + module)
    activities = job.activities(module)
    combine_engine.scheduler.reset_activity(next(activities), job)
    combine_engine.scheduler.commit()
    combine_engine.run()
    combine_engine.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', metavar="configfile",
                        default='./master.local.cfg',
                        help="specify path of the config file", required=False)
    parser.add_argument('-l', '--logfile', metavar="logfile",
                        default='./combine.log',
                        help="specify path of the log file", required=False)
    parser.add_argument("--slave", action="store_true",
                        help="always run as slave")
    args = vars(parser.parse_args())
    configfile = args['config']
    #
    config = configparser.RawConfigParser()
    config.read(configfile)
    if config.has_option('scheduler', 'mode'):
        is_start = (config.get('scheduler', 'mode') == 'start')
    else:
        is_start = True
    #
    logfile = args['logfile']
    #
    logging.basicConfig(filename=logfile, level=logging.INFO)
    #
    if not os.path.isfile(configfile):
        print("Bad configfile: "+configfile)
        sys.exit()
    #
    if args['slave']:
        combine_engine = Engine(configfile)
        combine_engine.run()
        combine_engine.stop()
    else:
        if is_start:
            configurator = Configurator(configfile, initialize=True)
            configurator.load_configuration(JSON_CONFIG)
            configurator.close()
        #
        combine_engine = Engine(configfile)
        combine_engine.run()
        combine_engine.stop()

        # storage.postgres.test_listener(configfile)
        # load_scenario(configfile, './bearing_crawl.json')
        # open_bearings_scenario(configfile)
