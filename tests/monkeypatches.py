import settings
from django.db.backends.oracle.creation import DatabaseCreation
from datetime import datetime

# Monkeypatch standard oracle driver for tests 
# so it can be tested against an existing db too. See settings.
if settings.DATABASES['oracle']['EXTRAS'].get('existing',''):

    print 'Monkey patching for using existing database for tests'

    def _create_test_db(self, verbosity=1, autoclobber=False):
        """ if existing is set then this uses the settings database
            for testing rather than creating a new one
        """
        self.start_time(True)
        if not getattr(settings, 'TEST_DATABASE_NAME', ''):
            settings.TEST_DATABASE_NAME = settings.DATABASE_NAME
            settings.TEST_DATABASE_USER = settings.DATABASE_USER
            settings.TEST_DATABASE_PASSWD = settings.DATABASE_PASSWORD
        print 'Using Test Database %s' % settings.TEST_DATABASE_NAME
        return settings.TEST_DATABASE_NAME

    def start_time(self, reset=False):
        """ Getter / setter since attrib may be lost with monkey patch """
        if reset or not getattr(self, 'start', None):
            self.start = datetime.now()
        return self.start

    def _destroy_test_db(self, test_database_name, verbosity=1):
        """ if existing is set then this must clean up all the test
            schema and data - not just drop the database
        """
        print "#### Built tables and tested in %s ####" % str(datetime.now() - self.start_time())
        from django.db import connection
        print 'Cleaning up test data and schema from %s' %  settings.TEST_DATABASE_NAME
        from oraclepool.creation import DatabaseCreation as DCPool
        pool = DCPool(connection)
        pool._drop_test_tables()
        pool._delete_test_users()

    DatabaseCreation.start_time = start_time
    DatabaseCreation._create_test_db = _create_test_db
    DatabaseCreation._destroy_test_db = _destroy_test_db

    


