import sys
import os.path
import argparse
import logging
import storage
import engine


JOBNAME = 'bearings-crawl'


def create_bearings_schedule(configfile):
    logging.info("Create new Bearings Schedule")
    db = storage.opendb(configfile)
    if True:
        # initialize a fresh database
        db.destroy()
        db.create()
    context = db.add_context(JOBNAME, "Bearing Crawl Context")
    job = db.add_job(context, JOBNAME, "Bearings Crawl Job")
    db.add_activity(job,
                    "modules.seed_json",
                    "--kind=rfc_entity,--tag=",
                    ([{'kind': 'rfc_entity_seed'}, ]),
                    ([{'kind': 'rfc_entity'}, ]))
    db.add_activity(job,
                    "modules.abf_detail_url", "",
                    ([{'kind': 'rfc_entity'}, ]),
                    ([{'kind': 'abf_detail_url'}, ]))
    db.add_activity(job,
                    "modules.abf_fetch", "",
                    ([{'kind': "abf_detail_url"}, ]),
                    ([{'kind': 'abf_detail_page'}, ]))
    db.add_activity(job,
                    "modules.abf_extract_fields", "",
                    ([{'kind': "abf_detail_page"}, ]),
                    ([{'kind': 'abf_entity'}, ]))
    db.add_activity(job,
                    "modules.rfc-x-abf-cmp", "",
                    ([{'kind': "rfc_entity"}, {'kind': "abf_entity"}]),
                    ([{'kind': 'UNKOWN'}, ]))
    db.add_seed_data(job, [engine.LwObject({'kind': 'rfc_entity_seed', 'tags': []}, {'Content-Type': 'text/html', 'encoding': 'utf-8'}, "./data/rfc.in.test.json", None), ])
    job.start()
    db.closedb()


def open_bearings_schedule(configfile):
    logging.info("Open new Bearings Schedule")
    db = storage.opendb(configfile)
    job = db.get_job(name=JOBNAME)
    job.delete_objects(activity="modules.abf_extract_fields")

logging.basicConfig(filename='combine.log', level=logging.INFO)
# logging.basicConfig(stream=sys.stdout, level=logging.INFO)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', metavar="configfile",  default='./combine.local.cfg', help="specify path of the confi file", required=False)
    args = vars(parser.parse_args())
    configfile = args['config']
    if not os.path.isfile(configfile):
        print("Bad configfile: "+configfile)
        sys.exit()
    #
    create_bearings_schedule(configfile)
    # open_bearings_schedule(configfile)
    engine.start(configfile)
