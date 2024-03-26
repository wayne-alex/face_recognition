from django.urls import path
from django.urls.converters import register_converter

from . import views


class FloatConverter:
    regex = '[-+]?\d*\.\d+|\d+'

    def to_python(self, value):
        return float(value)

    def to_url(self, value):
        return str(value)


register_converter(FloatConverter, 'float')

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard_staff/', views.dashboardStaff, name='dashboard_staff'),
    path('classes/', views.classes, name='classes'),
    path('add_class/', views.add_class, name='new_class'),
    path('face_recognition/', views.faceRecognition, name='face_recognition'),
    path('face_recognition_attendance/<int:classId>/', views.faceRecognitionAttendance,
         name='face_recognition_attendance'),
    path('delete/<int:id>', views.delete_class, name='delete_class'),
    path('end/<int:id>', views.end_class, name='end_class'),
    path('signed/<int:classId>', views.signed, name='signed'),
    path('enroll/<int:id>', views.enroll_class, name='enroll_class'),
    path('accountSetting/', views.accountSettings, name='account_settings'),
    path('take_attendance/<int:class_id>/<float:latitude>/<float:longitude>/', views.take_attendance,
         name='take_attendance'),

    path('sign_attendance/', views.sign_Attendance, name='sign_attendance'),
    path('generate_report/', views.generate_report, name='generate_report'),
    path('generate_report_staff/', views.generate_report_staff, name='generate_report_staff'),
    path('attendance_report/', views.attendance_report, name='attendance_report'),
    path('view_attendance/', views.view_attendance_staff, name='view_attendance'),
    path('update-secret-code/', views.update_secret_code, name='update_secret_code'),
    path('upload_image/', views.uploadImage, name='upload_image'),

    path('logout/', views.logout_user, name='log_out'),

]
