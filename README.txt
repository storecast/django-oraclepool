ilrtdjango.oracle_pool
======================

Packaged version of http://code.djangoproject.com/ticket/7732

With various tweaks in base.py to get it to work with django 1.1.1

django database backend that uses cx_Oracle session pooling for connections

Perhaps due to our remotely distributed Oracle network taking a very long time 
to establish connections, the use of cx_Oracle's 
session pooling for connections provided a truely radical performance boost
for requests from 3-4 secs/req to 0.3 secs/req  
ie a 1000% performance increase !! 

NB: Using mod_wsgi rather than mod_python may give a 25% added increase

NBB: Also tried out pyora pool see http://code.google.com/p/pyorapool
but found increase was only around 90% and also had 
issues with connection control and database edits failing.
This also requires the whole architecture of a separate remote procedure call daemon 
that holds the connection pool. Uneccesary here ... although possibly useful
for pooling across all apps, or multiple servers.

Remember with 11g it has Oracle side session pooling and cx_Oracle can use that for
even better performance, so modify this when we upgrade from 10.

Ed Crewe, University of Bristol Nov 11th 2009
