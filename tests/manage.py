#!/usr/bin/env python
import sys, os
# import django and oracle pool based on the location of this tests folder ...
here_path = os.path.abspath(os.path.dirname("."))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Specify path to django if its not installed in pythons own libs
# and not found above the location of this egg
# sys.path.append('your path to django')
try:
    from django.core.management import execute_manager
except:
    egg_path = os.path.join('django-oraclepool','tests')
    djangopath = here_path.replace(egg_path, '')
    parts = os.path.split(djangopath)
    while parts[0]:
        djangopath = os.path.join(parts[0],'django')
        if os.path.exists(djangopath):
            sys.path.append(djangopath)
            break
        djangopath = parts[0]
        parts = os.path.split(djangopath)
    from django.core.management import execute_manager
    
# Add oracle pool path
oraclepool_path = here_path.replace('tests', '')
sys.path.append(oraclepool_path)
	
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
