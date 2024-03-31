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
    path('manual_attendance_submit/',views.manual_attendance_submit, name='manual_attendance_submit'),

    path('logout/', views.logout_user, name='log_out'),

    #     Admin
    path('ad_min/', views.admin, name='admin'),
    path('admin_lecturers/', views.lecturers, name='lecturers'),
    path('admin_addlecturers/', views.addLecturer, name='add_lecturer'),
    path('admin_viewlecturer/<int:lec_id>', views.viewLecturer, name='view_lecturer'),
    path('admin_students/', views.students, name='students'),
    path('admin_add_Students/', views.addStudent, name='add_student'),
    path('admin_edit_student/<int:lec_id>', views.editStudent, name='edit_student'),
    path('admin_classes/', views.classes_admin, name='classes_admin'),
    path('admin_add_class/', views.addClass, name='add_class'),
    path('admin_edit_class/<int:class_id>', views.editClass, name='edit_class'),
    path('delete_student/<int:id>', views.delete_student, name='delete_student'),
    path('delete_lecturer/<int:id>', views.delete_lecturer, name='delete_lecturer'),

]
