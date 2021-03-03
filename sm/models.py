from django.db import models
from timescale.db.models.models import TimescaleModel

# Create your models here.
class Metric(TimescaleModel):
   temperature = models.FloatField()