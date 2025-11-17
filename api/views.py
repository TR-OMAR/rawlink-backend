from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import (
    User,
    Profile,
    Wallet,
    Transaction,
    Listing,
    Order,
    Message
)
from .serializers import (
    ProfileSerializer,
    WalletSerializer,
    TransactionSerializer,
    ListingSerializer,
    OrderSerializer,
    MessageSerializer,
    UserSerializer
)

# --- 1. IsOwnerOrReadOnly Permission ---
# We create a custom permission to only allow owners of an object to edit it
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        # Check if the object has a 'user' or 'vendor' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'vendor'):
            return obj.vendor == request.user
        return False

# --- 2. Profile ViewSet ---
# This viewset handles viewing and updating *your own* profile.
class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own profile
        return Profile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put'], url_path='me')
    def me(self, request):
        """
        Custom action to get or update the logged-in user's profile.
        """
        profile = request.user.profile
        if request.method == 'GET':
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- 3. Wallet ViewSet ---
# Handles viewing *your own* wallet and transactions
class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own wallet
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """
        Custom action to get the logged-in user's wallet.
        """
        wallet = request.user.wallet
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

# --- 4. Listing ViewSet ---
# Handles browsing, creating, updating, and deleting listings
class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    # Anyone can read, only logged-in users can create/edit
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        # By default, show all *available* listings
        queryset = Listing.objects.filter(status='available')
        
        # --- Filtering Logic ---
        category = self.request.query_params.get('category')
        location = self.request.query_params.get('location')
        
        if category:
            queryset = queryset.filter(category=category)
        if location:
            # Use 'icontains' for a partial (case-insensitive) match
            queryset = queryset.filter(location__icontains=location)
            
        return queryset

    @action(detail=False, methods=['get'], url_path='my-listings')
    def my_listings(self, request):
        """
        Custom action to get the listings created by the logged-in user.
        """
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        listings = Listing.objects.filter(vendor=request.user)
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # When creating a new listing, set the vendor to the logged-in user
        serializer.save(vendor=self.request.user)
    
    def get_serializer_context(self):
        # Pass the request to the serializer context
        return {'request': self.request}

# --- 5. Order ViewSet ---
# Handles creating and viewing orders
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see orders they placed (as buyer) or received (as vendor)
        user = self.request.user
        return Order.objects.filter(Q(buyer=user) | Q(vendor=user)).distinct()

    def perform_create(self, serializer):
        # Pass the request context to the serializer (which needs the user)
        serializer.save(buyer=self.request.user)

    def get_serializer_context(self):
        # Pass the request to the serializer context
        return {'request': self.request}

# --- 6. Message ViewSet ---
# Handles sending and receiving messages
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see messages they sent or received
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user)).distinct()

    def perform_create(self, serializer):
        # Set the sender to the logged-in user
        serializer.save(sender=self.request.user)
    
    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=False, methods=['get'], url_path='chat-history/(?P<user_id>\d+)')
    def chat_history(self, request, user_id=None):
        """
        Custom action to get the chat history with a specific user.
        """
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=request.user))
        ).order_by('timestamp')
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)