from django.db import models
from account.models import UserBankAccount
from .constants import TRANSACTION_TYPE
# Create your models here.
class Transaction(models.Model):
    account = models.ForeignKey(UserBankAccount, related_name = "transactions", on_delete=models.CASCADE) # ekjon user er multiple transactions hote pare
    amount = models.DecimalField(decimal_places = 2, max_digits = 12)
    balance_after_transaction = models.DecimalField(decimal_places = 2, max_digits = 12)
    transaction_type = models.IntegerField(choices = TRANSACTION_TYPE, null = True)
    timestamp = models.DateTimeField(auto_now_add = True) # jokhon ekta transaction object toiri hobe sei time ta store kore rakhbo.
    loan_approve = models.BooleanField(default = False)

    class Meta:
        # er kaj hocche, onek gula trasaction hote pare to amra segulake sort korbo timestamp er upor
        ordering = ['timestamp']