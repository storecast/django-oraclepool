from django.db import models, connection, backend, load_backend

from django.core import signals
from django.db import close_connection
from django.core.handlers.base import BaseHandler

from django.db.backends.oracle.base import DatabaseWrapper as OracleDatabaseWrapper
from oraclepool.base import DatabaseWrapper as PoolDatabaseWrapper
from django.core.paginator import Paginator
from django.test import TestCase
from datetime import datetime
from settings import DATABASES, get_settings_dict
from random import randint

class OneTable(models.Model):
    b = models.CharField(max_length=100)
    c = models.CharField(default=u'test', max_length=10)
    
    def __repr__(self):
        return '<OneTable %s: %s, %s>' % (self.pk, self.b, self.c)


class TwoTable(models.Model):
    a = models.ForeignKey(OneTable)
    b = models.CharField(max_length=100)
    
    def __repr__(self):
        return '<TwoTable %s: %s>' % (self.pk, self.b)

class PerformanceTestCase(TestCase):
    """ Runs a set of inserts and queries via each oracle
        connector and times the overall execution to indicate
        pool connection creation time differences
     """

    conncount = 32 # Apache2 default is 2 processes with 64 threads = 128
    querycount = 30  # multiply by five for number of queries
    conns = {'oracle':[],
             'oraclepool':[]}
    rows = {'oracle':0,
            'oraclepool':0}
    newconns = 1
    start = {}
    end = {}
    time = {}
    
    def resetTimer(self):
        self.start = {'oracle':[],
                      'oraclepool':[]}
        self.end = {'oracle':[],
                    'oraclepool':[]}
        self.time = {'oracle':0,
                     'oraclepool':0}
        
    
    def testTimed(self):
        """ Main test sequence is run here other funcs are helpers
            for those timed tests
        """
        fixtures = ['paging.json']
        self.setup_conns()
        conncount = {}
        for i in range(0,2):
            self.newconns = i
            self.resetTimer()
            print "\n-----------------------------------------------"            
            if i == 0:
                print 'Run query speed test set using a single connection'
            else:
                print 'Run test set using real world multiple process thread held connections'
            print "-----------------------------------------------\n"
            
            for engine in ['oracle','oraclepool']:
                self.engine = engine
                DATABASES['default'] = DATABASES[engine]
                self.addData()
                self.queryData()
                OneTable.objects.all().delete()
                j = 0
                for start in self.start[engine]:
                    delta = self.end[engine][j] - start
                    self.time[engine] += delta.microseconds
                    j += 1
                conncount[engine] = 1 - i
                for conn in self.conns['oracle']:
                    if conn:
                        conncount[engine] +=1
                print '%s engine took %s microsecs with %s connections' % (engine,
                                                               self.time[engine],
                                                               conncount[engine])
            self.assertEquals(self.rows['oracle'],self.rows['oraclepool'])
            print 'For each engine ran %d queries' % int(10 + (self.querycount * 5))
            speed = int(100*self.time['oracle']/self.time['oraclepool'])
            if speed > 100:
                adj = 'faster than'
            else:
                adj = 'of the speed of'
            print 'Oraclepool is %d percent %s Oracle engine' % (speed,adj)

    def addData(self):
        self.dummy_request_start()
        OneTable(b='here').save()
        OneTable(b='is').save()
        OneTable(b='some').save()
        OneTable(b='test').save()
        OneTable(b='data').save()
        OneTable(b='for').save()
        OneTable(b='querying').save()
        OneTable(b='fgh').save()
        OneTable(b='fgh').save()
        OneTable(b='ijk').save()
        self.dummy_request_end()        

    def queryData(self):
        """ Do a lot of queries """
        for engine in ['oraclepool','oracle']:
            self.engine = engine
            for i in range(0, self.querycount):
                self.runQuery(b__startswith='f')
                self.runQuery(b__endswith='h')
                self.runQuery(b__contains='e')        
                self.runQuery(twotable__b__startswith='B')
                self.runQuery(twotable__b__exact='B1')        

    def runQuery(self, **kwargs):
        """ Switch engine each time """
        self.dummy_request_start()
        Q = OneTable.objects.filter(**kwargs)
        for rec in Q:
            retrieve = rec
            self.rows[self.engine] += 1
        self.dummy_request_end()
        return

    def setup_conns(self):
        """ The global connection object is rebuilt frequently
            just as it is in deployment with a multi- process and/or threaded
            web server - such as apache2.
            This unpooled multiple connection use is where the bulk of
            the time is lost when the connections dont use pooling.
            
            TODO: Probably should do proper child process forking for holding
            each of these to more realistically simulate a production web server
        """
        for engine in ['oraclepool','oracle']:        
            for i in range(0,self.conncount):
                self.conns[engine].append(None)

    def get_connection(self):
        """ The global connection object is switched whenever 
            a different process or threads serves the request
            NB: Must call cursor for it to actually connect to oracle
            and hence demonstrate the real world pooled connection effect
        """
        if self.newconns:
            globals()['connection'].close()
            globals()['connection'] = None
            DATABASES['default'] = DATABASES[self.engine]
            backend = load_backend(self.engine)
            process = randint(0,self.conncount - 1)
            if not self.conns[self.engine][process]:
                self.conns[self.engine][process] = backend.DatabaseWrapper(get_settings_dict(self.engine)) 
                cursor = self.conns[self.engine][process].cursor()
            globals()['connection'] = self.conns[self.engine][process]
        return

    def dummy_request_start(self):
        """ Send the normal signals and start the timer """
        self.start[self.engine].append(datetime.now())
        self.get_connection()
        globals()['connection'].queries = []        
        signals.request_started.send(sender=self.__class__)

    def dummy_request_end(self):
        """ Send the normal signals and end the timer """        
        signals.request_finished.disconnect(close_connection)
        signals.request_finished.send(sender=self.__class__)
        signals.request_finished.connect(close_connection)
        self.end[self.engine].append(datetime.now())
