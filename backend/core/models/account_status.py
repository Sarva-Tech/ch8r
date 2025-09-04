from django.db import models
from django.contrib.auth.models import User


class AccountStatus(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
    ]

    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default='PENDING')
    account = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account.username} - {self.status}"