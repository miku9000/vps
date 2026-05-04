from django.shortcuts import render, redirect

# Create your views here.
from django.contrib.auth import login, authenticate, logout
from .models import Kasutaja
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_POST

def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = make_password(request.POST['password'])

        if Kasutaja.objects.filter(email=email).exists():
            return render(request, 'register.html', {
                'error': 'Email juba kasutuses'
            })

        user = Kasutaja.objects.create(
            username=username,
            email=email,
            password=password
        )
        login(request, user)
        return redirect('home')
    
    return render(request, 'register.html')

def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            return redirect('home')
        
    return render(request, 'login.html')

@require_POST
def user_logout(request):
    logout(request)
    return redirect('login')