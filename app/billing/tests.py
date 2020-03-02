from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from billing.logic import make_initial_wallets, get_main_wallet, move_money, get_main_user
from exn_tst_billing import settings


class BillingTest(TestCase):
    def test_smoke(self):
        user1 = User(username='test1', )
        user1.set_password('test')
        user1.save()

        user2 = User(username='test2', )
        user2.set_password('test')
        user2.save()

        main_wallet = get_main_wallet()
        assert main_wallet.amount == settings.INITIAL_MAIN_WALLET_AMOUNT

        u1_wallets = make_initial_wallets(user1)
        u2_wallets = make_initial_wallets(user2)

        user1.get_session_auth_hash()
        main_wallet = get_main_wallet()
        assert main_wallet.amount == settings.INITIAL_MAIN_WALLET_AMOUNT - 200

        token_response = self.client.post(reverse('auth'), data={'username': user1.username, 'password': 'test'})
        assert token_response.status_code == 200

        move_money(u1_wallets[0], u2_wallets[0], 10.0, description='test', use_commission=True)

        assert main_wallet.amount == (settings.INITIAL_MAIN_WALLET_AMOUNT - 200) + 0.1
