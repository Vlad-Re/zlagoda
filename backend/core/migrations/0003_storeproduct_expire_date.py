from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_employee_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="storeproduct",
            name="expire_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
