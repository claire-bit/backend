from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from users.utils import send_activation_email  # ✅ import this

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True, required=True)

    country = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    promotion_methods = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    role = serializers.ChoiceField(choices=[('user', 'Affiliate'), ('vendor', 'Vendor')], default='user')

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'password', 'confirm_password',
            'country', 'city', 'promotion_methods', 'role'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')  # Exclude confirm_password
        request = self.context.get('request')

        user = User.objects.create_user(
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=validated_data.get('password'),
            country=validated_data.get('country', ''),
            city=validated_data.get('city', ''),
            promotion_methods=validated_data.get('promotion_methods', []),
            role=validated_data.get('role', 'user'),
            is_active=False  # 🔒 Require email activation
        )

        send_activation_email(request, user)  # ✅ Send activation email
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_active', 'date_joined', 'role', 'country', 'city', 'promotion_methods'
        ]
