from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse

def subscription_home(request):
    return render(request, 'ostuleht.html')

def activate_user(request):
    status = request.GET.get('status')

    if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
    
    if request.method == "POST":
        # if statementid kontrollivad kas sa oled sisse logitud või konto on aktiveeritud juba

        if request.user.is_activated_user == True:
            return redirect(f"{reverse('tulemus')}?status=exists")
        
        # redirectib sind tulemusele, samal ajal aktiveerib konto
        try:
            request.user.is_activated_user = True
            request.user.save()

            return redirect(f"{reverse('tulemus')}?status=success")
        except Exception:
            return redirect(f"{reverse('tulemus')}?status=error")

    return render(request, 'tulemus.html', {'status': status})