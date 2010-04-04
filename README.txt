ILRT Django Oracle pool
=======================
UNRELEASED

Ed Crewe, ILRT, University of Bristol Nov 11th 2009

Packaged version of http://code.djangoproject.com/ticket/7732 by Taras Halturin

With various tweaks in base.py to get it to work with django 1.1.1 see the
change log below.

django database backend that uses cx_Oracle session pooling for connections

Perhaps due to our remotely distributed Oracle network taking a very long time 
to establish connections, the use of cx_Oracle's 
session pooling for connections provided a truely radical performance boost
for requests from 3-4 secs/req to 0.4 secs/req  
ie a 900% performance increase !! 

Installation
------------

Download the egg (or use buildout) or download the tarball and extract it. 
Then add /path/to/ilrtdjango.oracle_pool to your python path.

Specify DATABASE_ENGINE = 'ilrtdjango.oracle_pool' instead of 'oracle' in your settings.  

No other changes necessary because the pool settings are hard coded at the moment, should 
modify that to be configured via the DATABASE_EXTRAS setting.

General Performance
-------------------

Initially after apache restart you will see the first few requests taking the same time as each 
one initiates a new pooled connection. Then request speed should drop as it loses the Oracle 
connection time.

NB: Note that if you have PythonDebug On then the pool may get flushed much more regularly. 
So you will often get the slower pool populating requests.

Using mod_wsgi rather than mod_python may give a 25% added increase although this needs
confirmation on a production instance.

Pooling alternatives
--------------------

Pyora pool

Also tried out pyora pool see http://code.google.com/p/pyorapool
but found increase was only around 90% and also had 
issues with connection control and database edits failing.
This also requires the whole architecture of a separate remote procedure call daemon 
that holds the connection pool. Uneccesary here ... although possibly useful
for pooling across all apps, or multiple servers.

ORM pools

Usually ORMs have a generic pooling capability, unfortuately djangos only has a beta one 
in development, unless you plugin another ORM, eg. http://www.sqlalchemy.org/ instead. 
However that does require code rewriting.

Having said that a generic ORM level pool is unlikely to perform as well as one at the 
database connector level, which in turn is going to be less fast than one within the database itself.

Speaking of which, remember with 11g it has Oracle side session pooling - DRCP - and cx_Oracle can use that for
even better performance, so need to add appropriate modification to test if you are using 11g or later, 
and use this feature (requires cx_Oracle 5, see http://www.oracle.com/technology/pub/articles/tuininga-cx_oracle.html).



