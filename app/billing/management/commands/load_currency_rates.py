import logging
import time

from django.core.management import BaseCommand

from billing.helpers import get_rates_for_currency, store_or_update_rate, base_url

log = logging.getLogger('load_currency_rates')


class Command(BaseCommand):
    help = f'Loading currency rates from {base_url}'

    def handle(self, *args, **options):
        log.info('Start load currency rates')
        t0 = time.time()
        b_cur, rates = get_rates_for_currency()

        for cur, rate in rates.items():
            store_or_update_rate(b_cur, cur, rate)

            _, cur_rates = get_rates_for_currency(cur)
            for _cur, _rate in cur_rates.items():
                store_or_update_rate(cur, _cur, _rate)

        log.info(f'Currency rates loaded at {time.time() - t0} seconds')
