from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    STATUS_CHOICES = [
        ('NONE', 'NONE'),
        ('PENDING', 'PENDING'),
        ('APPROVED', 'APPROVED'),
        ('REJECTED', 'REJECTED'),
    ]

    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('client', 'Client'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    developer_token = models.CharField(max_length=64, blank=True, null=True, unique=True)
    client_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    login_approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NONE')
    approval_token = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} // {self.role.upper()} [{self.login_approval_status}]"