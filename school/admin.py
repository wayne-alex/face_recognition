from django.contrib import admin

from .models import Account, Class, Attendance, ClassCount, Enrollment


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'staff']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'teacher', 'ongoing']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'attended_class', 'timestamp']


@admin.register(ClassCount)
class ClassCountAdmin(admin.ModelAdmin):
    list_display = ['attended_class', 'count']


admin.site.register(Enrollment)
