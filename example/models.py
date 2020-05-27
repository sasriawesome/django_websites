from django.db import models
from django.contrib import admin
from django.db import models
from django.utils import translation


class Person(models.Model):

    name = models.CharField(max_length=50)