# Django settings for testbackend project.
# from dbsettings import *

# Set up common credentials for testing
# oraclepool vs. oracle functionality & performance 
try:
    from cred import CREDENTIALS
except:
    CREDENTIALS = {'USER' : 'SCOTT',      
                   'NAME' : 'SCOTT',             
                   'PASSWORD' : 'TIGER',     
                   'HOST' : 'localhost', 
                   'PORT' : '1521',            
                   'OPTIONS' : {}
                   }

# NB: Oracle already has OPTIONS dict so use EXTRAS for pooling and logging
EXTRAS = {'min':4,         # start number of connections
          'max':8,         # max number of connections
          'increment':2,   # increase by this amount when more are needed
          'homogeneous':1, # 1 = single credentials, 0 = multiple credentials
          'threaded':True, # server platform optimisation 
          'timeout':10,   # connection timeout, 600 = 10 mins
          'log':0,         # extra logging functionality
          'logpath':'.',    # file system path to log file
          'existing':'Unicode',   # Type modifications if using existing database data
          'session': ["alter session set session_cached_cursors = 8;",
                      "alter session set cursor_sharing = 'SIMILAR'"]
          }

# Use django 1.2 or later multi-db setting (see rewrite for pre 1.2 below ...)
DATABASES= { 'oraclepool':{'ENGINE' : 'oraclepool',
                           'EXTRAS' : EXTRAS
                          },
             'oracle':{'ENGINE' : 'django.db.backends.oracle',
                       'EXTRAS' : {'existing':'Unicode'}
                       }
             }

# Replace credentials details for both engines but make sure 
# do not over-ride the engine and related extras from above
for db in DATABASES.keys():
    for key in CREDENTIALS.keys():
        if key not in ('ENGINE', 'EXTRAS'):
            DATABASES[db][key] = CREDENTIALS[key] 

### Switch backend for standard tests
### Specify oracle or oraclepool for running the test suite against
DATABASES['default'] = DATABASES['oraclepool']

def get_settings_dict(db='default'):
    """ Make compatible with 1.2 or earlier database settings
        used by apitest and performance test
    """   
    try:
        from settings import DATABASES
        settings_dict = DATABASES.get(db, {})
    except:
        pass
    if not settings_dict:
        for key in ['HOST','PORT','NAME','USER','PASSWORD','ENGINE','OPTIONS','EXTRAS']:
            settings_dict[key] = globals().get('DATABASE_%s' % key, '') 
    for key in settings_dict.keys():
        settings_dict['DATABASE_%s' % key] = settings_dict[key]
    return settings_dict

# Also rewrite into globals for pre django 1.2 compatibility
for k, v in DATABASES['default'].items():
    globals()['DATABASE_' + k] = v

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
STATIC_URL = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%(u8uds4xsy0+95cj3o&k49*u@&--yp0t&e&0$!@s2fvea#u4j'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# required if South is installed ...
SOUTH_DATABASE_ADAPTERS = { 'default': "south.db.oracle" }

# DEBUG - run tests over Oracle engine only for South - check same pass rate!
#for key in ['ENGINE', 'EXTRAS']:
#    DATABASES['oraclepool'][key] = DATABASES['oracle'][key]
# SKIP_SOUTH_TESTS = False
# Drop south test tables ...
#BEGIN
#FOR c IN (SELECT table_name FROM user_tables where table_name like 'TEST%') LOOP
#EXECUTE IMMEDIATE ('DROP TABLE ' || c.table_name || ' CASCADE CONSTRAINTS');
#END LOOP;
#END;

INSTALLED_APPS = (
#    'south',
    'oraclepool',
    'oraclepool.tests.performance',
    'oraclepool.tests.apitest',
    'oraclepool.tests.regress',
    'oraclepool.tests.slicing',
    'oraclepool.tests.nulls',
    'oraclepool.tests.aggregates'
)

# For CI testing of releases
try:
    import django_jenkins
    CI = True
except:
    CI = False

if CI:
    INSTALLED_APPS += ('django_jenkins',)
    PROJECT_APPS = ('oraclepool.tests',)
    JENKINS_TASKS = ('django_jenkins.tasks.run_pylint',
                     'django_jenkins.tasks.with_coverage')
