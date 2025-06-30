# accounts/views.py 
from django.db.models import Sum
from .models import Referral, Order

from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.conf import settings
from rest_framework.generics import RetrieveUpdateAPIView

from .serializers import RegistrationSerializer, UserSerializer
from rest_framework.serializers import ModelSerializer
from .tokens import account_activation_token  # your custom token
from .utils import send_activation_email

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
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
            return Response({"error": "Email template not found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except BadHeaderError:
            return Response({"error": "Invalid header found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Account created successfully. Please check your email to activate your account."
        }, status=status.HTTP_201_CREATED)


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
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({"detail": "Account is already active."}, status=status.HTTP_400_BAD_REQUEST)

            send_activation_email(request, user)
            return Response({"detail": "Activation email resent."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"detail": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):
    def post(self, request):
        # Optional: blacklist token here if you're using refresh token rotation
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    def post(self, request):
        # Your password reset logic
        return Response({'message': 'Password reset link sent'})    


class PasswordResetConfirmView(APIView):
    def post(self, request):
        # Implement password reset confirmation logic
        return Response({'message': 'Password reset confirmed'})    


class UpdateProfileView(RetrieveUpdateAPIView):
    """
    Allows authenticated users to retrieve and update their profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ✅ Custom JWT login supporting email or username
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

class EmailOrUsernameTokenObtainSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        login = attrs.get("username")  # This will be username or email from the frontend
        password = attrs.get("password")

        user = User.objects.filter(username=login).first()

        if not user:
            user = User.objects.filter(email=login).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError({"detail": "No active account found with the given credentials"})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Account is inactive"})

        # Use the found user's username to proceed with SimpleJWT flow
        data = super().validate({
            "username": user.username,
            "password": password
        })

        return data


class EmailOrUsernameTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainSerializer

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
    serializer = ReferralSerializer(referrals, many=True)
    return Response(serializer.data)  

