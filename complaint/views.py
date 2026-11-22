from django.shortcuts import render,redirect,get_object_or_404
from django.http import Http404, JsonResponse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.dateparse import parse_date
from .models import CustomerComplaint
from homepage.models import Service,Category
from homepage.seo import category_page_seo, pick_service

def complaint(request):
    if request.method == 'POST':
        # Extract data
        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email_address = request.POST.get('email_address', '').strip()
        date_of_service = request.POST.get('date_of_service', '').strip()
        service_address = request.POST.get('service_address', '').strip()
        service_type = request.POST.get('service_type', '').strip()
        technician_name = request.POST.get('technician_name', '').strip()
        what_went_wrong = request.POST.get('what_went_wrong', '').strip()
        desired_resolution = request.POST.get('desired_resolution', '').strip()
        additional_details = request.POST.get('additional_details', '').strip()
        followup_preference = request.POST.get('followup_preference', '').strip()

        errors = {}

        # Validation
        if not full_name:
            errors['full_name'] = 'Please enter your full name.'
            
        if not phone_number or not phone_number.isdigit() or len(phone_number) <= 8:
            errors['phone_number'] = 'Please enter your phone number.'
            
        if not email_address:
            errors['email_address'] = 'Please enter your email address.'
        else:
            # Proper email validation
            try:
                validate_email(email_address)
            except ValidationError:
                errors['email_address'] = 'Please enter a valid email address.'
                
        # date_of_service is NOT NULL in the model: a blank/invalid value used to crash with HTTP 500.
        if not date_of_service:
            errors['date_of_service'] = 'Please select the date of service.'
        elif parse_date(date_of_service) is None:
            errors['date_of_service'] = 'Please enter a valid date.'
                
        if not what_went_wrong:
            errors['what_went_wrong'] = 'Please describe what went wrong.'
        
        # Return errors if any exist
        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            })

        # Save to database if no errors
        CustomerComplaint.objects.create(
            full_name=full_name,
            phone_number=phone_number,
            email_address=email_address,
            date_of_service=date_of_service,
            service_address=service_address,
            service_type=service_type,
            technician_name=technician_name,
            what_went_wrong=what_went_wrong,
            desired_resolution=desired_resolution,
            additional_details=additional_details,
            followup_preference=followup_preference
        )

        # Return success response
        return JsonResponse({
            'success': True,
            'message': 'Your complaint has been submitted successfully. Our team will review it and get back to you within 24-48 hours.'
        })
    
    # Render the complaint page for GET requests
    return render(request, 'complaint/complaint.html')

def about(request):
    return render(request, 'complaint/about.html')


def explor_views(request, slug):
    data = get_object_or_404(Category, slug=slug)

    # Previously get_object_or_404(Service, category=data): that raised MultipleObjectsReturned
    # (HTTP 500) as soon as a category had two services. Same result for one service; for several,
    # the newest is shown (matches Service.Meta.ordering). No service -> 404 as before.
    services = pick_service(data)
    if services is None:
        raise Http404("No service in this category")

    return render(request, 'complaint/explor_views.html', {
        'data': data,
        'services': services,
        'seo': category_page_seo(request, data, services),
    })