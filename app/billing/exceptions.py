from rest_framework.exceptions import APIException
from rest_framework import status


class NotEnoughMoneyException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Not enough money'
    default_code = 'not_enough_money'


class CurrencyRateNotPresent(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Currency rate not present'
    default_code = 'currency_not_present'
