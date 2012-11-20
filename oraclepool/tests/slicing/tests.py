from django.core.paginator import Paginator
from django.test import TestCase
from oraclepool.tests.slicing.models import *
        
class PagingTestCase(TestCase):
    """The Paginator uses slicing internally."""
    fixtures = ['paging.json']
    
    def get_q(self, a1_pk):
        return SecondTable.objects.filter(a=a1_pk).order_by('b').select_related(depth=1)

    def try_page(self, page_number, q):
        # Use a single item per page, to get multiple pages.
        pager = Paginator(q, 1)
        self.assertEquals(pager.count, 3)

        on_this_page = list(pager.page(page_number).object_list)
        self.assertEquals(len(on_this_page), 1)
        self.assertEquals(on_this_page[0].b, 'B'+str(page_number))
    
    def testWithDuplicateColumnNames(self):
        a1_pk = FirstTable.objects.get(b='A1').pk
        q = self.get_q(a1_pk)
        
        for i in (1,2,3):
            self.try_page(i, q)
            
    def testPerRowSelect(self):
        a1_pk = FirstTable.objects.get(b='A1').pk
        q = SecondTable.objects.filter(a=a1_pk).order_by('b').select_related(depth=1).extra(select=
        {
        'extra_column': 
            "select slicing_FirstTable.id from slicing_FirstTable where slicing_FirstTable.id=%s" % (a1_pk,)
        })
        
        for i in (1,2,3):
            self.try_page(i, q)

class DistinctTestCase(TestCase):
    def testLimitDistinct(self):
        T = DistinctTable
        T(s='abc').save()
        T(s='abc').save()
        T(s='abc').save()
        T(s='def').save()
        T(s='def').save()
        T(s='fgh').save()
        T(s='fgh').save()
        T(s='fgh').save()
        T(s='fgh').save()
        T(s='ijk').save()
        T(s='ijk').save()
        T(s='xyz').save()
        
        baseQ = T.objects.values_list('s', flat=True).distinct()
        
        stuff = list(baseQ)
        self.assertEquals(len(stuff), 5)
        
        stuff = list(baseQ[:2])
        self.assertEquals(stuff, [u'abc', u'def'])

        stuff = list(baseQ[3:])
        self.assertEquals(stuff, [u'ijk', u'xyz'])

        stuff = list(baseQ[2:4])
        self.assertEquals(stuff, [u'fgh', u'ijk'])

    def testUnusedDistinct(self):
        T = DistinctTable
        T(s='abc').save()
        T(s='abc').save()
        T(s='abc').save()
        T(s='def').save()
        T(s='def').save()
        T(s='fgh').save()
        T(s='fgh').save()
        T(s='fgh').save()
        T(s='fgh').save()
        T(s='ijk').save()
        T(s='ijk').save()
        T(s='xyz').save()
        
        baseQ = T.objects.distinct()

        stuff = list(baseQ)
        self.assertEquals(len(stuff), 12)

        stuff = list(baseQ[:2])
        self.assertEquals(
            [o.s for o in stuff],
            [u'abc', u'abc'])

        stuff = list(baseQ[3:])
        self.assertEquals(
            [o.s for o in stuff], 
            [u'def', u'def', u'fgh', u'fgh', u'fgh', u'fgh', u'ijk', u'ijk', u'xyz'])

        stuff = list(baseQ[2:4])
        self.assertEquals(
            [o.s for o in stuff], 
            [u'abc', u'def'])
