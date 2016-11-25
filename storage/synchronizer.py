import sys
import time
import select
from threading import Thread
import configparser
import psycopg2
import psycopg2.extras

import postgres

class TaskQueue:

    def __init__(self, conn, id):
        self.conn = conn
        self.id = id
        self.listening = False

    def commit(self):
        self.conn.commit()
        print(self.id + ": commit")

    def poll_task(self):
        print(self.id + ": poll_task")
        while True:
            if select.select([self.conn],[],[],60) == ([],[],[]):
                    print("***** SELECT Timeout")
            else:
                self.conn.poll()
                if self.conn.notifies:
                    self.conn.notifies.pop()
                    print(self.id + ": poll_task: succes")
                    return
                else:
                    print(self.id + ": poll_task: fail")

    def listen(self):
        cur = self.conn.cursor()
        cur.execute('LISTEN task_produced;')
        self.commit()
        self.listening = True
        print(self.id + ": listen")

    def unlisten(self):
        cur = self.conn.cursor()
        cur.execute('UNLISTEN task_produced;')
        self.commit()
        self.listening = False
        print(self.id + ": unlisten")

    def notify(self):
        cur = self.conn.cursor()
        cur.execute('NOTIFY task_produced;')
        print(self.id + ": notify")

    def create_tables(self):
        try:
            cur = self.conn.cursor()
            stat = """
                   CREATE TABLE task (id BIGSERIAL, jid BIGINT, aid BIGINT, oid BIGINT, slavetask BOOLEAN DEFAULT TRUE);
               """
            cur.execute(stat)
        except Exception as ex:
            print("Exception", ex)

    def drop_tables(self):
        try:
            cur = self.conn.cursor()
            stat = """
                  DROP TABLE IF EXISTS task CASCADE;
               """
            cur.execute(stat)
        except Exception as ex:
            print("Exception", ex)

    def insert_task(self, jid, aid, oid, slavetask):
        try:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO task (jid, aid, oid, slavetask) VALUES (%s, %s, %s, %s);", [jid, aid, oid, slavetask])
        except Exception as ex:
            print("Exception", ex)


    def push_task(self, payload):
        try:
            print(self.id + ": push_task")
            # cur = self.conn.cursor()
            # cur.execute("INSERT INTO queue (payload) VALUES (%s);", [payload,])
            self.insert_task(99, 100, 101, True)
            self.notify()
            self.commit()
        except Exception as ex:
            print("Exception", ex)

    def pop_task(self):
        try:
            cur = self.conn.cursor()
            stat = """
                DELETE FROM task
                WHERE id = (
                  SELECT id
                  FROM task
                  ORDER BY id
                  FOR UPDATE SKIP LOCKED
                  LIMIT 1
                )
                RETURNING *;
               """
            cur.execute(stat)
            return singlerow(cur)
        except Exception as ex:
            print("Exception", ex)

def singlerow(cur):
    if cur.rowcount == 0:
        return None
    else:
        rows = cur.fetchall()
        print('****'+str(rows[0]))
        return rows[0][0]

def singlevalue(cur):
    # TODO check if it is really a single value
    if cur.rowcount == 0:
        return None
    else:
        rows = cur.fetchall()
        return rows[0][0]


class Producer:

    def __init__(self, id):
        self.id = id
        print('Producer: ' + self.id + ": started")
        pdb = postgres.opendb('../master.local.cfg')
        taskq = TaskQueue(pdb.conn,id)
        taskq.drop_tables()
        taskq.create_tables()
        while True:
            taskq.push_task('dummy')
            taskq.push_task('dummy')
            taskq.commit()
            time.sleep(5)

def run_producer(id):
    prod = Producer(id)


class Consumer:

    def __init__(self, id):
        self.id = id
        pdb = postgres.opendb('../master.local.cfg')
        self.taskq = TaskQueue(pdb.conn,id)
        self.run_loop()


    def process_task(self, task):
        print(self.id + ": PROCESS TASK: "+ str(task))
        time.sleep(1)

    def run_loop(self):
        while True:
            task = self.taskq.pop_task()
            if task is None:
                print(self.id + ": NO TASK")
                self.taskq.commit() # necessary, otherwise consumer may block
                if not self.taskq.listening:
                    self.taskq.listen()
                self.taskq.poll_task()
            else:
                if self.taskq.listening:
                    self.taskq.unlisten()
                self.process_task(task)
    
def run_consumer(id):
    cons = Consumer(id)

if __name__ == '__main__':
    Thread(name='producer', target=run_producer, args=('producer',)).start()
    time.sleep(2)
    Thread(name='consumer-1', target=run_consumer, args=('consumer-1',)).start()
    Thread(name='consumer-2', target=run_consumer, args=('consumer-2',)).start()
