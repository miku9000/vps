from celery import shared_task
from .models import KliendiVM
import subprocess
import json
import os
import logging
import uuid
import shutil

logger = logging.getLogger(__name__)

TERRAFORM_SERVER = "DB_KASUTAJA@DB_IP" # siia oma andmebaasi server kasutaja ja ip

BASE_TF_DIR = "/ROOT_DIRECTORY/terraform/terraform-cloud-init-2204" # siia panna terraform skriptid
REMOTE_RUNS_DIR = "/ROOT_DIRECTORY/terraform/runs" # siia lähevad terraform virtuaalmasinad
KEY_DIR = "/ROOT_DIRECTORY/vps/ssh_keys" # siia lähevad virtuaalmasinate ssh võtmed

def run_stream(cmd, label):
    logger.info(f"{label} START")
    logger.info(f"{label} CMD {cmd}")

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    output = []

    for line in p.stdout:
        line = line.rstrip()
        output.append(line)
        logger.info(f"{label} {line}")

    p.wait()

    logger.info(f"{label} END RC={p.returncode}")

    return p.returncode, "\n".join(output)


def ssh(cmd, label):
    return run_stream([
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        TERRAFORM_SERVER,
        cmd
    ], label)


def scp(local, remote, label):
    return run_stream([
        "scp",
        local,
        remote
    ], label)


@shared_task
def create_vm_task(vm_id):
    logger.warning(f"TASK START vm_id={vm_id}")

    vm = KliendiVM.objects.get(id=vm_id)

    if vm.status != "creating":
        logger.warning("SKIP wrong state")
        return

    vm.status = "creating"
    vm.save()

    run_id = str(uuid.uuid4())
    remote_vm_dir = f"{REMOTE_RUNS_DIR}/vm_{vm.vmid}_{run_id}"

    logger.info(f"RUN_ID {run_id}")
    logger.info(f"REMOTE_DIR {remote_vm_dir}")

    key_path = f"{KEY_DIR}/vm_{vm.vmid}"

    if not os.path.exists(key_path):
        rc, _ = run_stream([
            "ssh-keygen",
            "-t",
            "rsa",
            "-b",
            "4096",
            "-f",
            key_path,
            "-N",
            ""
        ], "SSH_KEYGEN")

        if rc != 0:
            vm.status = "error"
            vm.save()
            return

    with open(f"{key_path}.pub") as f:
        public_key = f.read().strip()

    logger.info(f"PUBLIC_KEY {public_key}")

    rc, _ = ssh(
        f"rm -rf {remote_vm_dir} && mkdir -p {remote_vm_dir} && cp -r {BASE_TF_DIR}/* {remote_vm_dir}/",
        "REMOTE_SETUP"
    )

    if rc != 0:
        vm.status = "error"
        vm.save()
        return



    tfvars = {
        "node": vm.node,
        "vmid": vm.vmid,
        "vmname": f"VM-user-{vm.user}-{run_id}",
        "ssh_public_key": public_key,
        "ip": vm.ip
    }

    local_tfvars = f"/tmp/vm_{vm.vmid}_{run_id}.json"

    with open(local_tfvars, "w") as f:
        json.dump(tfvars, f)

    remote_tfvars = f"{remote_vm_dir}/vars.json"

    rc, _ = scp(local_tfvars, f"{TERRAFORM_SERVER}:{remote_tfvars}", "SCP_TFVARS")

    if rc != 0:
        vm.status = "error"
        vm.save()
        return

    tf_cmd = (
        f"cd {remote_vm_dir} && "
        f"terraform init -input=false && "
        f"terraform apply -auto-approve -var-file=vars.json"
    )

    rc, output = ssh(tf_cmd, "TERRAFORM_APPLY")

    logger.info(f"TERRAFORM_RC {rc}")
    logger.info(f"TERRAFORM_OUTPUT_START")
    logger.info(output)
    logger.info(f"TERRAFORM_OUTPUT_END")

    if rc == 0:
        vm.status = "running"
        logger.warning(f"VM RUNNING vmid={vm.vmid}")
    else:
        vm.status = "error"
        logger.error(f"VM FAILED vmid={vm.vmid}")

    vm.save()