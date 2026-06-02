import paramiko
import threading
import logging

from channels.generic.websocket import WebsocketConsumer
from virtualmachine.models import KliendiVM

logger = logging.getLogger(__name__)


class SSHConsumer(WebsocketConsumer):

    def connect(self):
        logger.warning("WEBSOCKET CONNECT START")

        try:
            vmid = self.scope["url_route"]["kwargs"]["vmid"]

            logger.warning(f"VMID {vmid}")

            vm = KliendiVM.objects.get(vmid=vmid)

            logger.warning(f"VM FOUND ip={vm.ip}")

            key_path = f"/home/john_veebiserver/vps/ssh_keys/vm_{vm.vmid}"

            logger.warning(f"KEY PATH {key_path}")

            privkey = paramiko.RSAKey.from_private_key_file(key_path)

            logger.warning("PRIVATE KEY LOADED")

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            logger.warning("CONNECTING PARAMIKO")

            self.ssh.connect(
                hostname=vm.ip,
                username="ubuntu",
                pkey=privkey,
                look_for_keys=False,
                allow_agent=False,
                timeout=15,
                banner_timeout=15,
                auth_timeout=15
            )

            logger.warning("PARAMIKO CONNECTED")

            self.channel = self.ssh.invoke_shell()

            logger.warning("SHELL INVOKED")

            self.alive = True

            self.accept()

            logger.warning("WEBSOCKET ACCEPTED")

            self.reader_thread = threading.Thread(
                target=self.read_from_ssh,
                daemon=True
            )

            self.reader_thread.start()

            logger.warning("READER THREAD STARTED")

        except Exception:
            logger.exception("CONNECT FAILED")

            try:
                self.close()
            except Exception:
                logger.exception("WEBSOCKET CLOSE FAILED")

    def read_from_ssh(self):
        logger.warning("READ LOOP START")

        try:
            while self.alive:

                if self.channel.recv_ready():

                    data = self.channel.recv(1024)

                    logger.warning(f"RECV RAW {len(data)} bytes")

                    if not data:
                        logger.warning("EMPTY DATA")
                        break

                    decoded = data.decode(errors="ignore")

                    logger.warning(f"SEND TO WS {repr(decoded[:200])}")

                    self.send(text_data=decoded)

        except Exception:
            logger.exception("READ LOOP FAILED")

        finally:
            logger.warning("READ LOOP END")
            self.alive = False

            try:
                self.close()
            except Exception:
                logger.exception("FINAL CLOSE FAILED")

    def receive(self, text_data):
        logger.warning(f"WS RECEIVE {repr(text_data)}")

        try:
            if hasattr(self, "channel") and self.channel:
                self.channel.send(text_data)

        except Exception:
            logger.exception("SSH SEND FAILED")

    def disconnect(self, close_code):
        logger.warning(f"DISCONNECT {close_code}")

        self.alive = False

        try:
            if hasattr(self, "channel"):
                self.channel.close()
        except Exception:
            logger.exception("CHANNEL CLOSE FAILED")

        try:
            if hasattr(self, "ssh"):
                self.ssh.close()
        except Exception:
            logger.exception("SSH CLOSE FAILED")