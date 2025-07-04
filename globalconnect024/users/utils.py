# globalconnect024/users/utils.py

from django.core.mail import EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from .tokens import account_activation_token


def send_activation_email(request, user):
    # Generate UID and token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    # Get current domain from request (or hardcode if needed)
    domain = get_current_site(request).domain
    activation_link = f"http://{domain}/api/users/auth/activate/{uid}/{token}/"
     # ✅ Print to terminal for dev use
    print("🔗 Activation link:", activation_link)

    # Render email content
    html_message = render_to_string('activation_email.html', {
        'user': user,
        'activation_link': activation_link,
    })

    text_message = f"Hi {user.username},\n\nPlease activate your account:\n{activation_link}"

    subject = 'Activate Your 024Global Account'
    from_email = settings.DEFAULT_FROM_EMAIL  # MUST match EMAIL_HOST_USER in .env
    to_email = [user.email]

    # Create and send the email
    email = EmailMultiAlternatives(subject, text_message, from_email, to_email)
    email.attach_alternative(html_message, "text/html")

    try:
        email.send(fail_silently=False)
        print("✅ Activation email sent to:", user.email)
    except Exception as e:
        print("Failed to send activation email:", str(e))
