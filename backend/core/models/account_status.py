from django.db import models
from django.contrib.auth.models import User

class AccountStatus(models.Model):
    id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=7)
    account = models.ForeignKey(User, on_delete=models.CASCADE)
