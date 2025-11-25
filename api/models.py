from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


# ---------------------------------------------------------
# User Manager
# ---------------------------------------------------------
class CustomUserManager(BaseUserManager):
    """
    Manager for the custom User model.

    Email is used as the primary login field instead of username.
    """

    def create_user(self, username, email, password, role=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """
        Creates a superuser with all necessary permissions.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser requires is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser requires is_superuser=True")

        return self.create_user(username, email, password, **extra_fields)


# ---------------------------------------------------------
# User Model
# ---------------------------------------------------------
class User(AbstractUser):
    """
    Custom user model that authenticates using email instead of username.
    """

    ROLE_CHOICES = (
        ("vendor", "Vendor"),
        ("buyer", "Buyer"),
        ("admin", "Admin"),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "role"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email


# ---------------------------------------------------------
# User Profile
# ---------------------------------------------------------
class Profile(models.Model):
    """
    Additional user details stored separately from the main User model.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"


# ---------------------------------------------------------
# Wallet
# ---------------------------------------------------------
class Wallet(models.Model):
    """
    Each user has a wallet that stores available balance.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.email}'s Wallet (Balance: {self.balance})"


# ---------------------------------------------------------
# Transactions
# ---------------------------------------------------------
class Transaction(models.Model):
    """
    Represents money movements in a user's wallet.
    """

    TRANSACTION_TYPES = (
        ("sale", "Sale"),
        ("purchase", "Purchase"),
        ("withdrawal", "Withdrawal"),
        ("credit", "Credit"),
    )

    wallet = models.ForeignKey(Wallet, related_name="transactions", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.type} of {self.amount} for {self.wallet.user.email}"


# ---------------------------------------------------------
# Listing (Vendor Items)
# ---------------------------------------------------------
class Listing(models.Model):
    """
    Marketplace listing posted by vendors.
    Includes category, pricing, and optional geographic fields.
    """

    CATEGORY_CHOICES = (
        ("plastic", "Plastic"),
        ("metal", "Metal"),
        ("paper", "Paper"),
        ("e-waste", "E-waste"),
        ("glass", "Glass"),
        ("other", "Other"),
    )

    UNIT_CHOICES = (
        ("kg", "kg"),
        ("tons", "tons"),
    )

    STATUS_CHOICES = (
        ("available", "Available"),
        ("in-transit", "In Transit"),
        ("completed", "Completed"),
    )

    COUNTRY_CHOICES = (
        ("MY", "Malaysia"),
        ("SG", "Singapore"),
        ("ID", "Indonesia"),
        ("TH", "Thailand"),
        ("VN", "Vietnam"),
        ("PH", "Philippines"),
        ("IN", "India"),
        ("PK", "Pakistan"),
        ("BD", "Bangladesh"),
        ("LK", "Sri Lanka"),
        ("KH", "Cambodia"),
        ("LA", "Laos"),
        ("MM", "Myanmar"),
        ("BN", "Brunei"),
    )

    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="listings", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in RM")

    # Geographic information
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, default="MY")
    city = models.CharField(max_length=100, blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    location = models.CharField(max_length=255, blank=True)  # Legacy field

    image = models.ImageField(upload_to="listings_images/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ---------------------------------------------------------
# Orders
# ---------------------------------------------------------
class Order(models.Model):
    """
    Represents a purchase made by a buyer for a specific listing.
    """

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, related_name="orders", on_delete=models.SET_NULL, null=True)
    listing_title = models.CharField(max_length=255, blank=True)  # Stored for history even if listing changes
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sales", on_delete=models.CASCADE)

    quantity_bought = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.buyer.email}"


# ---------------------------------------------------------
# Messages (Chat)
# ---------------------------------------------------------
class Message(models.Model):
    """
    private message model for real-time chat.
    """
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="received_messages", on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"From {self.sender.email} to {self.receiver.email}"


# ---------------------------------------------------------
# Signals: auto-create Profile + Wallet
# ---------------------------------------------------------
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    """
    Automatically create a Profile and Wallet whenever a new user is created.
    """
    if created:
        Profile.objects.create(user=instance)
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile_and_wallet(sender, instance, **kwargs):
    """
    Ensure profile and wallet are saved if they already exist.
    """
    if hasattr(instance, "profile"):
        instance.profile.save()
    if hasattr(instance, "wallet"):
        instance.wallet.save()
