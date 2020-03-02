from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from billing.logic import move_money
from billing.models import Transaction, Wallet, CurrencyRate
from billing.serializers import ClientSerializer, TransactionMakeSerializer, \
    TransactionResultSerializer, TransactionListSerializer, TransactionListInputSerializer, CurrencyRateInputSerializer


class RegisterClientView(generics.CreateAPIView):
    serializer_class = ClientSerializer


class ListClientsView(generics.ListAPIView):
    serializer_class = ClientSerializer
    queryset = User.objects.filter(is_staff=False)
    permission_classes = [permissions.IsAdminUser]


class DetailClientView(generics.RetrieveAPIView):
    serializer_class = ClientSerializer
    queryset = User.objects.filter(is_staff=False)
    permission_classes = [permissions.DjangoObjectPermissions]


class CreateTransactionView(generics.CreateAPIView):
    serializer_class = TransactionMakeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        input = self.get_serializer(data=request.data)
        input.is_valid(raise_exception=True)

        wallet_from = input.validated_data['wallet_from']

        if wallet_from.owner != request.user:
            return Response({'error': 'Try to move money from not yours wallet'}, status=status.HTTP_403_FORBIDDEN)

        result = move_money(wallet_from,
                            input.validated_data['wallet_to'],
                            input.validated_data['amount'],
                            description=input.validated_data['description'],
                            use_commission=True)

        return Response(TransactionResultSerializer(result).data, status=status.HTTP_202_ACCEPTED)


class TransactionsView(generics.ListAPIView):
    serializer_class = TransactionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Transaction.objects.all()

    def list(self, request, *args, **kwargs):
        input = TransactionListInputSerializer(data=request.query_params)
        input.is_valid(raise_exception=True)

        queryset = self.get_queryset()

        client_wallets = Wallet.objects.filter(owner=request.user)
        interested_wallets = []
        for wallet in input.validated_data['wallets']:
            if wallet in client_wallets:
                interested_wallets.append(wallet)

        interested_wallets = interested_wallets or client_wallets

        queryset.filter(wallet_from__in=interested_wallets)
        queryset.filter(wallet_to__in=interested_wallets)

        queryset.filter(created__gt=input.validated_data['end'], created__lt=input.validated_data['start'])
        queryset.order_by(input.validated_data['order_by'])
        if input.validated_data['order'] == 'desc':
            queryset.reverse()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CurrencyRateCreateView(generics.ListCreateAPIView):
    serializer_class = CurrencyRateInputSerializer
    queryset = CurrencyRate.objects.all()
    permission_classes = [permissions.IsAdminUser]
