from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from carts.models import Cart

User = get_user_model()


class CartInline(admin.TabularInline):
    model = Cart
    fields = ('product', 'quantity', 'get_total_price', 'created_at', 'updated_at')
    readonly_fields = ('get_total_price', 'created_at', 'updated_at')
    extra = 0
    can_delete = True

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = 'Total Price'


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = [CartInline]

    # Fields to show in list view
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'verified')
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name')

    # Fields when viewing/editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'verified', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    # Fields when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2'),
        }),
    )
