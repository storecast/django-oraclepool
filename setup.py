from setuptools import setup, find_packages
import os

version = '0.3'

setup(name='django-oraclepool',
      version=version,
      description="django database backend that uses cx_Oracle session pooling for connections",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "TODO.txt")).read() + "\n" +      
                       open(os.path.join("docs", "HISTORY.txt")).read(),      
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='django oracle connection pooling cx_Oracle',
      author='Ed Crewe, Taras Halturin',
      author_email='ed.crewe@bris.ac.uk',
      url='http://code.djangoproject.com/ticket/7732',
      license='Apache',
      packages=['oraclepool'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
