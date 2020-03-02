from django.contrib.auth.models import User
from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=3, db_index=True)
    min_count = models.IntegerField(default=1)


class CurrencyRate(models.Model):
    currency_from = models.ForeignKey('Currency', related_name='rates_to', on_delete=models.CASCADE)
    currency_to = models.ForeignKey('Currency', related_name='rates_from', on_delete=models.CASCADE)
    rate = models.DecimalField(decimal_places=2, max_digits=14)


class Wallet(models.Model):
    currency = models.ForeignKey('Currency', related_name='currency_wallets', on_delete=models.SET_NULL, null=True)
    owner = models.ForeignKey(to=User, related_name='wallets', on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=14, default=0.)


class Transaction(models.Model):
    wallet_from = models.ForeignKey('Wallet', related_name='buy_transactions', on_delete=models.CASCADE)
    wallet_to = models.ForeignKey('Wallet', related_name='sell_transactions', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=14)
