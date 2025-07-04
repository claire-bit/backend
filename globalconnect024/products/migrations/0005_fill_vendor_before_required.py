from django.db import migrations

def assign_default_vendor(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    User = apps.get_model('users', 'CustomUser')  # Your custom user model

    default_vendor = User.objects.filter(role='vendor').first()
    if default_vendor:
        Product.objects.filter(vendor__isnull=True).update(vendor=default_vendor)

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_product_approved'),
    ]

    operations = [
        migrations.RunPython(assign_default_vendor),
    ]
