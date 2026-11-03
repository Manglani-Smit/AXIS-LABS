from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('auth/', views.auth_view, name='auth'),
    path('dashboard/developer/', views.developer_dashboard_view, name='developer_dashboard'),
    path('dashboard/client/', views.client_dashboard_view, name='client_dashboard'),
    path('template/<int:template_id>/', views.template_workspace_view, name='template_workspace'),

    # API Endpoints
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('check-login-status/', views.check_login_status, name='check_login_status'),
    path('verify-login/<str:token>/<str:action>/', views.verify_login_action, name='verify_login_action'),
    path('analyze-architecture/', views.analyze_architecture, name='analyze_architecture'),

    # Stripe Payment Endpoints
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
]