# Generated by Django 2.1.5 on 2019-01-12 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telegramchannel',
            name='chat_id',
            field=models.BigIntegerField(blank=True, help_text='Telegram chat id of channel, can be omitted if username is specified.', null=True),
        ),
        migrations.AlterField(
            model_name='telegramchannel',
            name='subscriptions',
            field=models.ManyToManyField(blank=True, help_text='List of channel subscriptions.', related_name='tg_channels', to='core.Subscription'),
        ),
        migrations.AlterField(
            model_name='telegramchannel',
            name='username',
            field=models.CharField(blank=True, help_text='Channel username, should start with @.', max_length=200, null=True),
        ),
    ]