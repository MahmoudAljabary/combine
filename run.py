import storage
import engine

db = storage.opendb("./combine.local.cfg")
db.destroy()
db.create()

cid   = db.add_context("globalctx","Global Context")
jid   = db.add_job(cid,"myfirstjob","This is my first job")
acopy = db.add_activity(jid,"copyjob",(["mykind",["tag1","tag2"]],))
act = db.add_activation(acopy)
o1 = db.add_object(jid,act,"mykind",["tag1","tag2"],"application/text","Hello World 1")
o2 = db.add_object(jid,act,"mykind",["tag1","tag2"],"application/text","Hello World 2")
db.set_activation_graph(act,(o1,),(o2,))
db.add_log(act,"activation_finished","")
#
engine.start("./combine.local.cfg",db)

mod = __import__("modules.copy", fromlist=[''])
mod.run_activation(db,(o1,o2))

j = db.get_job(jid)
print("j.name="+str(j.name()))
o = db.get_object(o1)
print("o.kind="+str(o.kind()))
# o.activity()

# <@ for subset

j.start()
