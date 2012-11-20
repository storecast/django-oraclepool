from django.db import models

class OneTable(models.Model):
    b = models.CharField(max_length=100)
    c = models.CharField(default=u'test', max_length=10)
    
    def __repr__(self):
        return '<OneTable %s: %s, %s>' % (self.pk, self.b, self.c)


class TwoTable(models.Model):
    a = models.ForeignKey(OneTable)
    b = models.CharField(max_length=100)
    
    def __repr__(self):
        return '<TwoTable %s: %s>' % (self.pk, self.b)
