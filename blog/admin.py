from django.utils.html import format_html
from django.contrib import admin
from .models import *


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'title', 'price', 'offPrice', 'author', 'publish', 'status')
    list_filter = ('author', 'status')
    list_editable = ('status', 'price', 'offPrice')  # Now you can edit price directly from list view
    search_fields = ('title', 'description')
    ordering = ('status', 'publish')
    raw_id_fields = ('author',)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ('thumbnail',)  # Show image preview inside edit form

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'description', 'image', 'thumbnail', 'price', 'offPrice', 'tags', 'status')
        }),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:5px;" />', obj.image.url)
        return "-"
    thumbnail.short_description = 'Image'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            kwargs["queryset"] = User.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'email')
    list_filter = ('user',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'transaction_id')
    list_filter = ('customer', )


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order', 'city', 'date_added')
    list_filter = ('customer',)


# @admin.register(Customer)
# class CustomerAdmin(admin.ModelAdmin):
#     list_display = ('user', 'name', 'email')
#     list_filter = ('user',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'date_added')
    list_filter = ('product', 'order')


@admin.register(IPAddress)
class IPAddressAdmin(admin.ModelAdmin):
    list_display = ('ip_address',)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'valid_from', 'valid_to', 'discount', 'active')
    list_editable = ('active',)



@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'active')
    list_editable = ('active',)