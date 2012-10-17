print """To run the tests for oraclepool
         Go to django-oraclepool/tests
         Replace the details / or add a cred.py containing

        CREDENTIALS = {'ENGINE' : 'oraclepool',           
                            'USER' : 'scott',      
                            'NAME' : 'scott',             
                            'PASSWORD' : 'tiger',     
                            'HOST' : 'example.com',
                            'PORT' : '1521'            
                           }

         Run manage.py test
         Or if you are using virtualenv use 
         bin/python src/django-oraclepool/tests/manage.py test"""
