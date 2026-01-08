from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transaction

from . forms import DepositForm, WithdrawForm, LoanRequestForm
from .constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID
from django.contrib import messages
from datetime import datetime
from django.db.models import Sum
from django.views import View
from django.urls import reverse_lazy

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
# Create your views here.

#-------------------------------------------------------------------------
def send_transaction_email(user, amount, subject, template):
    message = render_to_string(template, {
        'user' : user,
        'amount' : amount,
    })
    send_email = EmailMultiAlternatives(subject, '', to=[user.email])
    send_email.attach_alternative(message, "text/html")
    send_email.send()
#-------------------------------------------------------------------------
# ei view ke inherit kore amra deposit, withdraw, loan request er kaj korbo
class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transaction/transaction_form.html'
    model = Transaction
    title = '' # ei title view ta class based view te thake na. (HTML title ja frontend e show korbe) Eita kono ekta koushol use kore pass kore dibo.
    success_url = reverse_lazy('transaction_report')

    """
    "TransactionForm & TransactionCreateMixin er combination e nicher documentation/lekha ta"
        jokhoni Transactionform er ekta object toiri hobe, ba ekta form e kono ekta user kono ekta jinish pass korbe
        tokhon jeta hobe --> tokhoni amader views er get_form_kwargs er account value ta amader TransactionForm er moddhe chole ashbe
        ashar pore ekhane pop hobe (check views.py). Pop hobar por pori user dekhbe je transaction_type ei field ta disable kora
        sei jinish ta fillup korte parbena, amra fillup kore dibo backend theke. Then jokhon eta save korte jabe orthat submit button click korbe
        tokhon tar account ta capture korar pore tar tar balance take ber kore niye ashlam ebong balance_after_transaction ta amra tar balance ta diye update kore dicchi prottekta bar.
        then reture kore dichhi return super().save ke --> Parent je chilo(Built-in) take overwrite kore eke save kore dicchi. 
    """
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            # je request korteche tar account
            'account' : self.request.user.account, # ei account ta form er moddhe ("def __init__(self, *args, **kwargs):") access kortechilam account naame (same naam duijaygatei thakte hobe)
        })
        return kwargs
    
    # Transaction vede Title nirdharon korar jonno
    # context ta frontend e send kore dibo (Diposite, Withdraw, LoanRequest)
    # jokhon amra TransactionCreateMixin ke iherite kore Deposit/Withdraw/LoanRequest Form toiri korbo, tokhon user chaile just title ta filup korlei ei function ta call hobe & title ta save hoye jabe.
    def get_context_data(self, **kwargs):
        # built-in context ke niye ashbo tarpor setake context.update er sahajje overwrite kore dibo.
        context = super().get_context_data(**kwargs)
        context.update({
            'title' : self.title
        })
        return context

class DepositMoneyView(TransactionCreateMixin):
    # jehetu template, model egula Deposit, Withdraw, LoanRequest sobar jonno same thakbe
    # tai egula ekhane ar lagbena.
    # form jehtu alada alada tai form lagbe.
    form_class = DepositForm
    title = 'Deposit'

    # return the initial data to use for forms on this view.
    # initial kono data ami form er moddhe agei pass kore dite chai. Jemon ekjon User form ta submit kore nai, just view korteche thik oi muhurte ami ekta data ke push kore dilam. User dekhte pacche na. 
    def get_initial(self):
        initial = {'transaction_type' : DEPOSIT}
        return initial
    
    # user form ta fillup korar por backend theke check korbo form ta valid kina, orthat form requirments onujayi fillup hoyeche kina. 
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount
        account.save(
            update_fields = ['balance']  
        )
        messages.success(self.request, f'${amount} was deposited to your account successfully')
        #----------------------------------
        # Sending Email
        send_transaction_email(self.request.user, amount, "Deposit Message", 'transaction/deposit_mail.html')
        #----------------------------------
        return super().form_valid(form)
    
class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type' : WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance -= amount
        account.save(
            update_fields = ['balance']
        )
        messages.success(self.request, f"Successfully withdrawn ${amount} from your account")
        #----------------------------------------
        # Sending Email
        send_transaction_email(self.request.user, amount, "Withdrawal Message", 'transaction/withdraw_mail.html')
        #----------------------------------------
        return super().form_valid(form)

class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type' : LOAN}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        # Transaction Model er object theke kichu jinish filter kore niye ashlam. 
        # Accont filter korbe, transaction_type (3 means LOAN) tarpor check kore dekbe je Loan_Approve True kina, jodi True Hoy tahole count kore niye ashbe. (Total kotobar Loan niyeche seta count kora holo)
        current_loan_count = Transaction.objects.filter(account = self.request.user.account, transaction_type = 3, loan_approve = True).count() # 3 means LOAN jeta constants er moddhe bole deya ache. 3 er bodole LOAN dileu hoto
        if current_loan_count >= 3:
            return HttpResponse("You have crossed your limits")
        messages.success(self.request, f"Loan request for amount ${amount} has been successfully sent to admin")
        #----------------------------------
        # Sending Email
        send_transaction_email(self.request.user, amount, "Loan Request Message", 'transaction/loan_request_mail.html')
        #----------------------------------
        return super().form_valid(form)
    
class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transaction/transaction_report.html'
    model = Transaction
    balance = 0 # eta built-in kono field na.
    context_object_name = 'report_list'

    def get_queryset(self):
        # jodi user kono type filter na kore tahole tar total transaction report dekhabo.
        queryset = super().get_queryset().filter(
            account = self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
            # User jodi filter kore tahole queryset ta emon hobe.
            # Eta bujhte somossha hole ba kothin lagle (Nicher ta kheyal kori)
            # user er account er information gulake filter kortechi. (queryset = super().get_queryset().filter(account = self.request.user.account)) ei account er user er
            queryset = queryset.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date) # gte --> greater than equal, lte --> less than equal

            self.balance = Transaction.objects.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
        return queryset

    def get_context_data(self, **kwargs):
        # built-in context ke niye ashbo tarpor setake context.update er sahajje overwrite kore dibo.
        context = super().get_context_data(**kwargs)
        context.update({
            'account' : self.request.user.account
        })
        return context
    
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id = loan_id)
        
        if loan.loan_approve: # ekjon user loan pay korte parbe tokhoni jokhon tar loan approve hobe.
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(self.request, f'Loan amount is greater than available balance')
                return redirect('loan_pay')

class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transaction/loan_request.html'
    context_object_name = 'loans' # total loan list ta ei loans er moddhe thakbe.

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account = user_account, transaction_type = LOAN)
        return queryset