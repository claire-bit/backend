from django.db.models import Sum 
from orders.models import Referral, Order
from products.models import Product

from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.utils.dateparse import parse_date
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.shortcuts import redirect
from django.conf import settings

from .tokens import account_activation_token
from .utils import send_activation_email
from .serializers import RegistrationSerializer, UserSerializer
from rest_framework.serializers import ModelSerializer

from django.contrib.auth import get_user_model
User = get_user_model()

# -------------------- Auth & Registration --------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save(is_active=False)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"

        subject = 'Activate Your 024GlobalConnect Account'
        try:
            message = render_to_string('activation_email.html', {
                'user': user,
                'activation_link': activation_link
            })
        except TemplateDoesNotExist:
            return Response({"error": "Email template not found."}, status=500)

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except BadHeaderError:
            return Response({"error": "Invalid header found."}, status=500)

        return Response({
            "message": "Account created successfully. Please check your email to activate your account."
        }, status=201)


class ActivateAccount(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return redirect(f'{settings.FRONTEND_URL}/activation-error')

        if user and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            return redirect(f'{settings.FRONTEND_URL}/login?activated=true')

        return redirect(f'{settings.FRONTEND_URL}/activation-error')


class ResendActivationEmail(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"detail": "Email is required."}, status=400)

        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({"detail": "Account is already active."}, status=400)

            send_activation_email(request, user)
            return Response({"detail": "Activation email resent."}, status=200)

        except User.DoesNotExist:
            return Response({"detail": "No account found with this email."}, status=404)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=200)
        except Exception:
            return Response({"error": "Invalid refresh token"}, status=400)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class PasswordResetRequestView(APIView):
    def post(self, request):
        return Response({'message': 'Password reset link sent'})


class PasswordResetConfirmView(APIView):
    def post(self, request):
        return Response({'message': 'Password reset confirmed'})


class UpdateProfileView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

# -------------------- Custom JWT Login --------------------

class EmailOrUsernameTokenObtainSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        login = attrs.get("username")
        password = attrs.get("password")

        user = User.objects.filter(username=login).first() or User.objects.filter(email=login).first()
        if not user or not user.check_password(password):
            raise serializers.ValidationError({"detail": "No active account found with the given credentials"})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Account is inactive"})

        data = super().validate({
            "username": user.username,
            "password": password
        })
        data["user"] = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "country": user.country,
            "city": user.city,
            "promotion_methods": user.promotion_methods,
        }
        return data


class EmailOrUsernameTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainSerializer

# -------------------- Affiliate Views --------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def affiliate_summary(request):
    user = request.user
    if user.role != 'user':
        return Response({"detail": "Only affiliates can access this."}, status=403)

    total_commission = Referral.objects.filter(affiliate=user).aggregate(
        total=Sum("commission_earned")
    )["total"] or 0

    total_referrals = Order.objects.filter(affiliate=user).count()
    total_purchases = Order.objects.filter(affiliate=user, status="paid").count()

    conversion_rate = round((total_purchases / total_referrals) * 100, 2) if total_referrals > 0 else 0

    return Response({
        "total_commission": total_commission,
        "total_referrals": total_referrals,
        "total_purchases": total_purchases,
        "conversion_rate": conversion_rate
    })


class ReferralSerializer(ModelSerializer):
    product_name = serializers.CharField(source="order.product.name", read_only=True)
    buyer_username = serializers.CharField(source="order.buyer.username", read_only=True)
    purchase_amount = serializers.DecimalField(source="order.amount", max_digits=10, decimal_places=2)

    class Meta:
        model = Referral
        fields = ["id", "created_at", "product_name", "buyer_username", "purchase_amount", "commission_earned"]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def affiliate_referrals(request):
    user = request.user
    if user.role != "user":
        return Response({"detail": "Only affiliates can access this."}, status=403)

    referrals = Referral.objects.filter(affiliate=user).select_related("order__product", "order__buyer")
    start = request.GET.get("start")
    end = request.GET.get("end")
    if start:
        referrals = referrals.filter(created_at__date__gte=parse_date(start))
    if end:
        referrals = referrals.filter(created_at__date__lte=parse_date(end))

    serializer = ReferralSerializer(referrals, many=True)
    return Response(serializer.data)

# -------------------- Admin Views --------------------

class IsCustomAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


@api_view(["GET"])
@permission_classes([IsCustomAdmin])
def admin_user_list(request):
    role = request.GET.get("role")
    if role in ['vendor', 'user']:
        users = User.objects.filter(role=role)
    else:
        users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsCustomAdmin])
def toggle_user_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=404)

    is_active = request.data.get("is_active")
    if is_active is None:
        return Response({"detail": "Missing 'is_active' field."}, status=400)

    user.is_active = bool(is_active)
    user.save()
    return Response({"detail": "User status updated."})


@api_view(["GET"])
@permission_classes([IsCustomAdmin])
def admin_product_list(request):
    products = Product.objects.select_related("vendor").all()
    data = [
        {
            "id": p.id,
            "name": p.name,
            "vendor": p.vendor.username,
            "price": str(p.price),
            "stock": p.stock,
            "is_active": p.is_active,
            "created_at": p.created_at,
        }
        for p in products
    ]
    return Response(data)


@api_view(["PATCH"])
@permission_classes([IsCustomAdmin])
def toggle_product_visibility(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.is_active = not product.is_active
        product.save()
        return Response({
            "message": "Product visibility updated.",
            "product_id": product.id,
            "is_active": product.is_active
        }, status=200)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)


@api_view(['GET'])
@permission_classes([IsCustomAdmin])
def admin_commission_logs(request):
    referrals = Referral.objects.select_related("affiliate", "order__product", "order__buyer")
    affiliate = request.GET.get("affiliate")
    if affiliate:
        referrals = referrals.filter(affiliate__username=affiliate) | referrals.filter(affiliate__id=affiliate)

    start = request.GET.get("start")
    end = request.GET.get("end")
    if start:
        referrals = referrals.filter(created_at__date__gte=parse_date(start))
    if end:
        referrals = referrals.filter(created_at__date__lte=parse_date(end))

    serializer = AdminReferralSerializer(referrals, many=True)
    return Response(serializer.data)


class AdminReferralSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="order.product.name", read_only=True)
    buyer_username = serializers.CharField(source="order.buyer.username", read_only=True)
    purchase_amount = serializers.DecimalField(source="order.amount", max_digits=10, decimal_places=2)

    is_approved = serializers.BooleanField()
    is_paid = serializers.BooleanField()
    affiliate = serializers.StringRelatedField()

    class Meta:
        model = Referral
        fields = [
            "id",
            "created_at",
            "affiliate",
            "product_name",
            "buyer_username",
            "purchase_amount",
            "commission_earned",
            "is_approved",
            "is_paid",
        ]


@api_view(["PATCH"])
@permission_classes([IsCustomAdmin])
def approve_commission(request, referral_id):
    try:
        ref = Referral.objects.get(id=referral_id)
        ref.is_approved = request.data.get("is_approved", True)
        ref.save()
        return Response({"detail": "Commission approval updated."})
    except Referral.DoesNotExist:
        return Response({"detail": "Referral not found."}, status=404)


@api_view(["PATCH"])
@permission_classes([IsCustomAdmin])
def mark_commission_paid(request, referral_id):
    try:
        ref = Referral.objects.get(id=referral_id)
        ref.is_paid = request.data.get("is_paid", True)
        ref.save()
        return Response({"detail": "Commission payout updated."})
    except Referral.DoesNotExist:
        return Response({"detail": "Referral not found."}, status=404)


@api_view(["GET"])
@permission_classes([IsCustomAdmin])
def system_logs(request):
    logs = [
        {"id": 1, "timestamp": "2025-07-01T14:20:00Z", "event": "User Login", "user": "Claire_m"},
        {"id": 2, "timestamp": "2025-07-01T15:05:00Z", "event": "Referral Link Clicked", "user": "Claire3"},
        {"id": 3, "timestamp": "2025-07-01T15:10:00Z", "event": "Commission Approved", "user": "admin"},
    ]
    return Response(logs)
