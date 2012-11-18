import settings
from django.db.backends.oracle.creation import DatabaseCreation
from django.test.simple import DjangoTestSuiteRunner
from datetime import datetime

# For repeated testing you may want to keep the test tables...
NO_TEARDOWN = False
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

    def _test_connection(self):
        """ Get the default connection from tests.settings """
        from django.db import connections, DEFAULT_DB_ALIAS
        return connections[DEFAULT_DB_ALIAS]

    def _destroy_test_db(self, test_database_name, verbosity=1):
        """ if existing is set then this must clean up all the test
            schema and data - not just drop the database
        """
        if hasattr(self, 'start_time'):
            print "#### Tested in %s ####" % str(datetime.now() - self.start_time())
        print 'Cleaning up test data and schema from %s' %  test_database_name
        from oraclepool.creation import DatabaseCreation as DCPool
        pool = DCPool(self._test_connection())
        if NO_TEARDOWN:
            print 'Leaving test tables around for speedy test repeat'
            pool._delete_test_data()
        else:
            print 'Dropping test tables'
            pool._drop_test_tables()
        pool._delete_test_users()

    def setup_databases(self, **kwargs):
        """ Dont create it, but do still run syncdb to populate test fixtures """
        connection = self._test_connection()
        alias = connection.alias
        from django.core.management import call_command
        try:
            call_command('syncdb',
                verbosity=1,
                interactive=False,
                database=alias,
                load_initial_data=False)
        except:
            # In case test suite cancelled before clean up in previous run
            _destroy_test_db(self, alias)
            call_command('syncdb',
                verbosity=1,
                interactive=False,
                database=alias,
                load_initial_data=False)
        return

    def dummy_teardown_databases(self, old_config, **kwargs):
        connection = self._test_connection()
        _destroy_test_db(self, connection.alias)

    DatabaseCreation.start_time = start_time
    DatabaseCreation._create_test_db = _create_test_db
    DatabaseCreation._destroy_test_db = _destroy_test_db
    setattr(DjangoTestSuiteRunner, '_test_connection', _test_connection)
    DjangoTestSuiteRunner.setup_databases = setup_databases
    DjangoTestSuiteRunner.teardown_databases = dummy_teardown_databases
