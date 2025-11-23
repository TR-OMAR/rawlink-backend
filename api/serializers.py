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
    Message
)

# --- Auth Serializers ---
class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password', 'role')
        extra_kwargs = {'password': {'write_only': True}}

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'role')

# --- Profile Serializer ---
class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Profile
        fields = ('user', 'name', 'phone', 'location')

# --- Wallet Serializers ---
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'amount', 'type', 'timestamp')

class WalletSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Wallet
        fields = ('user', 'balance', 'transactions')

# --- Listing Serializer ---
class ListingSerializer(serializers.ModelSerializer):
    # We use the 'vendor' field to display the name, but we also want the ID if needed
    vendor = serializers.StringRelatedField(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(source='vendor', read_only=True)
    vendor_username = serializers.CharField(source='vendor.username', read_only=True)

    class Meta:
        model = Listing
        fields = (
            'id', 'title', 'description', 'category', 'quantity', 'unit',
            'price_per_unit', 'location', 'image', 'status', 'created_at',
            'country', 'city', 'postal_code', # Ensure these are included!
            'vendor', 'vendor_id', 'vendor_username'
        )
        read_only_fields = ('id', 'created_at', 'vendor', 'vendor_id')

# --- Message Serializer ---
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'sender', 'receiver', 'content', 'timestamp')
        read_only_fields = ('id', 'sender', 'timestamp')

# --- Order Serializer (TRANSACTION SAFE) ---
class OrderSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    vendor = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    
    listing_id = serializers.IntegerField(write_only=True)
    quantity_bought = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    payment_method = serializers.CharField(write_only=True, required=False, default='wallet')

    class Meta:
        model = Order
        fields = (
            'id', 'buyer', 'vendor', 'listing', 'listing_title',
            'total_price', 'status', 'created_at',
            'listing_id', 'quantity_bought', 'payment_method'
        )
        read_only_fields = ('id', 'total_price', 'status', 'created_at', 'listing_title', 'buyer', 'vendor', 'listing')

    def create(self, validated_data):
        # We extract data here, but all DB operations happen inside atomic block
        listing_id = validated_data.pop('listing_id')
        quantity_bought = validated_data.pop('quantity_bought')
        payment_method = validated_data.pop('payment_method', 'wallet')
        buyer = self.context['request'].user

        # ATOMIC TRANSACTION BLOCK START
        with transaction.atomic():
            # 1. Lock the Listing Row (prevent others from buying same item simultaneously)
            try:
                listing = Listing.objects.select_for_update().get(id=listing_id, status='available')
            except Listing.DoesNotExist:
                raise serializers.ValidationError("This listing is not available or does not exist.")

            # Validation
            if buyer.id == listing.vendor.id:
                raise serializers.ValidationError("You cannot buy your own listing.")

            if quantity_bought > listing.quantity:
                raise serializers.ValidationError(f"Only {listing.quantity} {listing.unit} available.")

            total_price = listing.price_per_unit * quantity_bought

            # 2. Handle Wallet Payment (with Row Locking)
            if payment_method == 'wallet':
                # Lock both wallets to prevent race conditions
                # We assume profiles/wallets exist due to signals, but use get_or_create safety if unsure.
                # Ordering by ID prevents Deadlocks if two users buy from each other simultaneously.
                
                try:
                    buyer_wallet = Wallet.objects.select_for_update().get(user=buyer)
                except Wallet.DoesNotExist:
                    raise serializers.ValidationError("Buyer wallet not found.")
                
                # Check balance
                if buyer_wallet.balance < total_price:
                    raise serializers.ValidationError(f"Insufficient funds. Balance: {buyer_wallet.balance}, Required: {total_price}")

                try:
                    vendor_wallet = Wallet.objects.select_for_update().get(user=listing.vendor)
                except Wallet.DoesNotExist:
                    raise serializers.ValidationError("Vendor wallet not found.")

                # Transfer Funds
                buyer_wallet.balance -= total_price
                vendor_wallet.balance += total_price
                
                buyer_wallet.save()
                vendor_wallet.save()

                # Record Transactions
                Transaction.objects.create(wallet=buyer_wallet, amount=-total_price, type='purchase')
                Transaction.objects.create(wallet=vendor_wallet, amount=total_price, type='sale')

            # 3. Create Order Record
            order = Order.objects.create(
                buyer=buyer,
                listing=listing,
                vendor=listing.vendor,
                listing_title=listing.title,
                quantity_bought=quantity_bought,
                total_price=total_price,
                status='confirmed'
            )
            
            # 4. Update Inventory
            listing.quantity -= quantity_bought
            if listing.quantity <= 0:
                listing.status = 'completed' # Mark as Sold Out
            listing.save()
            
            return order