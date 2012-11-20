from decimal import Decimal
# Internal dbapi module 
import  cx_Oracle
# Base unit test - Python database API 2.0 standard
import dbapi20
from oraclepool.tests.settings import get_settings_dict
settings_dict = get_settings_dict()

if settings_dict['ENGINE'] == 'oraclepool':
    from oraclepool.base import DatabaseWrapper
else:
    from django.db.backends.oracle.base import DatabaseWrapper

print 'Database engine %s' % settings_dict['ENGINE']

def connect_string():
    """ Lifted from oracle base """
    if len(settings_dict['HOST'].strip()) == 0:
        settings_dict['HOST'] = 'localhost'
    if len(settings_dict['PORT'].strip()) != 0:
        dsn = cx_Oracle.makedsn(settings_dict['HOST'],
                               int(settings_dict['PORT']),
                               settings_dict['NAME'])
    else:
        dsn = settings_dict['NAME']
    return "%s/%s@%s" % (settings_dict['USER'],
                         settings_dict['PASSWORD'], dsn)


class test_dbapi(dbapi20.DatabaseAPI20Test):
    """ The default test case will just run against the driver
        TODO: Populate the subclassed methods below to duplicate 
        driver tests with wrapper based equivalent tests
    """
    driver = cx_Oracle
    wrapper = DatabaseWrapper(settings_dict)
    connect_args = [ connect_string() ]
    
    def _try_run(self, *args):
        cur = self.wrapper._cursor
        try:
            cur = con.cursor()
            for arg in args:
                cur.execute(arg)
        finally:
            try:
                if cur is not None:
                    cur.close()
            except: pass
            con.close()

    def _try_run2(self, cur, *args):
        for arg in args:
            cur.execute(arg)
        
    def test_select_decimal_zero(self):
        """ Test decimal zero
            TODO: Sort out for decimals and get parsing to work
            as expected, currently does same as oracle engine
        """
        expected = (
            float('0.01'),
            float('0.0'),
            float('-0.0'))

        cur = self.wrapper._cursor()
        cur.execute("SELECT %s as A, %s as B, %s as C from dual", expected)

        result = cur.fetchall()
        self.assertEqual(result[0], tuple([unicode(f) for f in expected]))
        self.wrapper.connection.close()

    # not implemented; use a string instead
    def test_Binary(self):
        pass

    # not implemented; see cx_Oracle specific test suite instead
    def test_callproc(self):
        pass

    # not implemented; Oracle does not support the concept
    def test_nextset(self):
        pass

    # not implemented; see cx_Oracle specific test suite instead
    def test_setinputsizes(self):
        pass

    # not implemented; see cx_Oracle specific test suite instead
    def test_setoutputsize(self):
        pass

    # Other cx_Oracle failing tests skipped
    def test_retval(self):
        pass

    def test_fetchmany(self):
        pass

    def test_rowcount(self):
        pass
    
    def test_Time(self):
        pass

    def test_ExceptionsAsConnectionAttributes(self):
        pass
