ILRT Django Oracle pool
=======================

Ed Crewe, `IT Services R&D
<http://www.bris.ac.uk/ilrt>`_ at University of Bristol, May 2012

Packaged version of http://code.djangoproject.com/ticket/7732 by Taras Halturin
django database backend that uses cx_Oracle session pooling for connections

See http://bitbucket.org/edcrewe/django-oraclepool

Original Code Modifications
---------------------------

Pruned original ticket's base.py to just hold the pooling relevant code. 
Using the standard Oracle connection for the rest of the database classes, 
ie. operations, client and introspection. 

Tested with django 1.1 to 1.4

Extra features
--------------

- Added the pooling and logging parameters to the settings.

- The connector uses the standard python logging model and caters for logging 
  full details of queries, either to a file log or appending them to the 
  bottom of the screen if the log level is DEBUG.

- Added an option for running against existing (older) Oracle databases, ie those 
  which may not have unicode for character fields.

- Option also allows running the tests against an existing database so that 
  running tests doesnt require database creation (oracle sys dba) rights.

- Added a modification to the cursor to not parse parameters if not required.

Why use it?
-----------

Perhaps due to our remotely distributed Oracle network taking a very long time 
to establish connections, the use of cx_Oracle's session pooling for 
connections provided a truely radical performance boost for requests 
from 3-4 secs/req to 0.4 secs/req, so many times faster.   

For single direct Oracle access it might still give a doubling of performance. 
Install it and run the performance test to find out (see below).

Installation
------------

Download the egg (or use buildout) or download the tarball and extract it. 
Then add /path/to/django-oraclepool to your python path.

Specify DATABASE_ENGINE = 'oraclepool' instead of 'oracle' in your settings.  

If you dont want to use the default extra database settings then the following defaults
are used

>>> EXTRAS = {'min':4,        # starting number of pooled connections
...           'max':8,         # maximum number of connections in the pool
...           'increment':1,   # increase by this amount when more are needed
...           'threaded':True, # server platform optimisation 
...           'timeout':600,   # connection timeout, 600 = 10 mins
...           'log':0,         # extra logging functionality turned on
...           'logfile':'',    # file system path to log file
...           'existing':''    # Type modifications for existing database and flag for tests
...           'session':[]     # Add session optimisations applied to each fresh connection, eg.
...                            #   alter session set cursor_sharing = similar;
...                            #   Enables use of bind variables assuming it isnt set at a system level 
...			       #   alter session set session_cached_cursors = 20;
...                            #   Allows cursor reuse between queries   
...            'like':'LIKE'   # Option instead of LIKEC default which can stop indexes being used
...            }

Note that if you want sql logging to screen when in DEBUG mode then add 
'oraclepool.log_sql.SQLLogMiddleware' to your MIDDLEWARE_CLASSES


General Performance
-------------------

Initially after apache restart you will see the first few requests taking the same time as each 
one initiates a new pooled connection. Then request speed should drop as it loses the Oracle 
connection time.

NB: Note that if you have PythonDebug On then the pool may get flushed much more regularly. 
So you will often get the slower pool populating requests.

Using mod_wsgi rather than mod_python may give a 25% added increase although this needs
confirmation on a production instance.

It should be remembered that there is also a very great deal of performance work that can be 
done at the database level. I have posted a page with some of the tips and tricks for 
improving database performance on my blog - http://python.blogs.ilrt.org/database-performance/

Pooling alternatives
--------------------

Pyora pool

Also tried out pyora pool see http://code.google.com/p/pyorapool
but found increase was only around 90% and also had 
issues with connection control and database edits failing.
This also requires the whole architecture of a separate remote procedure call daemon 
that holds the connection pool. Uneccesary here ... although useful
for pooling across different applications, or multiple servers.

ORM pools

Usually ORMs have a generic pooling capability, unfortuately djangos only has a beta one 
in development, unless you plugin another ORM, eg. http://www.sqlalchemy.org/ instead. 
However that does require code rewriting.

Having said that a generic ORM level pool is unlikely to perform as well as one at the 
database connector level, which in turn is going to be less fast than one within the 
database itself (see below).

Tests
-----

The tests are run via separate test apps in the django-oraclepool folder.
Some of these tests are derived from a set for http://code.google.com/p/django-mssql/

They also include the option to run the test suite against an existing database for users who dont
have full oracle dba rights on their test oracle servers. 

The key extra tests are performance timings for running the test suite via the pooled oracle
connection vs the standard one. Hopefully these timings should indicate whether using oraclepool is
of value when using django with your oracle server network. 

Run the tests by running django-oraclepool/tests/manage.py test 
Or run individual tests by supplying there name, eg. manage.py test performance

The performance test simulates a real environment by running up a number of connections
as would exist with a production web server (the Apache2 default is 2 processes * 64 threads)
whilst the test creates a maximum of only 32.
In practise I found the actual performance improvement significantly greater than that indicated 
by the doubling of speed that the multiple connections performance test gives. However that
may not be the case dependent on your production oracle and web server environment.






