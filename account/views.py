from django.shortcuts import render, redirect
from django.views.generic import FormView
from . forms import UserRagistrationForm, UserUpdateForm
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View
# Create your views here.
class UserRegistrationView(FormView):
    template_name = "account/registration.html"
    form_class = UserRagistrationForm
    success_url = reverse_lazy("register")

    def form_valid(self, form):
        print(form.cleaned_data)
        user = form.save() # je 3 ta model create korechi sei 3 ta model e data save hoye jabe. (save function call korechi ar return value hisebe our_user er pacchi)
        login(self.request, user) # user er data gula diye login kore dilam. (registation form theke prapto data gula diye sorasori login kore dilam)
        print(user)
        return super().form_valid(form) # form_valid function ta call hobe jodi sob thik thake

class UserLoginView(LoginView):
    template_name = 'account/login.html'
    def get_success_url(self):
        return reverse_lazy('home')
    
class UserLogoutView(LogoutView):
    def get_success_url(self):
        if self.request.user.is_authenticated:
            logout(self.request)
        return reverse_lazy('home')
    
class UserBankAccountUpdateView(View):
    template_name = 'account/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance = request.user)
        return render(request, self.template_name, {'form' : form})
    
    def post(self, request):
        form = UserUpdateForm(request.POST, instance = request.user)

        if form.is_valid():
            form.save()
            return redirect('profile')
        return render(request, self.template_name, {'form' : form})