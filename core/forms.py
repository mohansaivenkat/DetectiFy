from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Report, Product

User = get_user_model()

# ---------------------- VERIFY FORM ----------------------
class VerifyForm(forms.Form):
    serial_number = forms.CharField(
        max_length=200,
        required=False,
        label="Serial Number",
        widget=forms.TextInput(attrs={
            "placeholder": "Enter serial number or scan QR",
            "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]"
        })
    )
    image = forms.ImageField(required=False, label="Upload product image (optional)")

    def clean(self):
        cleaned = super().clean()
        serial = cleaned.get("serial_number", "").strip()
        image = cleaned.get("image")
        if not serial and not image:
            raise forms.ValidationError("Please provide a serial number or upload an image to verify.")
        return cleaned


# ---------------------- REPORT FORM ----------------------
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ("product_serial", "product_name", "description", "evidence_image")
        widgets = {
            "product_serial": forms.TextInput(attrs={
                "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]",
                "placeholder": "Enter product serial"
            }),
            "product_name": forms.TextInput(attrs={
                "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]",
                "placeholder": "Enter product name"
            }),
            "description": forms.Textarea(attrs={
                "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]",
                "rows": 4,
                "placeholder": "Describe the issue or counterfeit suspicion"
            }),
        }


# ---------------------- PRODUCT FORM (Admin Only) ----------------------
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_name',
            'manufacturer',
            'serial_number',
            'manufacture_date',
            'description',
            'image',
            'is_genuine'
        ]
        widgets = {
            "product_name": forms.TextInput(attrs={
                "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]"
            }),
            "manufacturer": forms.TextInput(attrs={
                "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]"
            }),
            "serial_number": forms.TextInput(attrs={
                "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]",
                "placeholder": "Enter or auto-generate"
            }),
            "manufacture_date": forms.DateInput(attrs={
                "type": "date",
                "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]"
            }),
            "description": forms.Textarea(attrs={
                "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]",
                "rows": 4
            }),
            "is_genuine": forms.CheckboxInput(attrs={
                "class": "h-5 w-5 accent-[var(--btn-bg)]"
            }),
        }

    def clean_serial_number(self):
        serial = self.cleaned_data['serial_number']
        if Product.objects.filter(serial_number=serial).exists():
            raise forms.ValidationError("A product with this serial number already exists.")
        return serial


# ---------------------- CUSTOM USER FORM ----------------------
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Please enter a valid and active email address. (No verification will be sent)",
        widget=forms.EmailInput(attrs={
            "class": "p-3 rounded-lg w-full bg-[var(--card-bg)] text-[var(--text)] border border-[var(--border)]"
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email