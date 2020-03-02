import logging

from django.contrib.auth.models import User
from django.db import transaction as t, DatabaseError

from billing.exceptions import NotEnoughMoneyException, CurrencyRateNotPresent
from billing.helpers import force_load_currency_rate
from billing.models import Wallet, Transaction, Currency, CurrencyRate
from exn_tst_billing import settings

log = logging.getLogger(__name__)


def _check_moving(wallet_from: Wallet, amount: float):
    if wallet_from.amount < amount:
        raise NotEnoughMoneyException(
            detail=f'Not enough money, deficit is {amount - wallet_from.amount} {wallet_from.currency.code}'
        )


def _make_move(wallet_from: Wallet, wallet_to: Wallet, amount: float, description=None) -> Transaction:
    try:
        with t.atomic():
            _check_moving(wallet_from, amount)

            to_amount = amount
            if wallet_from.currency != wallet_to.currency:
                currency_rate = CurrencyRate.objects \
                    .filter(currency_from=wallet_from.currency, currency_to=wallet_to.currency) \
                    .first()
                if not currency_rate:
                    currency_rate = force_load_currency_rate(wallet_from.currency, wallet_to.currency)
                to_amount = amount * currency_rate.rate

            transaction = Transaction(wallet_from=wallet_from, wallet_to=wallet_to, amount=amount,
                                      description=description)

            wallet_from.amount -= amount
            wallet_to.amount += to_amount

            wallet_from.save()
            wallet_to.save()
            transaction.save()

            return transaction
    except DatabaseError as e:
        log.exception(e)
        t.rollback()


def make_initial_wallets(user):
    try:
        wallets = []
        with t.atomic():
            for cur_code in ('USD', 'EUR', 'CNY'):
                currency = Currency.objects.get(code=cur_code)
                wallet = Wallet(currency=currency, owner=user)
                wallet.save()

                if cur_code == 'USD':
                    try:
                        move_money(get_main_wallet(), wallet, 100, 'welcome', use_commission=False)
                    except NotEnoughMoneyException:
                        log.error('Not enough money at main wallet')

                wallets.append(wallet)
        return wallets
    except DatabaseError as e:
        log.exception(e)
        t.rollback()


def get_main_user() -> User:
    return User.objects.get(username=settings.MAIN_USER_OWNER_USERNAME)


def get_main_wallet() -> Wallet:
    return Wallet.objects.get(owner=get_main_user())


def move_money(wallet_from: Wallet, wallet_to: Wallet, amount: float, description=None,
               use_commission=True) -> Transaction:
    if use_commission and wallet_to.owner != wallet_from.owner:
        commission_amount = (amount * settings.COMMISSION_PERCENT) / 100
        _make_move(wallet_from, get_main_wallet(), commission_amount, 'commission')

    transaction = _make_move(wallet_from, wallet_to, amount, description or '')
    return transaction
