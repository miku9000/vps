from django.db import models

# Create your models here.
from django.conf import settings
User = settings.AUTH_USER_MODEL

class KliendiVM(models.Model):
    STATUS_CHOICES = [
        ('creating', 'Loomine'),
        ('running', 'Jookseb'),
        ('stopped', 'Peatatud'),
        ('error', 'Error')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    vmid = models.IntegerField(unique=True)
    node = models.CharField(max_length=255, default='miku')
    status = models.CharField(
        max_length = 20,
        choices = STATUS_CHOICES,
        default = 'creating'
    )
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.vmid} ({self.status})"