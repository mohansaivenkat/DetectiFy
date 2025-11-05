from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # =========================
    # 🌐 Public Pages
    # =========================
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    


    # =========================
    # 🔹 Product Verification & Reporting
    # =========================
    path('verify/', views.verify, name='verify'),
    path('report/', views.report_counterfeit, name='report'),
    
     # Products
    path('products/', views.product_list, name='product_list'),
    path("counterfeit/", views.counterfeit_products, name="counterfeit_products"),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='delete_product'),

    # Reports (admin moderation)
    path('admin/reports/', views.admin_report_queue, name='admin_report_queue'),
    path('admin/reports/<int:pk>/approve/', views.approve_report, name='approve_report'),
    path('admin/reports/<int:pk>/reject/', views.reject_report, name='reject_report'),

    # =========================
    # 🔹 Staff-Only Product Management
    # =========================
    path('add-product/', views.add_product, name='add_product'),

    # =========================
    # 🔐 Authentication
    # =========================
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='home'
    ), name='logout'),
    path('register/', views.register, name='register'),

    # =========================
    # 🔑 Password Reset
    # =========================
    path('password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='core/password_reset.html'
        ),
        name='password_reset'
    ),
    path('password_reset_done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='core/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='core/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path('reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='core/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]