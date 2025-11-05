from django.contrib import admin
from .models import Product, Report

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'serial_number', 'manufacturer', 'is_genuine')
    list_filter = ('is_genuine', 'manufacturer')
    search_fields = ('product_name', 'serial_number')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_serial', 'reporter', 'resolved')
    list_filter = ('resolved',)
    actions = ['mark_as_counterfeit']

    def mark_as_counterfeit(self, request, queryset):
        for report in queryset:
            try:
                product = Product.objects.get(serial_number=report.product_serial)
                product.is_genuine = False
                product.save()
                report.resolved = True
                report.admin_notes = "Marked as counterfeit by admin."
                report.save()
            except Product.DoesNotExist:
                pass
        self.message_user(request, "Selected reports have been reviewed and product marked as counterfeit.")
    mark_as_counterfeit.short_description = "Mark as counterfeit & resolve report"