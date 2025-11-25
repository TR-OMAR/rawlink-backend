from rest_framework import viewsets, permissions, status
import decimal
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import Q

from .models import (
    User,
    Profile,
    Wallet,
    Transaction,
    Listing,
    Order,
    Message,
)
from .serializers import (
    ProfileSerializer,
    WalletSerializer,
    TransactionSerializer,
    ListingSerializer,
    OrderSerializer,
    MessageSerializer,
    UserSerializer,
)


# -------------------------
# 1. User ViewSet
# -------------------------
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to user list and details."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


# -------------------------
# 2. Custom Permission
# -------------------------
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to allow only owners to edit an object.
    Read-only access is allowed for anyone.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'vendor'):
            return obj.vendor == request.user
        return False


# -------------------------
# 3. Profile ViewSet
# -------------------------
class ProfileViewSet(viewsets.ModelViewSet):
    """Manage user profile. Only accessible by the owner."""
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put'], url_path='me')
    def me(self, request):
        """Retrieve or update the current user's profile."""
        profile = request.user.profile
        if request.method == 'GET':
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# -------------------------
# 4. Wallet ViewSet
# -------------------------
class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """View user's wallet and transactions."""
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Get current user's wallet details."""
        wallet = request.user.wallet
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add-credit')
    @transaction.atomic
    def add_credit(self, request):
        """Add credit to the user's wallet safely inside an atomic transaction."""
        amount = request.data.get('amount')
        if not amount:
            return Response({"detail": "Amount not provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            amount = decimal.Decimal(amount)
        except decimal.InvalidOperation:
            return Response({"detail": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)
        if amount <= 0:
            return Response({"detail": "Amount must be positive."}, status=status.HTTP_400_BAD_REQUEST)

        wallet = request.user.wallet
        with transaction.atomic():
            wallet.balance += amount
            wallet.save()
            Transaction.objects.create(wallet=wallet, amount=amount, type='credit')

        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


# -------------------------
# 5. Listing ViewSet
# -------------------------
class ListingViewSet(viewsets.ModelViewSet):
    """Manage listings. Supports filtering and search."""
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Listing.objects.filter(status='available')
        params = self.request.query_params

        # Apply filters if provided
        if category := params.get('category'):
            queryset = queryset.filter(category=category)
        if country := params.get('country'):
            queryset = queryset.filter(country=country)
        if city := params.get('city'):
            queryset = queryset.filter(city__icontains=city)
        if location := params.get('location'):
            queryset = queryset.filter(location__icontains=location)
        if search := params.get('search'):
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        queryset = queryset.order_by(params.get('ordering') or '-created_at')
        return queryset

    @action(detail=False, methods=['get'], url_path='my-listings')
    def my_listings(self, request):
        """Return listings created by the current user."""
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        listings = Listing.objects.filter(vendor=request.user)
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}


# -------------------------
# 6. Order ViewSet
# -------------------------
class OrderViewSet(viewsets.ModelViewSet):
    """Create and view orders. Buyers and vendors can see their related orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(Q(buyer=user) | Q(vendor=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status. Sellers can mark 'shipped', buyers can mark 'completed'.
        Protects against invalid transitions and unauthorized updates.
        """
        order = self.get_object()
        new_status = request.data.get('status')
        user = request.user
        if not new_status:
            return Response({"detail": "Status not provided."}, status=status.HTTP_400_BAD_REQUEST)

        if user == order.vendor:
            if new_status == 'shipped' and order.status == 'confirmed':
                order.status = 'shipped'
                order.save()
                return Response({'status': 'Order marked as shipped.'})
            return Response({"detail": "Invalid status update for vendor."}, status=status.HTTP_400_BAD_REQUEST)

        if user == order.buyer:
            if new_status == 'completed' and order.status == 'shipped':
                order.status = 'completed'
                order.save()
                if order.listing and order.listing.quantity <= 0:
                    order.listing.status = 'completed'
                    order.listing.save()
                return Response({'status': 'Order marked as completed.'})
            return Response({"detail": "Invalid status update for buyer."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)


# -------------------------
# 7. Message ViewSet
# -------------------------
class MessageViewSet(viewsets.ModelViewSet):
    """Manage messages between users. Supports conversation lists and chat history."""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Return list of users the current user has messaged or received messages from."""
        sent_ids = Message.objects.filter(sender=request.user).values_list('receiver', flat=True)
        received_ids = Message.objects.filter(receiver=request.user).values_list('sender', flat=True)
        contact_ids = set(sent_ids) | set(received_ids)
        contact_ids.discard(request.user.id)
        contacts = User.objects.filter(id__in=contact_ids)
        serializer = UserSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='chat-history/(?P<user_id>\d+)')
    def chat_history(self, request, user_id=None):
        """Return all messages exchanged between the current user and the given user."""
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
