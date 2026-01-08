from django.contrib import admin
from .models import Transaction

from .views import send_transaction_email
# Register your models here.
# ModelAdmin ke use korte gele amaderke @ (decorator use korte hoy)
@admin.register(Transaction)

# admin panel ke customize korbo. Admin panel ke customize korle je model ti use korte hoy take amra boli ModelAdmin
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount', 'balance_after_transaction', 'transaction_type', 'loan_approve']
    
    # ami jodi admin panel theke kono kichu change kori tahole setar effect kothay porbe seta bole dicchi.
    def save_model(self, request, obj, form, change):
        obj.account.balance += obj.amount
        obj.balance_after_transaction = obj.account.balance
        obj.account.save()
        send_transaction_email(obj.account.user, obj.amount, "Loan Approval", 'transaction/approval_mail.html')
        super().save_model(request, obj, form, change)