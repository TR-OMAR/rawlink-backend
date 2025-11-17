from django.contrib import admin
from .models import (
    User, 
    Profile, 
    Wallet, 
    Transaction, 
    Listing, 
    Order, 
    Message
)

# We use ModelAdmin classes for better display

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'role', 'is_staff')
    search_fields = ('email', 'username')

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'phone', 'location')
    search_fields = ('user__email', 'name')

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__email',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'type', 'amount', 'timestamp')
    list_filter = ('type', 'timestamp')

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'vendor', 'category', 'status', 'price_per_unit', 'unit')
    list_filter = ('status', 'category', 'vendor')
    search_fields = ('title', 'vendor__email')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'vendor', 'listing_title', 'status', 'total_price')
    list_filter = ('status', 'vendor', 'buyer')
    search_fields = ('buyer__email', 'vendor__email')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'timestamp')
    search_fields = ('sender__email', 'receiver__email')


# Register your models with their custom admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Message, MessageAdmin)