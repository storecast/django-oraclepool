TODO
----

- Oracle 11g has internal session pooling - DRCP - and cx_Oracle can use that for
  even better performance, so need to add appropriate modification to test whether 
  the database 11g or later, and use this feature in place of a cx_Oracle side pool.
  NB: requires cx_Oracle 5, see http://www.oracle.com/technology/pub/articles/tuininga-cx_oracle.html

