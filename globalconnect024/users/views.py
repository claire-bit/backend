# accounts/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .serializers import RegistrationSerializer
from .tokens import account_activation_token  # Custom token generator

User = get_user_model()


# ✅ Registration View with error logging
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("❌ Validation errors:", serializer.errors)  # 👈 This will print in your terminal
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save(is_active=False)  # inactive until email verified

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
        # Send activation email
        subject = 'Activate Your Account'
        message = render_to_string('emails/activation_email.html', {
            'user': user,
            'activation_link': activation_link
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        return Response({
            "message": "Account created successfully. Please check your email to activate your account."
        }, status=status.HTTP_201_CREATED)


# ✅ Activation View
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
