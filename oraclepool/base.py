"""
Oracle pooled connection database backend for Django.
Requires cx_Oracle: http://www.python.net/crew/atuining/cx_Oracle/
"""

import os
import thread
from django.db.backends import BaseDatabaseWrapper, BaseDatabaseValidation
try:
    from django.db.backends.signals import connection_created
except:
    connection_created = None
# Makes it explicit where the default oracle versions of these components are used
from django.db.backends.oracle.base import DatabaseFeatures as OracleDatabaseFeatures
from django.db.backends.oracle.base import DatabaseOperations as OracleDatabaseOperations
from django.db.backends.oracle.client import DatabaseClient as OracleDatabaseClient
from django.db.backends.oracle.introspection import DatabaseIntrospection as OracleDatabaseIntrospection
from django.db.backends.oracle.base import FormatStylePlaceholderCursor as OracleFormatStylePlaceholderCursor

from oraclepool.creation import DatabaseCreation
from django.conf import settings

try:
    import cx_Oracle as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading cx_Oracle module: %s" % e)

from django.utils.encoding import smart_str, force_unicode
# Check whether cx_Oracle was compiled with the WITH_UNICODE option.  This will
# also be True in Python 3.0.
if int(Database.version.split('.', 1)[0]) >= 5 and not hasattr(Database, 'UNICODE'):
    convert_unicode = force_unicode
else:
    convert_unicode = smart_str

# Oracle takes client-side character set encoding from the environment.
os.environ['NLS_LANG'] = '.UTF8'

def get_extras(database='default'):
    """ Oracle already has OPTIONS specific to cx_Oracle.connection() use
        This adds extra pool and sql logging attributes to the settings 

        'homogeneous':1, # 1 = single credentials, 0 = multiple credentials
        Dropped this option to use multiple credentials since if supplied
        to Database.version (ie cx_Oracle) < '5.0.0' it breaks and we want
        separate pools for separate credentials anyhow.
    """
    default_extras = {'min':4,         # start number of connections
                      'max':8,         # max number of connections
                      'increment':1,   # increase by this amount when more are needed
                      'threaded':True, # server platform optimisation 
                      'timeout':600,   # connection timeout, 600 = 10 mins
                      'log':0,         # extra logging functionality
                      'logpath':'',    # file system path for oraclepool.log file
                      'existing':'',   # Type modifications if using existing database data
                      'like':'LIKEC',  # Use LIKE or LIKEC - Oracle ignores index for LIKEC on older dbs
                      'session':[]     # Add session optimisations applied to each fresh connection, eg.
                                       #   ['alter session set cursor_sharing = similar',
                                       #    'alter session set session_cached_cursors = 20']
                      }
    if hasattr(settings, 'DATABASES'):
        db_settings = settings.DATABASES.get(database, {})
        if db_settings.has_key('EXTRAS'):
            return db_settings['EXTRAS']
    if hasattr(settings, 'DATABASE_EXTRAS'):
        return settings.DATABASE_EXTRAS
    else:
        return default_extras

def get_logger(extras):
    """ Check whether logging is required
        If log level is more than zero then logging is performed
        If log level is DEBUG then logging is printed to screen
        If no logfile is specified then unless its DEBUG to screen its added here
        NB: Log levels are 10 DEBUG, 20 INFO, 30 WARNING, 40 ERROR, 50 CRITICAL
    """

    loglevel = int(extras.get('log', 0))
    if loglevel > 0:
        import logging
        logfile = extras.get('logpath','')
        if logfile.endswith('.log'):
            (logfile, filename) = os.path.split(logfile)
        else:
            filename = 'oraclepool.log'
        if os.path.exists(logfile):
            logfile = os.path.join(logfile, filename)
        else:
            logfile = ''
        if not logfile and extras.get('log') > logging.DEBUG:
            logfile = '.'
        if logfile in ['.', '..']:
            logfile = os.path.join(os.path.abspath(os.path.dirname(logfile)), filename)
        # if log file is writable do it
        if not logfile:
            raise Exception('Log path %s not found' % extras.get('logpath', ''))
            return None
        else:
            logging.basicConfig(filename=logfile, level=loglevel)
            mylogger = logging.getLogger("oracle_pool")
            mylogger.setLevel(loglevel)
            chandler = logging.StreamHandler()
            chandler.setLevel(loglevel)
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            formatter = logging.Formatter(fmt)
            chandler.setFormatter(formatter)
            mylogger.addHandler(chandler)
            from datetime import datetime
            msg = '''%s #### Started django-oraclepool 
                     SQL logging at level %s ####''' % (datetime.now(), loglevel)
            mylogger.info(msg)
            return mylogger
    else:
        # 'No logging set'
        return None

    # Add sql logging for all requests if DEBUG level
    if extras.get('log') == 10 or settings.DEBUG:
        # Add middleware if needed
        middleware_classes = list(settings.MIDDLEWARE_CLASSES) 
        middleware_classes.append('oraclepool.log_sql.SQLLogMiddleware')
        settings.MIDDLEWARE_CLASSES = tuple(middleware_classes)

DATABASE_EXTRAS = get_extras()
logger = get_logger(DATABASE_EXTRAS)
    
class DatabaseFeatures(OracleDatabaseFeatures):
    """ Add extra options from default Oracle ones
        Plus switch off save points and id return
        See 
        http://groups.google.com/group/django-developers/browse_thread/thread/bca33ecf27ff5d63
        Savepoints could be turned on but are not needed
        and since they may impact performance they are turned off here 
    """
    uses_savepoints = False
    can_return_id_from_insert = False
    allows_group_by_ordinal = False
    supports_tablespaces = True
    uses_case_insensitive_names = True
    time_field_needs_date = True
    date_field_supports_time_value = False

class DatabaseWrapper(BaseDatabaseWrapper):
    """ This provides the core connection object wrapper
        for cx_Oracle's pool handling.
        The code is mostly taken from
        http://code.djangoproject.com/ticket/7732 by halturin
    """

    poolprops = {'homogeneous':'',
                 'increment':'',
                 'max':'',
                 'min':'',
                 'busy':'',
                 'opened':'',
                 'name':'',
                 'timeout':'',
                 'tnsentry':''
                }
    operators = {
        'exact': '= %s',
        'iexact': '= UPPER(%s)',
        'contains': "LIKEC %s ESCAPE '\\'",
        'icontains': "LIKEC UPPER(%s) ESCAPE '\\'",
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': "LIKEC %s ESCAPE '\\'",
        'endswith': "LIKEC %s ESCAPE '\\'",
        'istartswith': "LIKEC UPPER(%s) ESCAPE '\\'",
        'iendswith': "LIKEC UPPER(%s) ESCAPE '\\'",
    }
    oracle_version = None

    def __init__(self, *args, **kwargs):
        """ Set up the various database components
            Oracle prefixed classes use the standard Oracle
            version - tested with both 1.0 and 1.2
        """
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        if DATABASE_EXTRAS.get('like', 'LIKEC') != 'LIKEC':
            for key in ['contains',
                        'icontains',
                        'startswith',
                        'istartswith',
                         'endswith',
                        'iendswith']:
                self.operators[key] = self.operators[key].replace('LIKEC', 
                                                     DATABASE_EXTRAS['like'])
        try:        
            self.features = DatabaseFeatures(self)
        except:
            # pre django 1.3
            self.features = DatabaseFeatures()
        try:
            self.ops = OracleDatabaseOperations(self)
        except:
            # pre django 1.4
            self.ops = OracleDatabaseOperations()
        self.client = OracleDatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = OracleDatabaseIntrospection(self)
        try:
            self.validation = BaseDatabaseValidation(self)
        except:
            # pre django 1.2
            self.validation = BaseDatabaseValidation()            

    def get_config(self):
        """ Report the oracle connection and pool data see 
            http://cx-oracle.sourceforge.net/html/session_pool.html#sesspool
        """
        pool = self._get_pool()
        if pool:
            for key in self.poolprops.keys():
                try:
                    self.poolprops[key] = getattr(pool, key, '')
                except:
                    pass
        else:
            self.poolprops['name'] = 'Session pool not found'
        return self.poolprops

    def _get_pool (self):
        """ Get the connection pool or create it if it doesnt exist
            Add thread lock to prevent server initial heavy load creating multiple pools
        """
        pool_name = '_pool_%s' % getattr(self, 'alias', 'common')
        if not hasattr (self.__class__, pool_name):
            lock = thread.allocate_lock()
            lock.acquire()
            if not hasattr (self.__class__, pool_name):            
                if DATABASE_EXTRAS['threaded']:
                    Database.OPT_Threading = 1
                else:
                    Database.OPT_Threading = 0
                # Use 1.2 style dict if its there, else make one
                try:
                    settings_dict = self.creation.connection.settings_dict
                except:
                    settings_dict = None

                if not settings_dict.get('NAME',''):
                    settings_dict = {'HOST':settings.DATABASE_HOST,
                                     'PORT':settings.DATABASE_PORT,
                                     'NAME':settings.DATABASE_NAME,
                                     'USER':settings.DATABASE_USER, 
                                     'PASSWORD':settings.DATABASE_PASSWORD, 
                                     }
                if len(settings_dict.get('HOST','').strip()) == 0:
                    settings_dict['HOST'] = 'localhost'
                if len(settings_dict.get('PORT','').strip()) != 0:
                    dsn = Database.makedsn(settings_dict['HOST'],
                                           int(settings_dict['PORT']),
                                           settings_dict.get('NAME',''))
                else:
                    dsn = settings_dict.get('NAME','')

                try:
                    pool = Database.SessionPool(settings_dict.get('USER',''), 
                                                settings_dict.get('PASSWORD',''), 
                                                dsn, 
                                                DATABASE_EXTRAS.get('min',4), 
                                                DATABASE_EXTRAS.get('max',8), 
                                                DATABASE_EXTRAS.get('increment',1),
                                                threaded = DATABASE_EXTRAS.get('threaded',
                                                                               True))
                except Exception, err:
                    pool = None
                if pool:
                    if DATABASE_EXTRAS.get('timeout', 0):
                        pool.timeout = DATABASE_EXTRAS['timeout']
                    setattr(self.__class__, pool_name, pool)
                else:
                    msg = """##### Database '%s' login failed or database not found ##### 
                             Using settings: %s 
                             Django start up cancelled
                          """ % (settings_dict.get('NAME', 'None'), settings_dict)
                    print msg
                    print '\n##### DUE TO ERROR: %s\n' % err
                    return None
                lock.release()
        return getattr(self.__class__, pool_name)
        
    pool = property(_get_pool)

    def _cursor(self, settings=None):
        """ Get a cursor from the connection pool """
        cursor = None
        if self.pool is not None:
            if self.connection is None:
                # Set oracle date to ansi date format.  This only needs to execute
                # once when we create a new connection. 
                self.connection = self.pool.acquire()
                if connection_created:
                    # Assume acquisition of existing connection = create for django signal
                    connection_created.send(sender=self.__class__)
                if logger:
                    logger.info("Acquire pooled connection \n%s\n" % self.connection.dsn)

                cursor = FormatStylePlaceholderCursor(self.connection)
                cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD' "  
                               "NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'")
                if DATABASE_EXTRAS.get('session', []):
                    for sql in DATABASE_EXTRAS['session']:
                        cursor.execute(sql)
                try:
                    self.oracle_version = int(self.connection.version.split('.')[0])
                    # There's no way for the DatabaseOperations class to know the
                    # currently active Oracle version, so we do some setups here.
                    # TODO: Multi-db support will need a better solution (a way to
                    # communicate the current version).
                    if self.oracle_version <= 9:
                        self.ops.regex_lookup = self.ops.regex_lookup_9
                    else:
                        self.ops.regex_lookup = self.ops.regex_lookup_10
                except ValueError, err:
                    if logger:
                        logger.warn(str(err))
                try:
                    self.connection.stmtcachesize = 20
                except:
                    # Django docs specify cx_Oracle version 4.3.1 or higher, but
                    # stmtcachesize is available only in 4.3.2 and up.
                    pass
            else:
                cursor = FormatStylePlaceholderCursor(self.connection)                
        else:
            if logger:
                logger.critical('Pool couldnt be created - please check your Oracle connection or credentials')
            else:
                raise Exception('Pool couldnt be created - please check your Oracle connection or credentials')
            
        if not cursor:
            cursor = FormatStylePlaceholderCursor(self.connection)
        # Default arraysize of 1 is highly sub-optimal.
        cursor.arraysize = 100
        return cursor

    def close(self):
        """ Releases connection back to pool """
        if self.connection is not None:
            if logger:
                logger.debug("Release pooled connection\n%s\n" % self.connection.dsn)
            self.pool.release(self.connection)
            self.connection = None

    def _savepoint_commit(self, sid):
        """ Oracle doesn't support savepoint commits.  Ignore them. """
        pass

class FormatStylePlaceholderCursor(OracleFormatStylePlaceholderCursor):
    """ Added just to allow use of % for like queries without params
        and use of logger if present.
    """

    def cleanquery(self, query, args=None):
        """ cx_Oracle wants no trailing ';' for SQL statements.  For PL/SQL, it
            it does want a trailing ';' but not a trailing '/'.  However, these
            characters must be included in the original query in case the query
            is being passed to SQL*Plus.

            Split out this as a function and allowed for no args so
            % signs can be used in the query without requiring parameterization
        """
#        if query.find('INSERT')> -1:
#            raise Exception(query) #params[8])
        if query.endswith(';') or query.endswith('/'):
            query = query[:-1]
        if not args:
            return convert_unicode(query, self.charset)
        else:
            try:
                return convert_unicode(query % tuple(args), self.charset)
            except TypeError, error:
                err = 'Parameter parsing failed due to error %s for query: %s' % (error,
                                                                                  query)
                if logger:
                    logger.critical(err)
                else:
                    raise Exception(err)
                
    def execute(self, query, params=[]):
        if params is None:
            args = None
        else:
            params = self._format_params(params)
            args = [(':arg%d' % i) for i in range(len(params))]
        query = self.cleanquery(query, args)
        self._guess_input_sizes([params])
        try:
            return self.cursor.execute(query, self._param_generator(params))
        except Database.Error, error:
            # cx_Oracle <= 4.4.0 wrongly raises a Database.Error for ORA-01400.
            if error.args[0].code == 1400 and not isinstance(error, 
                                                             Database.IntegrityError):
                error = Database.IntegrityError(error.args[0])
            err = '%s due to query:%s' % (error, query)
            if logger:
                logger.critical(err)
            else:
                raise Exception(err) 

    def executemany(self, query, params=[]):
        try:
            args = [(':arg%d' % i) for i in range(len(params[0]))]
        except (IndexError, TypeError):
            # No params given, nothing to do
            return None
        query = self.cleanquery(query, args)        
        formatted = [self._format_params(i) for i in params]
        self._guess_input_sizes(formatted)
        try:
            return self.cursor.executemany(query,
                                [self._param_generator(p) for p in formatted])
        except Database.Error, error:
            # cx_Oracle <= 4.4.0 wrongly raises a Database.Error for ORA-01400.
            if error.args[0].code == 1400 and not isinstance(error, 
                                                             Database.IntegrityError):
                error = Database.IntegrityError(error.args[0])
            if logger:
                logger.critical('%s due to query: %s' % (error, query))                
            else:
                raise 
