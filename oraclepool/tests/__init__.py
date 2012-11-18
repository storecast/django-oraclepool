""" Importing tests here means they are found for running test oraclepool
    Need to also add each as an app for it to have the test models needed
    eg. oraclepool.tests.performance
"""
import monkeypatches
from oraclepool.tests.aggregates import models
from oraclepool.tests.apitest.tests import test_dbapi
from oraclepool.tests.regress.tests import *
from oraclepool.tests.nulls.tests import NullTests
from oraclepool.tests.slicing.tests import PagingTestCase, DistinctTestCase
from oraclepool.tests.performance.tests import PerformanceTestCase


