# Generated by Django 5.1.5 on 2025-04-02 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='Anonymous', max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('desc', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Contact',
                'verbose_name_plural': 'Contacts',
                'ordering': ['name'],
            },
        ),
    ]
