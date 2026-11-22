from django.urls import path

from . import views

urlpatterns = [
    path('adminlogin/', views.adminlogin, name='adminlogin'),
    path('dashboard/', views.dashboard, name='dashboard'),                       # redirects to Orders
    path('dashboard/orders/', views.orders_view, name='dashboard_orders'),
    path('dashboard/orders/<int:pk>/', views.order_detail_view, name='dashboard_order_detail'),
    path('dashboard/orders/<int:pk>/delete/', views.order_delete_view, name='dashboard_order_delete'),
    path('dashboard/employees/', views.employees_view, name='dashboard_employees'),
    path('dashboard/employees/<int:pk>/', views.employee_detail_view, name='dashboard_employee_detail'),
    path('dashboard/employees/<int:pk>/delete/', views.employee_delete_view, name='dashboard_employee_delete'),
    path('dashboard/complaints/', views.complaints_view, name='dashboard_complaints'),
    path('dashboard/complaints/<int:pk>/', views.complaint_detail_view, name='dashboard_complaint_detail'),
    path('dashboard/reviews/', views.reviews_view, name='dashboard_reviews'),
    path('dashboard/reviews/<int:pk>/approval/', views.review_approval_view, name='dashboard_review_approval'),
    path('dashboard/logout/', views.admin_logout, name='admin_logout'),
]
