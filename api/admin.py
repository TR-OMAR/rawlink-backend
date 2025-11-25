from django.contrib import admin
from .models import (
    User,
    Profile,
    Wallet,
    Transaction,
    Listing,
    Order,
    Message,
)


"""
Admin configuration for marketplace models.

Each ModelAdmin below configures how the model appears in the Django admin:
- list_display: columns shown in the changelist (table) view
- search_fields: fields the admin search box will query
- list_filter: sidebar filters for quick narrowing

"""


class UserAdmin(admin.ModelAdmin):
    """
    Admin for the User model.

    Shows (email, username) and role information so
    admins can quickly scan user rows. Searching on email and username helps
    locate accounts fast.
    """
    list_display = ("email", "username", "role", "is_staff")
    search_fields = ("email", "username")


class ProfileAdmin(admin.ModelAdmin):
    """
    Admin for user Profile data.

    The list shows the linked user plus human-friendly profile fields like name
    and phone. Searching by the related user's email (user__email) lets staff
    find profiles when they only have an account email.
    """
    list_display = ("user", "name", "phone", "location")
    search_fields = ("user__email", "name")


class WalletAdmin(admin.ModelAdmin):
    """
    Wallet admin.

    Display the wallet owner and current balance. Searching by the related user's
    email helps support quickly locate a user's wallet.
    """
    list_display = ("user", "balance")
    search_fields = ("user__email",)


class TransactionAdmin(admin.ModelAdmin):
    """
    Transaction admin.

    Show the wallet, transaction type and amount together with a timestamp.
    Add a list_filter on 'type' and 'timestamp' to let staff quickly narrow to
    date ranges or transaction kinds (refund, charge, payout, etc.).
    """
    list_display = ("wallet", "type", "amount", "timestamp")
    list_filter = ("type", "timestamp")


class ListingAdmin(admin.ModelAdmin):
    """
    Listing admin for items offered by vendors.

    list_display: key listing attributes so staff can quickly check status and price.
    list_filter: useful for filtering by listing status, category or vendor.
    search_fields: title and vendor email are the most common lookup fields.
    """
    list_display = (
        "title",
        "vendor",
        "category",
        "status",
        "price_per_unit",
        "unit",
    )
    list_filter = ("status", "category", "vendor")
    search_fields = ("title", "vendor__email")


class OrderAdmin(admin.ModelAdmin):
    """
    Order admin.

    Shows order id, buyer, vendor, a human-readable listing title, status and total.
    - If `listing_title` is a property/method on the Order model, make sure it is
      defined on the model and decorated with `@admin.display` (or has a
      `short_description`) so the label is readable here.
    - Consider using list_select_related(('buyer', 'vendor')) in get_queryset
      if the changelist feels slow due to related lookups.
    """
    list_display = ("id", "buyer", "vendor", "listing_title", "status", "total_price")
    list_filter = ("status", "vendor", "buyer")
    search_fields = ("buyer__email", "vendor__email")


class MessageAdmin(admin.ModelAdmin):
    """
    Simple admin for user messages.

    Show sender, receiver and timestamp. Searching by sender/receiver email is
    the most useful operation for support or dispute resolution.
    """
    list_display = ("sender", "receiver", "timestamp")
    search_fields = ("sender__email", "receiver__email")


# Register models with their respective admin classes.
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Message, MessageAdmin)
