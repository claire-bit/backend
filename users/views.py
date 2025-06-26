# accounts/views.py 

from rest_framework import generics, status, permissions
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
from .tokens import account_activation_token  # your custom token
from .utils import send_activation_email
from .models import BlogPost
from .serializers import BlogPostSerializer

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

class ContactFormView(APIView):
    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        phone = request.data.get("phone")
        subject = request.data.get("subject")
        message = request.data.get("message")

        if not name or not email or not message:
            return Response(
                {"error": "Name, email and message are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Combine message content
        full_message = f"""
You have a new contact form submission:

Name: {name}
Email: {email}
Phone: {phone or 'N/A'}
Subject: {subject}
Message:
{message}
        """

        try:
            send_mail(
                subject=f"New Contact Message: {subject}",
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["024globalconnect@gmail.com"],
                fail_silently=False,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to send email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({"message": "Your message has been sent successfully!"}, status=status.HTTP_200_OK)


class BlogPostCreateView(generics.CreateAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer

class UserBlogPostListView(generics.ListAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user)