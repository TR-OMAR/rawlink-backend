from django.db import transaction
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from .models import (
    User,
    Profile,
    Wallet,
    Transaction,
    Listing,
    Order,
    Message,
)


# -------------------------
# Auth / User Serializers
# -------------------------
class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for creating users via Djoser. Password is write-only.
    """
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "password", "role")
        extra_kwargs = {"password": {"write_only": True}}


class UserSerializer(serializers.ModelSerializer):
    """Lightweight user representation used across other serializers."""
    class Meta:
        model = User
        fields = ("id", "email", "username", "role")


# -------------------------
# Profile Serializer
# -------------------------
class ProfileSerializer(serializers.ModelSerializer):
    # Show related user using __str__ (email) for clarity in responses
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Profile
        fields = ("user", "name", "phone", "location")


# -------------------------
# Wallet & Transaction Serializers
# -------------------------
class TransactionSerializer(serializers.ModelSerializer):
    """Serialize individual wallet transactions."""
    class Meta:
        model = Transaction
        fields = ("id", "amount", "type", "timestamp")


class WalletSerializer(serializers.ModelSerializer):
    """
    Wallet serializer that nests recent transactions.
    Transactions are read-only here — they should be created via business logic.
    """
    transactions = TransactionSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Wallet
        fields = ("user", "balance", "transactions")


# -------------------------
# Listing Serializer
# -------------------------
class ListingSerializer(serializers.ModelSerializer):
    """
    Listing representation.
    """
    vendor = serializers.StringRelatedField(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(source="vendor", read_only=True)
    vendor_username = serializers.CharField(source="vendor.username", read_only=True)

    class Meta:
        model = Listing
        fields = (
            "id", "title", "description", "category", "quantity", "unit",
            "price_per_unit", "location", "image", "status", "created_at",
            "country", "city", "postal_code",
            "vendor", "vendor_id", "vendor_username",
        )
        read_only_fields = ("id", "created_at", "vendor", "vendor_id")


# -------------------------
# Message Serializer
# -------------------------
class MessageSerializer(serializers.ModelSerializer):
    """
    Message serializer for chat: both sender and receiver are returned
    as nested user objects (read-only).
    """
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "receiver", "content", "timestamp")
        read_only_fields = ("id", "sender", "timestamp")


# -------------------------
# Order Serializer (handles payment transfer + order creation)
# -------------------------
class OrderSerializer(serializers.ModelSerializer):
    """
    All DB changes happen inside an atomic block
    and rows involved are locked to prevent race conditions.
    """
    buyer = UserSerializer(read_only=True)
    vendor = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)

    # Inputs for creation
    listing_id = serializers.IntegerField(write_only=True)
    quantity_bought = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    payment_method = serializers.CharField(write_only=True, required=False, default="wallet")

    class Meta:
        model = Order
        fields = (
            "id", "buyer", "vendor", "listing", "listing_title",
            "total_price", "status", "created_at",
            "listing_id", "quantity_bought", "payment_method"
        )
        read_only_fields = ("id", "total_price", "status", "created_at", "listing_title", "buyer", "vendor", "listing")

    def create(self, validated_data):
        """
        Create an order and perform a wallet transfer when payment_method is 'wallet'.

        Key points:
        - select_for_update() locks rows so concurrent purchases can't oversell.
        - The whole operation is wrapped in transaction.atomic() to ensure
          consistency: either all changes persist, or none do.
        - Raises ValidationError on invalid state (insufficient funds, own listing, etc.).
        """
        listing_id = validated_data.pop("listing_id")
        quantity_bought = validated_data.pop("quantity_bought")
        payment_method = validated_data.pop("payment_method", "wallet")
        buyer = self.context["request"].user

        with transaction.atomic():
            # Lock the listing row and ensure it is available
            try:
                listing = Listing.objects.select_for_update().get(id=listing_id, status="available")
            except Listing.DoesNotExist:
                raise serializers.ValidationError("This listing is not available or does not exist.")

            # Prevent vendor buying their own listing
            if buyer.id == listing.vendor.id:
                raise serializers.ValidationError("You cannot buy your own listing.")

            # Validate requested quantity against inventory
            if quantity_bought > listing.quantity:
                raise serializers.ValidationError(f"Only {listing.quantity} {listing.unit} available.")

            total_price = listing.price_per_unit * quantity_bought

            # Handle wallet payment flow
            if payment_method == "wallet":
                # Lock buyer wallet
                try:
                    buyer_wallet = Wallet.objects.select_for_update().get(user=buyer)
                except Wallet.DoesNotExist:
                    raise serializers.ValidationError("Buyer wallet not found.")

                # Check balance
                if buyer_wallet.balance < total_price:
                    raise serializers.ValidationError(
                        f"Insufficient funds. Balance: {buyer_wallet.balance}, Required: {total_price}"
                    )

                # Lock vendor wallet (order of locking helps avoid deadlocks)
                try:
                    vendor_wallet = Wallet.objects.select_for_update().get(user=listing.vendor)
                except Wallet.DoesNotExist:
                    raise serializers.ValidationError("Vendor wallet not found.")

                # Perform balance update
                buyer_wallet.balance -= total_price
                vendor_wallet.balance += total_price

                # Save updated balances
                buyer_wallet.save()
                vendor_wallet.save()

                # Record transaction history
                Transaction.objects.create(wallet=buyer_wallet, amount=-total_price, type="purchase")
                Transaction.objects.create(wallet=vendor_wallet, amount=total_price, type="sale")

            # Create order record (status confirmed after successful payment)
            order = Order.objects.create(
                buyer=buyer,
                listing=listing,
                vendor=listing.vendor,
                listing_title=listing.title,
                quantity_bought=quantity_bought,
                total_price=total_price,
                status="confirmed"
            )

            # Update listing inventory and status
            listing.quantity -= quantity_bought
            if listing.quantity <= 0:
                listing.status = "completed"
            listing.save()

            return order
