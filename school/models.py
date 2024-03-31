# Create your models here.

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    staff = models.BooleanField(default=False)
    face = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    face_image = models.ImageField(upload_to='user_faces/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class Class(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True)
    secret_code = models.UUIDField(blank=True, null=True)
    teacher = models.ForeignKey(Account, on_delete=models.CASCADE)
    ongoing = models.BooleanField(default=False)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(Account, on_delete=models.CASCADE)
    enrolled_class = models.ForeignKey(Class, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} - {self.enrolled_class}"


class Attendance(models.Model):
    student = models.ForeignKey(Account, on_delete=models.CASCADE)
    attended_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.attended_class} - {self.timestamp}"


class ClassCount(models.Model):
    attended_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.attended_class} - {self.count}"


class Signed(models.Model):
    class_field = models.ForeignKey(Class, on_delete=models.CASCADE)
    student = models.ForeignKey(Account, on_delete=models.CASCADE)
    time = models.DateTimeField(default=timezone.now)
    remarks = models.CharField(max_length=255, default="Signed Attendance Successfully")

    def __str__(self):
        return f"{self.student} signed attendance for {self.class_field} at {self.time}"
