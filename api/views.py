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

# --- 1. User ViewSet ---
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


# --- 2. Permissions ---
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'vendor'):
            return obj.vendor == request.user
        return False


# --- 3. Profile ViewSet ---
class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put'], url_path='me')
    def me(self, request):
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


# --- 4. Wallet ViewSet ---
class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        wallet = request.user.wallet
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add-credit')
    @transaction.atomic
    def add_credit(self, request):
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
            
            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type='credit'
            )
            
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


# --- 5. Listing ViewSet ---
class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Listing.objects.filter(status='available')
        category = self.request.query_params.get('category')
        location = self.request.query_params.get('location')
        search = self.request.query_params.get('search')
        ordering = self.request.query_params.get('ordering')
        
        if category:
            queryset = queryset.filter(category=category)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if search:
             queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    @action(detail=False, methods=['get'], url_path='my-listings')
    def my_listings(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        listings = Listing.objects.filter(vendor=request.user)
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)
    
    def get_serializer_context(self):
        return {'request': self.request}


# --- 6. Order ViewSet ---
class OrderViewSet(viewsets.ModelViewSet):
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
            else:
                return Response({"detail": "Invalid status update for vendor."}, status=status.HTTP_400_BAD_REQUEST)

        elif user == order.buyer:
            if new_status == 'completed' and order.status == 'shipped':
                order.status = 'completed'
                order.save()
                if order.listing and order.listing.quantity <= 0: 
                     order.listing.status = 'completed'
                     order.listing.save()
                return Response({'status': 'Order marked as received/completed.'})
            else:
                return Response({"detail": "Invalid status update for buyer."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)


# --- 7. Message ViewSet ---
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    
    def get_serializer_context(self):
        return {'request': self.request}

    # --- THIS IS THE CRITICAL ENDPOINT FOR CHAT SIDEBAR ---
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """
        Returns a list of users that the current user has exchanged messages with.
        """
        # IDs of people I sent messages to
        sent_ids = list(Message.objects.filter(sender=request.user).values_list('receiver', flat=True))
        # IDs of people who sent messages to me
        received_ids = list(Message.objects.filter(receiver=request.user).values_list('sender', flat=True))
        
        # Combine lists and remove duplicates using set
        contact_ids = set(sent_ids + received_ids)
        
        # Remove self if present
        if request.user.id in contact_ids:
            contact_ids.remove(request.user.id)
        
        # Fetch User objects
        contacts = User.objects.filter(id__in=contact_ids)
        serializer = UserSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='chat-history/(?P<user_id>\d+)')
    def chat_history(self, request, user_id=None):
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