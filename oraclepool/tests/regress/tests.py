import decimal
from django.test import TestCase
from oraclepool.tests.regress.models import *

class Bug26TestCase(TestCase):
    """Test that slicing queries w/ duplicate column names works."""

    def testWithDuplicateColumnNames(self):
        b = RelatedB(a='this is a value', b="valueb", c="valuec")
        b.save()
        
        RelatedA(a="valuea", b=b).save()
        RelatedA(a="valuea", b=b).save()

        items = RelatedA.objects.select_related()[1:2]
        self.assertEqual(len(items), 1)

class Bug37TestCase(TestCase):
    """Test that IntegrityErrors are raised when appropriate."""

    def testDuplicateKeysFails(self):
        Bug37ATable(pk=1, a='a', b='b', c='c').save(force_insert=True)
        try:
            Bug37ATable(pk=1, a='a', b='b', c='c').save(force_insert=True)
        except Exception, e:
            self.failUnless(isinstance(e, IntegrityError) or str(e).find('ORA-00001')>-1,
                            'Expected IntegrityError but got: %s - %s' % (type(e),str(e)))
            
    def testDeleteRelatedRecordFails(self):
        a2 = Bug37ATable(a='a', b='b', c='c')
        a2.save()
        
        Bug37BTable(d='d', a=a2).save()
        try:
            a2.delete()
        except Exception, e:
            self.failUnless(isinstance(e, IntegrityError), 'Expected IntegrityError but got: %s' % type(e))

class Bug38TestCase(TestCase):
    def testInsertVariousFormats(self):
        """
        Test adding decimals as strings with various formats.
        """
        Bug38Table(d=decimal.Decimal('0')).save()
        Bug38Table(d=decimal.Decimal('0e0')).save()
        Bug38Table(d=decimal.Decimal('0E0')).save()
        Bug38Table(d=decimal.Decimal('450')).save()
        Bug38Table(d=decimal.Decimal('450.0')).save()
        Bug38Table(d=decimal.Decimal('450.00')).save()
        Bug38Table(d=decimal.Decimal('450.000')).save()
        Bug38Table(d=decimal.Decimal('0450')).save()
        Bug38Table(d=decimal.Decimal('0450.0')).save()
        Bug38Table(d=decimal.Decimal('0450.00')).save()
        Bug38Table(d=decimal.Decimal('0450.000')).save()
        Bug38Table(d=decimal.Decimal('4.5e+2')).save()
        Bug38Table(d=decimal.Decimal('4.5E+2')).save()
        self.assertEquals(len(list(Bug38Table.objects.all())),13)

    def testReturnsDecimal(self):
        """
        Test if return value is a python Decimal object 
        when saving the model with a Decimal object as value 
        """
        Bug38Table(d=decimal.Decimal('0')).save()
        d1 = Bug38Table.objects.all()[0]
        self.assertEquals(decimal.Decimal, d1.d.__class__)

    def testReturnsDecimalFromString(self):
        """
        Test if return value is a python Decimal object 
        when saving the model with a unicode object as value.
        """
        Bug38Table(d=u'123').save()
        d1 = Bug38Table.objects.all()[0]
        self.assertEquals(decimal.Decimal, d1.d.__class__)        

    def testSavesAfterDecimal(self):
        """
        Test if value is saved correctly when there are numbers 
        to the right side of the decimal point 
        """
        Bug38Table(d=decimal.Decimal('450.1')).save()
        d1 = Bug38Table.objects.all()[0]
        self.assertEquals(decimal.Decimal('450.1'), d1.d)
    
    def testInsertWithMoreDecimals(self):
        """
        Test if numbers to the right side of the decimal point 
        are saved correctly rounding to a decimal with the correct 
        decimal places.
        """
        Bug38Table(d=decimal.Decimal('450.111')).save()
        d1 = Bug38Table.objects.all()[0]
        self.assertEquals(decimal.Decimal('450.11'), d1.d)    
        
    def testInsertWithLeadingZero(self):
        """
        Test if value is saved correctly with Decimals with a leading zero.
        """
        Bug38Table(d=decimal.Decimal('0450.0')).save()
        d1 = Bug38Table.objects.all()[0]
        self.assertEquals(decimal.Decimal('450.0'), d1.d)


class Bug58TestCase(TestCase):
    def testDistinctRelated(self):
        i1 = Bug58TableIn(name='bread')
        i1.save()
        i2 = Bug58TableIn(name='butter')
        i2.save()
        
        r = Bug58TableRecipe(name='toast')
        r.save()
        
        Bug58TableItem(recipe=r, ingredient=i1, amount='1 slice').save()
        Bug58TableItem(recipe=r, ingredient=i2, amount='1 Tbsp').save()

        q = list(Bug58TableRecipe.objects.filter(item__ingredient__name__in=['bread','butter']).distinct())
        self.assertEqual(len(q), 1)

        
