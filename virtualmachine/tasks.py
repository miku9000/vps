from celery import shared_task
from .models import KliendiVM
import subprocess
import json
import os
import logging

logger = logging.getLogger(__name__)

TERRAFORM_SERVER = "DB_KASUTAJA@DB_IP" # siia oma andmebaasi server kasutaja ja ip

BASE_TF_DIR = "/ROOT_DIRECTORY/terraform/terraform-cloud-init-2204" # siia panna terraform skriptid
REMOTE_RUNS_DIR = "/ROOT_DIRECTORY/terraform/runs" # siia lähevad terraform virtuaalmasinad


@shared_task
def create_vm_task(vm_id):
    logger.warning(f"TASK STARTED {vm_id}")

    vm = KliendiVM.objects.get(id=vm_id)

    if vm.status != "creating":
        logger.warning("VM not in creating state, skipping")
        return

    vm.status = "creating"
    vm.save()

    # Generate SSH key

    KEY_DIR = "/ROOT_DIRECTORY/vps/ssh_keys" # siia lähevad ssh võtmed
    key_path = f"{KEY_DIR}/vm_{vm.vmid}"

    subprocess.run([
        "ssh-keygen",
        "-t", "ed25519",
        "-f", key_path,
        "-N", ""
    ], check=True)

    with open(f"{key_path}.pub") as f:
        public_key = f.read().strip()

    # Prepare remote TF dir

    remote_vm_dir = f"{REMOTE_RUNS_DIR}/vm_{vm.vmid}"

    remote_setup_cmd = (
        f"rm -rf {remote_vm_dir} && "
        f"mkdir -p {remote_vm_dir} && "
        f"cp -r {BASE_TF_DIR}/* {remote_vm_dir}/"
    )

    subprocess.run([
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        TERRAFORM_SERVER,
        remote_setup_cmd
    ], check=True)

    # Write tfvars remotely

    tfvars = {
        "node": vm.node,
        "vmid": vm.vmid,
        "vmname": f"VM-user-{vm.user}",
        "ssh_public_key": public_key
    }

    local_tfvars = f"/tmp/vm_{vm.vmid}.json"

    with open(local_tfvars, "w") as f:
        json.dump(tfvars, f)

    remote_tfvars = f"{remote_vm_dir}/vars.json"

    subprocess.run([
        "scp",
        local_tfvars,
        f"{TERRAFORM_SERVER}:{remote_tfvars}"
    ], check=True)

    # Run Terraform (isolated)

    remote_apply_cmd = (
        f"cd {remote_vm_dir} && "
        f"terraform init -input=false && "
        f"terraform apply -auto-approve -var-file=vars.json"
    )

    result = subprocess.run(
        [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            TERRAFORM_SERVER,
            remote_apply_cmd,
        ],
        capture_output=True,
        text=True
    )

    logger.warning(f"STDOUT:\n{result.stdout}")
    logger.warning(f"STDERR:\n{result.stderr}")
    logger.warning(f"RETURN CODE: {result.returncode}")

    # Final status

    if result.returncode == 0:
        vm.status = "running"
    else:
        vm.status = "error"

    vm.save()