from django.contrib import admin
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from billing.views import RegisterClientView, ListClientsView, DetailClientView, CreateTransactionView, \
    TransactionsView, CurrencyRateCreateView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('clients', ListClientsView.as_view()),
    path('client/auth', obtain_auth_token, name='auth'),
    path('client/register', RegisterClientView.as_view()),
    path('client/<int:pk>', DetailClientView.as_view()),

    path('transaction', CreateTransactionView.as_view(), name='transaction'),
    path('transactions', TransactionsView.as_view(), name='transactions'),

    path('currency_rate', CurrencyRateCreateView.as_view())
]
