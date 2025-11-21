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
    vendor = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Listing
        fields = (
            'id', 'title', 'description', 'category', 'quantity', 'unit',
            'price_per_unit', 'location', 'image', 'status', 'created_at',
            'vendor',
            'vendor_id'
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

# --- Order Serializer (UPDATED) ---
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

    @transaction.atomic
    def create(self, validated_data):
        listing_id = validated_data.pop('listing_id')
        quantity_bought = validated_data.pop('quantity_bought')
        payment_method = validated_data.pop('payment_method', 'wallet')
        buyer = self.context['request'].user
        
        try:
            listing = Listing.objects.select_for_update().get(id=listing_id, status='available')
            buyer_wallet = Wallet.objects.select_for_update().get(user=buyer)
            vendor_wallet = Wallet.objects.select_for_update().get(user=listing.vendor)
        except Listing.DoesNotExist:
            raise serializers.ValidationError("This listing is not available.")
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not found.")

        if buyer.id == listing.vendor.id:
            raise serializers.ValidationError("You cannot buy your own listing.")

        if quantity_bought > listing.quantity:
            raise serializers.ValidationError(f"Only {listing.quantity} {listing.unit} available.")

        total_price = listing.price_per_unit * quantity_bought

        # Wallet Logic: Only check/deduct if payment method is 'wallet'
        if payment_method == 'wallet':
            if buyer_wallet.balance < total_price:
                raise serializers.ValidationError(f"Insufficient funds. Balance: {buyer_wallet.balance}, Required: {total_price}")
            
            buyer_wallet.balance -= total_price
            vendor_wallet.balance += total_price
            buyer_wallet.save()
            vendor_wallet.save()

            Transaction.objects.create(wallet=buyer_wallet, amount=-total_price, type='purchase')
            Transaction.objects.create(wallet=vendor_wallet, amount=total_price, type='sale')

        # Create Order
        order = Order.objects.create(
            buyer=buyer,
            listing=listing,
            vendor=listing.vendor,
            listing_title=listing.title,
            quantity_bought=quantity_bought,
            total_price=total_price,
            status='confirmed'
        )
        
        # Update Listing Quantity
        listing.quantity -= quantity_bought
        if listing.quantity <= 0:
             listing.status = 'completed' # Sold out
        listing.save()
        
        return order