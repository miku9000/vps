from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from .models import KliendiVM
from .tasks import create_vm_task
import requests
import logging

logger = logging.getLogger(__name__)

PROXMOX_URL = "https://192.168.x.x:8006" # PROXMOX URL SIIA
TOKEN = "PVEAPIToken=PROX_KASUTAJA@REALM!TOKEN_NIMI=TOKEN_SALADUS" # PROXMOXI TOKEN SIIA
PROXMOX_NODE = "PROXMOX_NODE" # PROXMOX NODE SIIA
VM_START_ID = 800

def vm_dashboard(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    
    if not request.user.is_activated_user:
        return redirect(f"{reverse('ostuleht')}")
    
    vm = KliendiVM.objects.filter(user=request.user).first()

    if not vm:
        with transaction.atomic():
            vm = KliendiVM.objects.create(
                user=request.user,
                vmid=generate_vmid(),
                node=PROXMOX_NODE,
                status="creating",
                ip=allocate_ip()
            )

        create_vm_task.delay(vm.id)

    return render(request, 'dashboard.html', {'vm': vm})

def generate_vmid():
    with transaction.atomic():
        last_vm = (
            KliendiVM.objects
            .select_for_update()
            .order_by('-vmid')
            .first()
        )

        if last_vm:
            return last_vm.vmid + 1

    return VM_START_ID

def start_vm(request):
    if request.method == "POST":
        vm = KliendiVM.objects.get(user=request.user)
        url = f"{PROXMOX_URL}/api2/json/nodes/{vm.node}/qemu/{vm.vmid}/status/start"
        headers = {
            "Authorization": TOKEN
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                timeout=10,
                verify=False
            )

            logger.warning(response.text)

            response.raise_for_status()
            data = response.json()

            if data.get("data") is None:
                vm.status = "error"
            else:
                vm.status = "running"

        except Exception as e:
            logger.error(f"START VM FAILED: {e}")
            vm.status = "error"

        vm.save()
    
    return redirect(f"{reverse('dashboard')}")

def stop_vm(request):
    if request.method == "POST":
        vm = KliendiVM.objects.get(user=request.user)
        url = f"{PROXMOX_URL}/api2/json/nodes/{vm.node}/qemu/{vm.vmid}/status/stop"
        headers = {"Authorization": TOKEN}

        try:
            response = requests.post(
                url,
                headers=headers,
                timeout=10,
                verify=False
            )

            logger.warning(response.text)

            response.raise_for_status()
            data = response.json()

            if data.get("data") is None:
                vm.status = "error"
            else:
                vm.status = "stopped"

        except Exception as e:
            logger.error(f"START VM FAILED: {e}")
            vm.status = "error"

        vm.save()

    return redirect(f"{reverse('dashboard')}")

def allocate_ip():
    used = set(KliendiVM.objects.exclude(ip=None).values_list("ip", flat=True))
    base = "192.168.10."

    for i in range(220, 240):
        ip = f"{base}{i}"
        if ip not in used:
            return ip
    
    raise Exception("No free IPs")

def vm_console(request, vmid):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")

    if not request.user.is_activated_user:
        return redirect(f"{reverse('ostuleht')}")

    vm = KliendiVM.objects.get(user=request.user)

    return render(request, 'console.html', {"vm": vm})
