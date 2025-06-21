# globalconnect024/users/utils.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from .tokens import account_activation_token

def send_activation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    domain = get_current_site(request).domain

    activation_link = f"http://localhost:8000/api/users/auth/activate/{uid}/{token}/"

    # Render HTML email
    html_message = render_to_string('activation_email.html', {
        'user': user,
        'activation_link': activation_link,
    })

    # Optional: plain text fallback
    text_message = f"Hi {user.username},\n\nPlease activate your account:\n{activation_link}"

    subject = 'Activate Your 024Global Account'
    from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else 'noreply@024global.com'
    to_email = [user.email]

    email = EmailMultiAlternatives(subject, text_message, from_email, to_email)
    email.attach_alternative(html_message, "text/html")
    email.send(fail_silently=False)
