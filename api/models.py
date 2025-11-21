from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


# --- 1. Custom User Manager ---
class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, username, email, password, role=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # create_user accepts role as a kwarg in extra_fields
        return self.create_user(username, email, password, **extra_fields)


# --- 2. Custom User Model ---
class User(AbstractUser):
    ROLE_CHOICES = (
        ('vendor', 'Vendor'),
        ('buyer', 'Buyer'),
        ('admin', 'Admin'),
    )

    # Use email as the unique identifier
    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


# --- 3. Profile Model ---
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"


# --- 4. Wallet Model ---
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.email}'s Wallet (Balance: {self.balance})"


# --- 5. Transaction Model ---
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('withdrawal', 'Withdrawal'),
        ('credit', 'Credit'),
    )
    wallet = models.ForeignKey(Wallet, related_name='transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.type} of {self.amount} for {self.wallet.user.email}"


# --- 6. Listing Model (merged with additional country/city/postal fields) ---
class Listing(models.Model):
    CATEGORY_CHOICES = (
        ('plastic', 'Plastic'),
        ('metal', 'Metal'),
        ('paper', 'Paper'),
        ('e-waste', 'E-waste'),
        ('glass', 'Glass'),
        ('other', 'Other'),
    )
    UNIT_CHOICES = (
        ('kg', 'kg'),
        ('tons', 'tons'),
    )
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('in-transit', 'In Transit'),
        ('completed', 'Completed'),
    )

    COUNTRY_CHOICES = (
        ('MY', 'Malaysia'),
        ('SG', 'Singapore'),
        ('ID', 'Indonesia'),
        ('TH', 'Thailand'),
        ('VN', 'Vietnam'),
        ('PH', 'Philippines'),
        ('IN', 'India'),
        ('PK', 'Pakistan'),
        ('BD', 'Bangladesh'),
        ('LK', 'Sri Lanka'),
        ('KH', 'Cambodia'),
        ('LA', 'Laos'),
        ('MM', 'Myanmar'),
        ('BN', 'Brunei'),
    )

    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='listings', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in RM")

    # New location-related fields
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, default='MY')
    city = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    # Keep 'location' for backward compatibility
    location = models.CharField(max_length=255, blank=True)

    image = models.ImageField(upload_to='listings_images/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# --- 7. Order Model ---
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, related_name='orders', on_delete=models.SET_NULL, null=True)
    listing_title = models.CharField(max_length=255, blank=True)
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sales', on_delete=models.CASCADE)

    quantity_bought = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.buyer.email}"


# --- 8. Message Model ---
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender.email} to {self.receiver.email}"


# --- 9. Signals to auto-create Profile and Wallet ---
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile_and_wallet(sender, instance, **kwargs):
    # If profile/wallet were just created this will still succeed.
    if hasattr(instance, 'profile'):
        instance.profile.save()
    if hasattr(instance, 'wallet'):
        instance.wallet.save()
