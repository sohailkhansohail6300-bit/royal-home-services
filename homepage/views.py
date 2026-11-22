from django.shortcuts import render,redirect
from django.http import JsonResponse
from .models import Booking, Service
from admin2.models import Review 


def home(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        service = request.POST.get('service', '').strip()
        date = request.POST.get('date', '').strip()

        errors = {}

        if not name:
            errors['name'] = 'Please enter your full name.'
        if not phone or not phone.isdigit() or len(phone) <= 8:
            errors['phone'] = 'Please enter your phone number.'
        if not address:
            errors['address'] = 'Please enter your service address.'
        if not service:
            errors['service'] = 'Please select a cleaning service.'
        if not date:
            errors['date'] = 'Please select a preferred date.'

        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            })

        Booking.objects.create(
            full_name=name,
            phone_number=phone,
            service_address=address,
            cleaning_service=service,
            preferred_date=date
        )

        return JsonResponse({
            'success': True,
            'message': 'Your cleaning appointment has been booked successfully!'
        })
        
        
    reviews = Review.objects.filter(is_approved=True)[:3] 
    

# this is Service data ..................


    service_data=Service.objects.order_by('-created_at')
        

    return render(request, 'home.html',{'reviews':reviews, 'service_data':service_data})

