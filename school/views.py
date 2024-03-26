import base64
import io
import json
import math
import random

import cv2
import numpy as np
import requests
from PIL import Image
# Create your views here...
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image as Img
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .forms import SignUpForm
from .models import Account, Signed
from .models import Enrollment
from .models import User, Class, ClassCount, Attendance


def home(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            response = redirect('dashboard')
            response.set_cookie('stored_username', username)

            messages.success(request, "You have successfully signed in.")
            return response
        else:
            messages.error(request, "There was an error while signing in.")
            return redirect('home')

    else:
        return render(request, 'home.html')


def image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_image


def save_base64_image(base64_string, filename):
    with open(filename, "wb") as f:
        f.write(base64.b64decode(base64_string))


@csrf_exempt
def faceRecognition(request):
    if request.method == 'POST':
        if 'imageData' in request.FILES:
            image_data = request.FILES['imageData']
            username = request.POST.get('username')
            if not username:
                messages.error(request, 'No username found! Please log in with your username.')
                return JsonResponse({'error': 'No username found'}, status=400)

            try:
                acc = Account.objects.get(user__username=username)
                if not acc:
                    messages.error(request, 'Username is incorrect!')
                    return JsonResponse({'error': 'Username is incorrect'}, status=400)

                if not acc.face_image:
                    messages.error(request,
                                   "You have not enrolled your face image in the system. Please log in with your password to enroll.")
                    return JsonResponse({'error': 'Face image not enrolled'}, status=400)

                url = settings.FACE_RECOGNITION_URL
                img2_path = acc.face_image.path

                # Encode images to base64
                img1_base64 = image_to_base64(img2_path)

                # Resize the uploaded image if needed
                uploaded_image = Image.open(image_data)
                uploaded_image = uploaded_image.resize((acc.face_image.width, acc.face_image.height))

                # Convert resized image to base64
                buffer = io.BytesIO()
                uploaded_image.save(buffer, format="PNG")
                img2_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                data = {
                    'img1_base64': img1_base64,
                    'img2_base64': img2_base64
                }

                response = requests.post(url, json=data)

                verification_result = response.json().get('verified', False)

                if verification_result:
                    user = acc.user
                    login(request, user)
                    messages.success(request, "You have successfully signed in using your face.")
                    return JsonResponse({'message': 'Face recognition successful. User logged in.'}, status=200)
                else:
                    # Face recognition failed
                    messages.error(request, "Face verification failed! Please try again.")
                    return JsonResponse({'error': 'Face recognition failed'}, status=401)

            except Account.DoesNotExist:
                return JsonResponse({'error': 'User account not found'}, status=400)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
        else:
            return JsonResponse({'error': 'Missing image data'}, status=400)
    else:
        return render(request, 'face_recognition.html')


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)

            # Use the user object obtained after saving the form
            account = Account(user=user, staff=0)
            account.save()

            messages.success(request, "Successfully registered to Machakos University!. 👋 Welcome to our platform! "
                                      "We're glad to have you here. 🌟")
            return redirect('dashboard')
        else:
            messages.error(request, 'Form not valid! Check the form and try again.')
            return redirect('register')
    else:
        form = SignUpForm()
        return render(request, 'register.html', {'form': form})


def dashboard(request):
    if request.user.is_authenticated:
        account = get_object_or_404(Account, user__id=request.user.id)
        if account.staff:
            return redirect('dashboard_staff')
        else:
            student = Account.objects.get(user__id=request.user.id)
            enrolled_classes = Enrollment.objects.filter(student__user__id=request.user.id)
            enrolled_class_ids = enrolled_classes.values_list('enrolled_class__id', flat=True)
            classes = Class.objects.exclude(id__in=enrolled_class_ids)
            return render(request, 'dashboard.html',
                          {'student': student, 'classes': classes, 'enrolled_classes': enrolled_classes})

    else:
        return redirect('login')


def dashboardStaff(request):
    teacher = Account.objects.get(user__id=request.user.id)
    created_class_count = Class.objects.filter(teacher=teacher).count()

    # Get the total number of enrolled students for the teacher
    enrolled_student_count = Enrollment.objects.filter(enrolled_class__teacher=teacher).count()

    # Get the total number of attendance taken for the teacher
    attendance_taken_count = Attendance.objects.filter(attended_class__teacher=teacher).count()

    # Calculate the percentage of attendance
    percentage_attendance = (attendance_taken_count / enrolled_student_count) * 100 if enrolled_student_count > 0 else 0

    return render(request, 'dashboard_staff.html',
                  {'teacher': teacher, 'created_class_count': created_class_count,
                   'enrolled_student_count': enrolled_student_count,
                   'attendance_taken_count': attendance_taken_count, 'percentage_attendance': percentage_attendance})


def classes(request):
    teacher = Account.objects.get(user__id=request.user.id)
    _classes = Class.objects.filter(teacher=teacher)

    # Get the number of students enrolled in each class
    class_enrollment_count = [Enrollment.objects.filter(enrolled_class=class_obj).count() for class_obj in _classes]

    # Combine the classes and the number of enrolled students into a single dictionary
    classes_and_enrollment = zip(_classes, class_enrollment_count)

    return render(request, 'class.html', {'teacher': teacher, 'classes_and_enrollment': classes_and_enrollment})


def add_class(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        try:
            # Get the selected teacher
            teacher = Account.objects.get(user__id=request.user.id)
            new_class = Class.objects.create(
                name=name,
                code=code,
                teacher=teacher,
            )

            messages.success(request, f'Class for Lecturer {teacher.user.username} added successfully!')
            return redirect('classes')
        except Exception as e:
            messages.error(request, f'Error adding class: {e}')
            return redirect('classes')
    else:
        teacher = Account.objects.get(user__id=request.user.id)
        return render(request, 'add_newClass.html', {'teacher': teacher})


def delete_class(request, id):
    deleted_class = Class.objects.get(id=id)
    deleted_class.delete()
    messages.success(request, 'You have successfully deleted  class ' + str(id))
    return redirect('classes')


def end_class(request, id):
    startClass = Class.objects.get(id=id)
    startClass.ongoing = 0
    startClass.latitude = None
    startClass.longitude = None
    startClass.save()
    messages.success(request, 'You have successfully Ended attendance signing')
    return redirect('classes')


def enroll_class(request, id):
    enroll = Enrollment.objects.filter(enrolled_class__id=id)
    if enroll:
        enrolled_class = Class.objects.get(id=id)
        enroll.delete()
        messages.success(request, 'You have successfully un enrolled from class ' + str(enrolled_class.name))
        return redirect('dashboard')
    else:
        enrolled_class = Class.objects.get(id=id)
        enroll_class = Enrollment(student=Account.objects.get(user__id=request.user.id),
                                  enrolled_class=enrolled_class)
        enroll_class.save()
        messages.success(request, 'You have successfully enrolled to class ' + str(enrolled_class.name))
        return redirect('dashboard')


def take_attendance(request, class_id, latitude, longitude):
    classroom = get_object_or_404(Class, id=class_id)
    classroom.ongoing = True
    classroom.latitude = latitude
    classroom.longitude = longitude
    classroom.save()
    class_enrollment_count = Enrollment.objects.filter(enrolled_class=classroom).count()
    return render(request, 'take_attendance.html', {'classroom': classroom, 'count': class_enrollment_count})


@csrf_exempt
def update_secret_code(request):
    if request.method == 'POST':
        class_code = request.POST.get('class_code')
        secret_code = request.POST.get('secret_code')

        try:
            # Retrieve the Class object using the class_code
            class_obj = Class.objects.get(code=class_code)
            # Update the secret_code
            class_obj.secret_code = secret_code
            class_obj.save()

            return JsonResponse({'status': 'success'})
        except Class.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Class not found.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


def logout_user(request):
    messages.success(request, "You have successfully logged out")
    logout(request)
    return redirect('home')


@login_required
def accountSettings(request):
    user_id = request.user.id
    try:
        teacher = Account.objects.get(user__id=user_id)
        student = Account.objects.get(user__id=user_id)
    except Account.DoesNotExist:
        # Handle the case where the user account is not found
        messages.error(request, 'User account not found.')
        return redirect('home')  # Redirect to the home page or another appropriate view

    account = teacher if teacher.staff else student

    template_name = 'account_settings_staff.html' if teacher.staff else 'account_settings.html'
    context = {'account': account}
    return render(request, template_name, context)


def uploadImage(request):
    if request.method == 'POST':
        try:
            face_image = request.FILES['face_image']
            image = np.frombuffer(face_image.read(), np.uint8)
            image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30),
                                                  flags=cv2.CASCADE_SCALE_IMAGE)

            if len(faces) == 0:
                messages.error(request, "No face detected.Upload a picture with your face clearly seen!")
                return redirect("account_settings")
            elif len(faces) > 1:
                messages.error(request, "Multiple faces detected.Upload a picture with only one face clearly seen!")
                return redirect("account_settings")
            else:
                acc = Account.objects.get(user__id=request.user.id)
                acc.face_image = face_image
                acc.save()
                messages.success(request, "You have successfully enrolled your face!")
                return redirect('account_settings')
        except KeyError:
            messages.error(request, "Error: No face image provided.")
            return redirect('account_settings')
    else:
        return HttpResponseBadRequest("Bad Request: Invalid HTTP method.")


def sign_Attendance(request):
    user = request.user
    student_account = Account.objects.get(user=user)
    ongoing_classes = Class.objects.filter(ongoing=True, enrollment__student=student_account)
    return render(request, 'sign_attendance.html', {'classrooms': ongoing_classes})


@csrf_exempt
def signed(request, classId):
    # Get today's date
    today = timezone.now().date()
    # Filter Signed objects for the given class and today's date, ordered by time in descending order
    student_signed = Signed.objects.filter(class_field_id=classId, time__date=today).order_by('-time')

    # Serialize the queryset
    serialized_data = serialize('json', student_signed)

    # Return the serialized data in JSON format
    return JsonResponse(serialized_data, safe=False)


@csrf_exempt
def faceRecognitionAttendance(request, classId):
    if request.method == 'POST':
        if 'imageData' in request.FILES and 'latitude' in request.POST and 'longitude' in request.POST:
            image_data = request.FILES['imageData']
            username = request.user.username
            latitude = float(request.POST['latitude'])
            longitude = float(request.POST['longitude'])

            # checking the location of the teacher and student
            try:
                classroom = Class.objects.get(id=classId)
            except Class.DoesNotExist:
                return JsonResponse({'error': 'Class not found'}, status=404)

            teacher_latitude = classroom.latitude
            teacher_longitude = classroom.longitude

            # Calculate the distance between the teacher's and student's locations
            distance = haversine(latitude, longitude, teacher_latitude, teacher_longitude)

            if distance <= 100:
                try:
                    acc = Account.objects.get(user__username=username)

                    if not acc.face_image:
                        messages.success(request,
                                         "You have not Enrolled your Face Image In the System.Enroll Before continuing!")
                        return redirect('account_settings')
                    img2_path = acc.face_image.path
                    url = settings.FACE_RECOGNITION_URL

                    # Encode images to base64
                    img1_base64 = image_to_base64(img2_path)
                    img2_base64 = base64.b64encode(image_data.read()).decode('utf-8')

                    data = {
                        'img1_base64': img1_base64,
                        'img2_base64': img2_base64
                    }

                    response = requests.post(url, json=data)

                    if response.status_code == 200:
                        verification_result = response.json().get('verified', False)

                        if verification_result:
                            attend = Attendance(student=request.user.account, attended_class=classroom)
                            attend.save()
                            signed = Signed(class_field=classroom, student=request.user.account)
                            signed.save()
                            messages.success(request, "You have successfully signed the Attendance.☺️")
                            return JsonResponse({'success': True})
                        else:
                            # Face recognition failed
                            messages.error(request, "Face verification failed! Try again")
                            return JsonResponse({'success': False})
                    else:
                        messages.error(request, "Error in face recognition API. Please try again later.")
                        return JsonResponse({'success': False})

                except Account.DoesNotExist:
                    return JsonResponse({'error': 'User account not found'}, status=400)
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            else:
                print("Student is Farther than 100 meters")
                messages.success(request, "You are not within 100 meters of the classroom! Move near.")
                return JsonResponse({'error': 'Student is farther than 100 meters from the classroom'}, status=400)
        else:
            messages.success(request, "Image or Location not sent. Try Again.")
            return JsonResponse({'error': 'Image or Location not sent'}, status=400)
    else:
        return render(request, 'attend.html')


def haversine(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    radius_of_earth = 6371000
    distance = radius_of_earth * c

    return distance


def attendance_report(request):
    enrolled_classes = Enrollment.objects.filter(student=request.user.account)
    total_classes = 0
    attended_classes = 0
    for enrollment in enrolled_classes:
        total_classes += ClassCount.objects.filter(attended_class=enrollment.enrolled_class).count()
        attended_classes += Attendance.objects.filter(attended_class=enrollment.enrolled_class).count()

    # Handling division by zero error
    percentage_attendance = 0
    if total_classes > 0:
        percentage_attendance = (attended_classes / total_classes) * 100

    return render(request, 'view_attendance.html', {
        'enrolled_classes': enrolled_classes,
        'total_classes': total_classes,
        'attended_classes': attended_classes,
        'percentage_attendance': percentage_attendance,
    })


@csrf_exempt
def generate_report(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        class_id = data.get('class_id')
        user_id = data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            selected_class = get_object_or_404(Class, id=class_id)
            taught_class = ClassCount.objects.filter(attended_class=selected_class).count()
            attended_class = Attendance.objects.filter(attended_class=selected_class, student=user.account).count()
            serial_number = ''.join([str(random.randint(0, 9)) for _ in range(8)])

            # Get the current timestamp
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

            # Create a PDF buffer
            buffer = io.BytesIO()

            # Create a PDF document
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Define styles
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            institution_style = ParagraphStyle(name='Institution', parent=styles['Normal'], alignment=TA_CENTER,
                                               fontSize=16)
            header_style = ParagraphStyle(name='Header', parent=styles['Normal'], fontName='Helvetica-Bold',
                                          fontSize=14)
            left_style = ParagraphStyle(name='Left', parent=styles['Normal'], fontName='Helvetica-Bold',
                                        alignment=TA_LEFT, fontSize=12)
            right_style = ParagraphStyle(name='Right', parent=styles['Normal'], fontName='Helvetica-Bold',
                                         alignment=TA_RIGHT, fontSize=10)
            box_style = ParagraphStyle(name='Box', parent=styles['Normal'], textColor=colors.white,
                                       backColor=colors.blue,
                                       borderWidth=1, borderColor=colors.black)

            # Add timestamp
            elements.append(Paragraph(f"Generated on: {timestamp}", right_style))
            elements.append(Spacer(1, 0.5 * inch))

            # Add institution logo
            logo_path = finders.find('assets/img/Logo.png')
            logo_image = Img(logo_path, width=2 * inch, height=1 * inch)
            elements.append(logo_image)

            # Add institution name
            elements.append(Paragraph("Machakos University", institution_style))
            elements.append(Spacer(1, 0.25 * inch))

            # Add report title
            elements.append(Paragraph(f"Attendance Report for {selected_class.name}", header_style))
            elements.append(Spacer(1, 0.25 * inch))

            # Add report details
            class_info = [
                ["Student Name", f"{user.first_name} {user.last_name}"],
                ["Class Name", selected_class.name],
                ["Class Code", selected_class.code],
                ["Lecturer", f"{selected_class.teacher.user.first_name} {selected_class.teacher.user.last_name}"],
                ["Total Classes Taught", taught_class],
                ["Total Classes Attended", attended_class],
            ]

            if taught_class != 0:
                attendance_percentage = (attended_class / taught_class) * 100
                class_info.append(["Attendance Percentage", f"{attendance_percentage:.2f}%"])
            else:
                class_info.append(["Attendance Percentage", "N/A"])

            class_table = Table(class_info, colWidths=[1.5 * inch, 3 * inch])
            class_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(class_table)
            elements.append(Spacer(1, 0.25 * inch))

            # Add attendance note
            note_paragraph = Paragraph(f"<i>Note:</i> The attendance policy for this class is 75%.",
                                       styles['Normal'])
            elements.append(note_paragraph)
            elements.append(Spacer(1, 0.25 * inch))

            # Add footer
            footer_content = "This report is computer-generated without any erasing whatsoever."
            footer_paragraph = Paragraph(footer_content, styles['Normal'])
            elements.append(footer_paragraph)

            # Build PDF document
            doc.build(elements)

            # Reset buffer position to start
            buffer.seek(0)

            # Return PDF response
            response = HttpResponse(buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'
            return response
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("Invalid data provided")
    else:
        return HttpResponseBadRequest()


def view_attendance_staff(request):
    teacher = Account.objects.get(user__id=request.user.id)

    # Retrieve all classes taught by the teacher
    classes_created = Class.objects.filter(teacher=request.user.account)

    # Initialize lists to store data for each class
    class_data = []

    # Iterate over each class to gather data
    for class_obj in classes_created:
        class_name = class_obj.name
        total_classes_taught = ClassCount.objects.filter(attended_class=class_obj).count()
        attendance_counts = Attendance.objects.filter(attended_class=class_obj).count()

        # Append class data to the list
        class_data.append({
            'class_name': class_name,
            'total_classes_taught': total_classes_taught,
            'attendance_counts': attendance_counts
        })

    # Convert the class_data list to JSON format
    class_data_json = json.dumps(class_data)

    return render(request, 'view_attendance_staff.html', {
        'teacher': teacher,
        'class_created': classes_created,
        'class_data_json': class_data_json,
    })


@csrf_exempt
def generate_report_staff(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        class_id = data.get('class_id')
        user_id = data.get('user_id')
        report_type = data.get('report_type')
        print(report_type)

        if int(report_type) == 1:
            # class report
            try:
                user = User.objects.get(id=user_id)
                selected_class = get_object_or_404(Class, id=class_id)
                taught_class = ClassCount.objects.filter(attended_class=selected_class).count()
                no_of_students = Enrollment.objects.filter(enrolled_class=selected_class).count()
                attended_class = Attendance.objects.filter(attended_class=selected_class).count()
                # Get the current timestamp
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

                # Create a PDF buffer
                buffer = io.BytesIO()

                # Create a PDF document
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []

                # Define styles
                styles = getSampleStyleSheet()
                title_style = styles['Title']
                institution_style = ParagraphStyle(name='Institution', parent=styles['Normal'], alignment=TA_CENTER,
                                                   fontSize=16)
                header_style = ParagraphStyle(name='Header', parent=styles['Normal'], fontName='Helvetica-Bold',
                                              fontSize=14)
                left_style = ParagraphStyle(name='Left', parent=styles['Normal'], fontName='Helvetica-Bold',
                                            alignment=TA_LEFT, fontSize=12)
                right_style = ParagraphStyle(name='Right', parent=styles['Normal'], fontName='Helvetica-Bold',
                                             alignment=TA_RIGHT, fontSize=10)
                box_style = ParagraphStyle(name='Box', parent=styles['Normal'], textColor=colors.white,
                                           backColor=colors.blue,
                                           borderWidth=1, borderColor=colors.black)

                elements.append(Paragraph(f"Generated on: {timestamp}", right_style))
                elements.append(Spacer(1, 0.5 * inch))

                # Add institution logo
                logo_path = finders.find('assets/img/Logo.png')
                logo_image = Img(logo_path, width=1 * inch, height=1 * inch)
                elements.append(logo_image)

                # Add institution name
                elements.append(Paragraph("Machakos University.", institution_style))
                elements.append(Spacer(1, 0.5 * inch))

                # Add report title
                elements.append(Paragraph(f"Attendance Report For  {selected_class.name}", header_style))
                elements.append(Spacer(1, 0.25 * inch))

                # Add report details
                class_info = [
                    ["Class Name ", selected_class.name],
                    ["Class Code ", selected_class.code],
                    ["Lecturer ", f"{selected_class.teacher.user.first_name} {selected_class.teacher.user.last_name}"],
                    ["Student(s) Enrolled ", no_of_students],
                    ["Total Classes Taught ", taught_class],
                    ["Total Classes Attended ", attended_class],
                ]
                if taught_class != 0:
                    attendance_percentage = (attended_class / taught_class) * 100
                    class_info.append(["Attendance Percentage", f"{attendance_percentage:.2f}%"])
                else:
                    class_info.append(["Attendance Percentage", "N/A"])

                class_table = Table(class_info, colWidths=[1.5 * inch, 3 * inch])
                class_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(class_table)
                elements.append(Spacer(1, 0.25 * inch))

                # Add attendance note
                note_paragraph = Paragraph(f"<i>Note:</i> The attendance policy for this class is 75%.",
                                           styles['Normal'])
                elements.append(note_paragraph)
                elements.append(Spacer(1, 0.25 * inch))

                # Add footer
                footer_content = "This report is computer-generated without any erasing whatsoever."
                footer_paragraph = Paragraph(footer_content, styles['Normal'])
                elements.append(footer_paragraph)

                # Build PDF document
                doc.build(elements)

                # Reset buffer position to start
                buffer.seek(0)

                # Return PDF response
                response = HttpResponse(buffer.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'
                return response
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("Invalid data provided")
        #     Class Report
        else:
            try:
                user = User.objects.get(id=user_id)
                selected_class = get_object_or_404(Class, id=class_id)
                taught_class = ClassCount.objects.filter(attended_class=selected_class).count()
                no_of_students = Enrollment.objects.filter(enrolled_class=selected_class).count()
                enrolled_students = Enrollment.objects.filter(enrolled_class=selected_class)

                def percentage_attendance(taught_class, no_of_attended):
                    if taught_class > 0:
                        return (no_of_attended / taught_class) * 100
                    else:
                        return 0

                # Get the current timestamp
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

                # Create a PDF buffer
                buffer = io.BytesIO()

                # Create a PDF document
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []

                # Define styles
                styles = getSampleStyleSheet()
                title_style = styles['Title']
                institution_style = ParagraphStyle(name='Institution', parent=styles['Normal'], alignment=TA_CENTER,
                                                   fontSize=16)
                header_style = ParagraphStyle(name='Header', parent=styles['Normal'], fontName='Helvetica-Bold',
                                              fontSize=14)
                left_style = ParagraphStyle(name='Left', parent=styles['Normal'], fontName='Helvetica-Bold',
                                            alignment=TA_LEFT, fontSize=12)
                right_style = ParagraphStyle(name='Right', parent=styles['Normal'], fontName='Helvetica-Bold',
                                             alignment=TA_RIGHT, fontSize=9)
                box_style = ParagraphStyle(name='Box', parent=styles['Normal'], textColor=colors.white,
                                           backColor=colors.blue,
                                           borderWidth=1, borderColor=colors.black)

                # Add timestamp
                elements.append(Paragraph(f"Generated on: {timestamp}", right_style))
                elements.append(Spacer(1, 0.5 * inch))

                # Add institution logo
                logo_path = finders.find('assets/img/Logo.png')
                logo_image = Img(logo_path, width=1 * inch, height=1 * inch)
                elements.append(logo_image)

                # Add institution name
                elements.append(Paragraph("Machakos University.", institution_style))
                elements.append(Spacer(1, 0.25 * inch))

                # Add report title
                elements.append(Paragraph(f"Attendance Report For {selected_class.name}", header_style))
                elements.append(Spacer(1, 0.25 * inch))

                # Add lecturer name and number of students
                elements.append(Paragraph(f"Lecturer Name: {selected_class.teacher.user.first_name} "
                                          f"{selected_class.teacher.user.last_name}", left_style))
                elements.append(Paragraph(f"No of Students: {no_of_students}", left_style))
                elements.append(Spacer(1, 0.25 * inch))

                # Add table header
                table_data = [['S/n', 'Student Name', 'Admission No.', 'Attendance Percentage']]

                # Loop through enrolled students and add to table
                for index, enrolled_student in enumerate(enrolled_students):
                    student_name = f"{enrolled_student.student.user.first_name} {enrolled_student.student.user.last_name}"
                    admission_number = 'J17-5576-2020'  # enrolled_student.student.admission_number

                    # Count the number of times the student attended the class
                    no_attended = Attendance.objects.filter(student=enrolled_student.student,
                                                            attended_class=selected_class).count()

                    # Calculate attendance percentage
                    attendance_percentage = percentage_attendance(taught_class, no_attended)

                    table_data.append([index + 1, student_name, admission_number, attendance_percentage])

                # Create table
                class_table = Table(table_data, colWidths=[0.5 * inch, 2 * inch, 1.5 * inch, 2 * inch])
                class_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(class_table)
                elements.append(Spacer(1, 0.25 * inch))

                # Add attendance note
                note_paragraph = Paragraph(f"<i>Note:</i> The attendance policy for this class is 75%.",
                                           styles['Normal'])
                elements.append(note_paragraph)
                elements.append(Spacer(1, 0.25 * inch))

                # Add footer
                footer_content = "This report is computer-generated without any erasing whatsoever."
                footer_paragraph = Paragraph(footer_content, styles['Normal'])
                elements.append(footer_paragraph)

                # Build PDF document
                doc.build(elements)

                # Reset buffer position to start
                buffer.seek(0)

                # Return PDF response
                response = HttpResponse(buffer.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'
                return response
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("Invalid data provided")
