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
# This serializer adds our custom 'role' field to the Djoser registration
class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password', 'role')
        extra_kwargs = {'password': {'write_only': True}}

# This serializer is for viewing user details (without password)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'role')

# --- Profile Serializer ---
class ProfileSerializer(serializers.ModelSerializer):
    # We display the user's email, not just their ID
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Profile
        fields = ('user', 'name', 'phone', 'location')

# --- Wallet & Transaction Serializers ---
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'amount', 'type', 'timestamp')

class WalletSerializer(serializers.ModelSerializer):
    # We can nest the transactions directly inside the wallet
    transactions = TransactionSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Wallet
        fields = ('user', 'balance', 'transactions')

# --- Listing Serializer ---
class ListingSerializer(serializers.ModelSerializer):
    # Show the vendor's username, not their ID
    vendor = serializers.StringRelatedField(read_only=True)
    # Allow the client to specify the vendor ID when creating (write_only)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='vendor', write_only=True
    )

    class Meta:
        model = Listing
        fields = (
            'id', 'title', 'description', 'category', 'quantity', 'unit',
            'price_per_unit', 'location', 'image', 'status', 'created_at',
            'vendor', 'vendor_id'
        )
        read_only_fields = ('id', 'created_at', 'vendor')

    def create(self, validated_data):
        # Override create to set the vendor from the context (the logged-in user)
        # We will set this up in the View
        validated_data['vendor'] = self.context['request'].user
        return super().create(validated_data)

# --- Order Serializers ---
class OrderSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    vendor = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    
    # These fields are for *creating* an order
    listing_id = serializers.IntegerField(write_only=True)
    quantity_bought = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'buyer', 'vendor', 'listing', 'listing_title',
            'total_price', 'status', 'created_at',
            'listing_id', 'quantity_bought' # Write-only fields
        )
        read_only_fields = ('id', 'total_price', 'status', 'created_at', 'listing_title', 'buyer', 'vendor', 'listing')

    def create(self, validated_data):
        listing_id = validated_data.pop('listing_id')
        quantity_bought = validated_data.pop('quantity_bought')
        buyer = self.context['request'].user

        try:
            listing = Listing.objects.get(id=listing_id, status='available')
        except Listing.DoesNotExist:
            raise serializers.ValidationError("This listing is not available.")

        if quantity_bought > listing.quantity:
            raise serializers.ValidationError("Not enough quantity available.")

        # --- This is your core business logic ---
        total_price = listing.price_per_unit * quantity_bought
        
        # 1. Create the order
        order = Order.objects.create(
            buyer=buyer,
            listing=listing,
            vendor=listing.vendor,
            listing_title=listing.title,
            quantity_bought=quantity_bought,
            total_price=total_price,
            status='pending' # Or 'confirmed' if you want it to be auto-confirmed
        )
        
        # 2. Update listing quantity (or mark as completed)
        # For simplicity, we'll mark it as in-transit if fully bought
        if quantity_bought == listing.quantity:
            listing.status = 'in-transit'
        else:
            # Or you could allow partial buys by reducing quantity
            listing.quantity -= quantity_bought
        listing.save()

        # 3. TODO: Handle wallet transactions (we'll add this later)
        # (e.g., move money from buyer's wallet to escrow)
        
        return order

# --- Message Serializers ---
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='receiver', write_only=True
    )

    class Meta:
        model = Message
        fields = ('id', 'sender', 'receiver', 'content', 'timestamp', 'receiver_id')
        read_only_fields = ('id', 'sender', 'timestamp')

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)