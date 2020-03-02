from datetime import datetime, timedelta

from django.contrib.auth.models import User
from rest_framework import serializers

from billing.logic import make_initial_wallets
from billing.models import CurrencyRate, Currency
from .models import Wallet, Transaction


class WalletSerializer(serializers.ModelSerializer):
    def __init__(self, **kwargs):
        self.with_owner = kwargs.pop('with_owner', True)
        super().__init__(**kwargs)

    currency = serializers.ReadOnlyField(source='currency.code')
    amount = serializers.DecimalField(decimal_places=2, max_digits=14)

    class Meta:
        model = Wallet
        fields = ['id', 'currency', 'amount', 'owner']

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        if self.with_owner:
            repr['owner'] = instance.owner.id
        return repr


class ClientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    wallets = WalletSerializer(many=True, read_only=True, with_owner=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'wallets']

    def create(self, data):
        user = super(ClientSerializer, self).create(data)
        user.set_password(data['password'])
        user.save()

        make_initial_wallets(user)

        return user


class TransactionMakeSerializer(serializers.Serializer):
    wallet_from = serializers.PrimaryKeyRelatedField(queryset=Wallet.objects.all(), write_only=True, required=True)
    wallet_to = serializers.PrimaryKeyRelatedField(queryset=Wallet.objects.all(), write_only=True, required=True)
    amount = serializers.FloatField(write_only=True, required=True)
    description = serializers.CharField(write_only=True)


class TransactionResultSerializer(serializers.ModelSerializer):
    wallet_from = WalletSerializer(read_only=True)
    wallet_to = WalletSerializer(read_only=True)
    amount = serializers.DecimalField(decimal_places=2, max_digits=14)

    class Meta:
        model = Transaction
        fields = ['id', 'wallet_from', 'wallet_to', 'amount', 'description']


class TransactionListInputSerializer(serializers.Serializer):
    input = serializers.BooleanField(write_only=True, default=True)
    output = serializers.BooleanField(write_only=True, default=True)
    wallets = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Wallet.objects.all()), default=[])
    start = serializers.DateTimeField(default=(datetime.utcnow() - timedelta(days=30)))
    end = serializers.DateTimeField(default=datetime.utcnow())

    order = serializers.ChoiceField(['asc', 'desc'], default='asc')
    order_by = serializers.ChoiceField(['created', 'amount', 'description'], default='created')


class TransactionListSerializer(serializers.ModelSerializer):
    wallet_from = serializers.CharField(source='wallet_from.id', read_only=True)
    wallet_to = serializers.CharField(source='wallet_to.id', read_only=True)
    amount = serializers.DecimalField(decimal_places=2, max_digits=14)

    class Meta:
        model = Transaction
        fields = ['id', 'wallet_from', 'wallet_to', 'amount', 'description']


class CurrencyRateSerializer(serializers.ModelSerializer):
    currency_from = serializers.CharField(source='currency_from.code', read_only=True)
    currency_to = serializers.CharField(source='currency_to.code', read_only=True)

    class Meta:
        model = CurrencyRate
        fields = ['currency_from', 'currency_to', 'rate']


class CurrencyRateInputSerializer(serializers.ModelSerializer):
    currency_from = serializers.CharField(source='currency_from.code')
    currency_to = serializers.CharField(source='currency_to.code')

    class Meta:
        model = CurrencyRate
        fields = ['currency_from', 'currency_to', 'rate']

    def create(self, validated_data):
        cur_from, _ = Currency.objects.get_or_create(code=validated_data['currency_from']['code'])
        cur_to, _ = Currency.objects.get_or_create(code=validated_data['currency_to']['code'])
        rate = CurrencyRate(currency_from=cur_from, currency_to=cur_to, rate=validated_data['rate'])
        rate.save()
        return rate
