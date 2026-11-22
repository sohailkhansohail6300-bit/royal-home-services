from django.shortcuts import render
from django.http import JsonResponse
from .models import EmployeeRegistration


from django.http import JsonResponse
from django.shortcuts import render
from .models import EmployeeRegistration

def employee(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', '').strip()
        location = request.POST.get('location', '').strip()
        terms = request.POST.get('terms')

        errors = {}

        # --- Validation ---
        if not name:
            errors['name'] = 'Please enter your full name.'

        if not email:
            errors['email'] = 'Please enter your email address.'
        elif '@' not in email:
            errors['email'] = 'Please enter a valid email address.'

        if not phone or not phone.isdigit() or len(phone) <= 8:
            errors['phone'] = 'Please enter your phone number.'

        if not department:
            errors['department'] = 'Please select your department.'

        if not location:
            errors['location'] = 'Please enter your location.'

        if not terms:
            errors['terms'] = 'You must agree to the Terms and Conditions.'

        if not errors and EmployeeRegistration.objects.filter(email=email).exists():
            errors['email'] = 'This email is already registered.'

        # --- Return Errors ---
        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            })

        # --- Save ---
        EmployeeRegistration.objects.create(
            username=name,
            email=email,
            phone_number=phone,
            department=department,
            em_location=location
        )

        return JsonResponse({
            'success': True,
            'message': 'Your registration has been submitted successfully!'
        })

    return render(request, 'employe/employe.html')