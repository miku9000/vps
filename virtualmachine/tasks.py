from celery import shared_task
from .models import KliendiVM
import subprocess
import json
import os
import logging

logger = logging.getLogger(__name__)

TERRAFORM_SERVER = "JOHN_KASUTAJA@192.168.x.x" # ANDMEBAAS_KASUTAJA@ANDMEBAAS_IP

@shared_task
def create_vm_task(vm_id):
    logger.warning(f"TASK STARTED {vm_id}")

    vm = KliendiVM.objects.get(id=vm_id)

    vm.status = "creating"
    vm.save()

    KEY_DIR = "/home/john_veebiserver/vps/ssh_keys"

    key_path = f"{KEY_DIR}/vm_{vm.vmid}"

    # generate SSH key pair
    subprocess.run([
        "ssh-keygen",
        "-t", "ed25519",
        "-f", key_path,
        "-N", ""
    ], check=True)

    with open(f"{key_path}.pub") as f:
        public_key = f.read()

    remote_cmd = (
        f"cd /home/john_andmebaas/terraform/terraform-cloud-init-2204 && "
        f"terraform apply -auto-approve "
        f"-var='node={vm.node}' "
        f"-var='vmid={vm.vmid}' "
        f"-var='vmname=VM-user-{vm.user}' "
        f"-var='ssh_public_key={public_key.strip()}'"
    )

    result = subprocess.run(
        [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            TERRAFORM_SERVER,
            remote_cmd,
        ],
        capture_output=True,
        text=True
    )

    logger.warning(f"STDOUT:\n{result.stdout}")
    logger.warning(f"STDERR:\n{result.stderr}")
    logger.warning(f"RETURN CODE: {result.returncode}")

    vm.status = "running"
    vm.save()