from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class Kasutaja(AbstractUser):
    email = models.EmailField(unique=True)
    is_activated_user = models.BooleanField(default=False)