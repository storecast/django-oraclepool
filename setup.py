from setuptools import setup, find_packages
import os

version = '0.2'

setup(name='ilrtdjango.oracle_pool',
      version=version,
      description="django database backend that uses cx_Oracle session pooling for connections",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='django oracle connection pooling cx_Oracle',
      author='Taras Halturin, Ed Crewe',
      author_email='halturin@gmail.com',
      url='http://code.djangoproject.com/ticket/7732',
      license='Apache',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ilrtdjango'],
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
