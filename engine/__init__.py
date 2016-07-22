from threading import Thread
import logging
import configparser

import storage

class basic_handler:

    def __init__(self,context):
        self.context = context
        # tmp
        self.db = context['db']
        self.activity = context['activity']
        self.job = None
        self.activation = None

    def start_activation(self):
        if not(self.activation is None):
           raise Exception("Start already started activation")
        self.activation = self.db.add_activation(self.activity.aid())
        if self.job is None:
           self.job = self.db.get_job(self.activity.jid())
        self.inobj  = []
        self.outobj = []

    def add2in(self,o):
        self.inobj.append(o)

    def add2out(self,o):
        self.outobj.append(o)

    def create_object(self,kind,tags,content_type,content):
        newobj = self.db.add_object(self.job,self.activation,kind,tags,content_type,content)
        return newobj

    def finish_activation(self):
        self.db.set_activation_graph(self.activation,self.inobj,self.outobj)
        self.activation = None

class activity_handler:

    def __init__(self,db,job,activity):
        self.db = db
        self.job = job
        self.activity = activity
        self.module =  __import__(self.activity.module(), fromlist=[''])
        self.handler = self.module.get_handler({'db':self.db,'job':job,'activity':self.activity,'args':activity.args()})
        logging.info("activity_handler:"+self.activity.module() + " start")

    def handle_object(self,o):
        logging.info(__name__+": handle_object(aid="+str(self.activity.aid())+",oid="+str(o.oid())+") start")
        #
        self.handler.start_activation()
        self.handler.handle_object(o)
        self.handler.finish_activation()
        #
        logging.info(__name__+": handle_object(aid="+str(self.activity.aid())+",oid="+str(o.oid())+") finish")

def run_job(configfile,job):
    db = storage.opendb(configfile)
    active = {}
    while True:
        todo = db.objects_todo(job)
        if len(todo) == 0:
            logging.info("run_job: no more todo")
            break
        else:
            logging.info("run_job: get todo: len="+str(len(todo)))
        for ao in todo:
            a = active.get(ao[0])
            if a is None:
                a = activity_handler(db,job,db.get_activity(ao[0]))
                active[ao[0]] = a
            a.handle_object(db.get_object(ao[1]))
    db.closedb()

def start(configfile):
    """
    Run the Combine engine
    """
    logging.info("Running the Combine Web Harvesting engine!")
    db = storage.opendb(configfile)
    joblist = []
    for job in db.active_jobs():
        jobthread = Thread(name="Job:"+job.name(),target=run_job,args=(configfile,job,))
        joblist.append((job,jobthread))
        jobthread.start()
    # db.closedb() error
