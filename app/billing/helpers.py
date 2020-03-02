import logging
import time

import requests
from django.db import transaction as t, DatabaseError
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from billing.exceptions import CurrencyRateNotPresent
from billing.models import Currency, CurrencyRate

log = logging.getLogger(__name__)

base_url = 'https://api.ratesapi.io/api/latest'


def force_load_currency_rate(currency_from: Currency, currency_to: Currency) -> CurrencyRate:
    _, cur_rates = get_rates_for_currency(currency_from.code)
    result_currency_rate = None
    for cur, rate in cur_rates.items():
        currency_rate = store_or_update_rate(currency_from.code, cur, rate)
        if cur == currency_to.code:
            result_currency_rate = currency_rate

    if not result_currency_rate:
        raise CurrencyRateNotPresent(detail=f'Rate for {currency_from.code} -> {currency_to.code} is not present')
    return result_currency_rate


def get_rates_for_currency(code=None):
    if not code:
        url = base_url
    else:
        url = f'{base_url}?base={code}'

    result = retrieve_external_rates(url)
    base_cur = result.get('base')
    rates = result.get('rates')
    return base_cur, rates


def store_or_update_rate(currency_from, currency_to, rate):
    try:
        with t.atomic():
            cur_from_obj, _ = Currency.objects.get_or_create(code=currency_from)
            cur_to_obj, _ = Currency.objects.get_or_create(code=currency_to)

            rate_obj, _ = CurrencyRate.objects.get_or_create(currency_from=cur_from_obj, currency_to=cur_to_obj)
            rate_obj.rate = rate
            rate_obj.save()

            log.info(f'Storing currency rate {cur_from_obj.code} -> {cur_to_obj.code} [{rate}]')

            return cur_to_obj
    except DatabaseError as e:
        log.exception(e)
        t.rollback()


def requests_retry_session(retries=5, backoff_factor=0.3, status_forcelist=(500, 502, 504), ):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def retrieve_external_rates(url):
    t0 = time.time()
    try:
        response = requests_retry_session().get(url)
        return response.json()
    except Exception as x:
        log.error('It failed :(', x.__class__.__name__)
    finally:
        t1 = time.time()
        log.info(f'{url} retrieve took {t1 - t0} seconds')

