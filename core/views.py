# core/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from .models import Product, Report, CounterfeitSerial
from .forms import (
    CustomUserCreationForm,
    VerifyForm,
    ReportForm,
    ProductForm,
)

# ---------------------------
# Helpers
# ---------------------------
def is_staff_user(user):
    return user.is_active and user.is_staff


# ---------------------------
# Auth / Registration
# ---------------------------
def register(request):
    """Handle user registration and auto-login."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data.get('password1')
            authenticated_user = authenticate(request, username=user.username, password=raw_password)
            if authenticated_user:
                # Explicit backend for multi-backend setups
                login(request, authenticated_user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect('home')
        messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


# ---------------------------
# Product management (Staff)
# ---------------------------
@user_passes_test(is_staff_user)
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)  # include FILES for images
        if form.is_valid():
            form.save()
            messages.success(request, "Product added to registry.")
            return redirect("add_product")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm()
    return render(request, "core/add_product.html", {"form": form})


@user_passes_test(is_staff_user)
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product details updated successfully.")
            return redirect('product_list')
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)
    # Reuse add_product template in edit mode
    return render(request, "core/add_product.html", {"form": form, "edit_mode": True})


@user_passes_test(is_staff_user)
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
    return redirect('product_list')


def product_list(request):
    """Public page: show genuine products (no serial numbers)."""
    products = Product.objects.filter(is_genuine=True).order_by('-created_at')
    return render(request, 'core/product_list.html', {'products': products})


def counterfeit_products(request):
    from django.core.paginator import Paginator
    from .models import Report, Product

    qs = Report.objects.filter(status="approved").order_by("-reported_at")

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Fetch any matching products to use their image if report has none
    serials = [r.product_serial for r in page_obj.object_list if r.product_serial]
    product_map = {
        p.serial_number: p for p in Product.objects.filter(serial_number__in=serials)
    }

    # Attach fallback product to each report
    for rep in page_obj:
        rep.fallback_product = product_map.get(rep.product_serial)

    return render(
        request,
        "core/counterfeit_list.html",
        {"reports": page_obj},
    )

# ---------------------------
# Verification
# ---------------------------
def verify(request):
    """
    Verify logic priority:
    1) If serial exists in CounterfeitSerial → counterfeit
    2) Else if serial matches a Product:
         - if is_genuine=True → genuine
         - else → counterfeit
    3) Else → unknown
    """
    result = None
    form = VerifyForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        serial = form.cleaned_data.get("serial_number", "").strip()

        # 1) Counterfeit list check
        cf = CounterfeitSerial.objects.filter(serial_number=serial).first()
        if cf:
            # Try to show the related product image if exists, else counterfeit evidence
            product = Product.objects.filter(serial_number=serial).first()
            result = {"status": "counterfeit", "product": product, "counterfeit": cf}
            messages.error(request, "Warning: This serial has been flagged as COUNTERFEIT.")
        else:
            # 2) Registered product?
            try:
                product = Product.objects.get(serial_number=serial)
                if product.is_genuine:
                    result = {"status": "genuine", "product": product}
                    messages.success(request, "Product verified as genuine.")
                else:
                    result = {"status": "counterfeit", "product": product}
                    messages.error(request, "Warning: This product has been flagged as COUNTERFEIT.")
            except Product.DoesNotExist:
                # 3) Unknown
                result = {"status": "unknown", "serial": serial}
                messages.warning(request, "No match found. Product may be counterfeit or unregistered.")

    return render(request, "core/verify.html", {"form": form, "result": result})


# ---------------------------
# Reports (User)
# ---------------------------
@login_required
def report_counterfeit(request):
    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            rep = form.save(commit=False)
            rep.reporter = request.user
            rep.status = "pending"  # <- explicit is fine (default should do it too)
            rep.resolved = False
            rep.save()
            messages.success(request, "Report submitted. Admin will review it.")
            return redirect("report")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReportForm()

    reports = Report.objects.filter(reporter=request.user).order_by("-reported_at")
    return render(request, "core/report.html", {"form": form, "reports": reports})


# ---------------------------
# Reports Review (Admin)
# ---------------------------
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Report, CounterfeitSerial, Product

def is_staff_user(user):
    return user.is_active and user.is_staff

@user_passes_test(is_staff_user)
def admin_report_queue(request):
    """
    Admin review queue: show only pending reports.
    """
    reports = Report.objects.filter(status='pending').order_by('-reported_at')
    return render(request, "core/reports_admin.html", {"reports": reports})


@user_passes_test(is_staff_user)
def approve_report(request, pk):
    """
    Approve a report: create/update counterfeit entry, mark product counterfeit if exists,
    and mark report as approved.
    """
    report = get_object_or_404(Report, pk=pk)
    if request.method != "POST":
        return redirect("admin_report_queue")

    # Create CounterfeitSerial if not present
    cf, created = CounterfeitSerial.objects.get_or_create(
        serial_number=report.product_serial.strip(),
        defaults={
            "product_name": report.product_name,
            "notes": f"Approved via report #{report.id}",
            "evidence_image": report.evidence_image,
            "source_report": report,
            "created_by": request.user,
        }
    )

    # If there is a product with same serial, mark it as not genuine
    try:
        product = Product.objects.get(serial_number=report.product_serial.strip())
        product.is_genuine = False
        product.save()
    except Product.DoesNotExist:
        pass

    report.status = "approved"
    report.resolved = True
    report.admin_notes = (report.admin_notes or "") + "\nApproved by admin."
    report.save()

    messages.success(request, f"Report #{report.id} approved.")
    return redirect("admin_report_queue")


@user_passes_test(is_staff_user)
def reject_report(request, pk):
    """
    Reject a report: mark as rejected, keep for record.
    """
    report = get_object_or_404(Report, pk=pk)
    if request.method != "POST":
        return redirect("admin_report_queue")

    report.status = "rejected"
    report.resolved = True
    report.admin_notes = (report.admin_notes or "") + "\nRejected by admin."
    report.save()

    messages.info(request, f"Report #{report.id} rejected.")
    return redirect("admin_report_queue")


# ---------------------------
# Static pages
# ---------------------------
def home(request):
    features = [
        {"icon": "shield", "title": "Advanced Security", "description": "Military-grade encryption and blockchain technology to ensure product authenticity verification."},
        {"icon": "bolt", "title": "Instant Results", "description": "Get verification results in milliseconds with AI-powered checks."},
        {"icon": "analytics", "title": "Detailed Analytics", "description": "Access comprehensive reports and analytics to track counterfeit patterns."},
        {"icon": "public", "title": "Global Database", "description": "Connected to international product registries for global coverage."},
        {"icon": "psychology", "title": "Built-In QR Scanner", "description": "Easily scan product QR codes using your device camera for quick verification."},
        {"icon": "devices", "title": "Multi-Platform", "description": "Access from any device — web, mobile, or integrate via API."},
    ]
    return render(request, "core/home.html", {"features": features})


def about(request):
    return render(request, "core/about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"New Contact Message from {name}"
        body = f"From: {name}\nEmail: {email}\n\nMessage:\n{message}"

        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_RECEIVER_EMAIL],
                fail_silently=False,
            )
            messages.success(request, "Thank you! Your message has been sent successfully.")
        except Exception as e:
            messages.error(request, f"Error sending message: {e}")

    return render(request, "core/contact.html")