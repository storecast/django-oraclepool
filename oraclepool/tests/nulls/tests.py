import datetime
import decimal
from django.test import TestCase

from oraclepool.tests.nulls.models import *

class NullTests(TestCase):
    def _run(self, model, values):
        for v in values:
            model(val=v).save()
            
        self.assertEquals(len(list(model.objects.all())), len(values))

    def testChar(self):
        self._run(TableNullChar, (None, "This is my string value."))
        
    def testText(self):
        self._run(TableNullText, (None, "This is my string value."))
        
    def testInteger(self):
        self._run(TableNullInteger, (None, 32768))
        
    def testDateTime(self):
        self._run(TableNullDateTime,(None, datetime.datetime(2009,1,1,4,3,5)))
     
    def testDate(self):
        self._run(TableNullDate, (None, datetime.date(2009,1,1)))
     
    def testBoolean(self):
        self._run(TableNullNullBoolean, (None, True, False))

    def testFloat(self):
        self._run(TableNullFloat, (None, 34.3))

    def testDecimal(self):
        self._run(TableNullDecimal, (None, decimal.Decimal('99.99')))
