import paramiko
import threading
from channels.generic.websocket import WebsocketConsumer
from virtualmachine.models import KliendiVM
from virtualmachine.views import get_vm_ip


class SSHConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()

        try:
            vmid = self.scope["url_route"]["kwargs"]["vmid"]
            vm = KliendiVM.objects.get(vmid=vmid)

            vm_ip = get_vm_ip(vm.node, vm.vmid)

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.ssh.connect(
                hostname=vm_ip,
                username="ubuntu",
                key_filename=f"/KUS_IGANES/vps/ssh_keys/vm_{vm.vmid}" # MUUDA KUHU PANNA SSH KEYD
            )

            self.channel = self.ssh.invoke_shell()

            self.alive = True
            threading.Thread(target=self.read_from_ssh, daemon=True).start()

        except Exception as e:
            self.close()

    def read_from_ssh(self):
        try:
            while self.alive:
                data = self.channel.recv(1024).decode(errors="ignore")
                if data:
                    self.send(data)
        except:
            self.alive = False

    def receive(self, text_data):
        if self.channel:
            self.channel.send(text_data)

    def disconnect(self, close_code):
        self.alive = False
        if hasattr(self, "ssh"):
            self.ssh.close()