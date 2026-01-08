from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']
    # Amra jokhon transaction niye kaj korte jabo thokhon user er account ta ekhane pass kore dibo. Ar ei TransactionForm ke inherite korbo (DepositForm, WithdrawForm, LoanRequestForm ei class gula TransactionForm ke inheite korbe)
    # Account ta je pop hocche ba ei jinish ta actually kothay use hocche seta amra dekhte parbo (views.py te get_form_kwargs er moddhe)
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account') # account value ke pop kore anlam. | keyword argument er moddhe built in kichu jinish ke pass kore dibo
        super().__init__(*args, **kwargs) # Parent class er __init__ ke overwrite korbo
        self.fields['transaction_type'].disabled = True # ei field disable thakbe
        self.fields['transaction_type'].widget = forms.HiddenInput() # user er theke hide kora thakbe

    def save(self, commit = True):
        self.instance.account = self.account # je user ta request korteche tar kono object jodi amader database e thake tahole sei instance er account je jabo, giye self.account ke rekhe dibo
        # jekono trasaction er por balance take update kore dibo.
        self.instance.balance_after_transaction = self.account.balance # suppouse 0(main balance)--> 5000(deposit) = 5000(total_balance/balance_after_transaction)
        return super().save() # parent class (ModelForm) er save function ke call kore dilam
    

class DepositForm(TransactionForm):
    def clean_amount(self): # amount field ke filter korbo | clean_amount --> builtin ekta function (clean_... jei field ta niye kaj korte chai sei field ta use korbo, jehetu amount niye kaj kortechi tai amount niyechi)
        min_deposit_amount = 100
        amount = self.cleaned_data.get('amount') # user er fillup kora form theke amount field er value ke niye ashlam
        if amount < min_deposit_amount:
            raise forms.ValidationError( # raise hocche error ke show koranor jonno ekta keyword
                f'You need to deposit at least ${min_deposit_amount}'
            )
        return amount
    
class WithdrawForm(TransactionForm):
    def clean_amount(self):
        account = self.account # je user request korteche tar account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least ${min_withdraw_amount}'
            )
        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most ${max_withdraw_amount}'
            )
        if amount > balance:
            raise forms.ValidationError(
                f'You have ${balance} in your account.'
                'You can not withdraw more than your account balance'
            )
        return amount
    

class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return amount

# Loan koybar neya hoyche seta views er moddhe korechi. Koybar loan neya hoyeche eta model er sathe connected ba model theke pabo. Tai ei kaj ta form er moddhe na kore views er moddhe korechi karon form er kaj form e ar model er kaj views e koratai better.
# form er kaj form e rakhte hoy
# model er kaj views e rakhte hoy.