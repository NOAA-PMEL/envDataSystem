import json
# from urllib.request import HTTPDefaultErrorHandler

from shared.data.message import Message


class Status:

    ENABLING = "ENABLING"
    ENABLED = "ENABLED"
    DISABLING = "DISABLING"
    DISABLED = "DISABLED"

    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    READY_TO_RUN = "READY_TO_RUN"
    STOPPING = "STOPPING"
    SHUTING_DOWN = "SHUTTING_DOWN"
    SHUTDOWN = "SHUTDOWN"
    
    READY = "READY"
    NOT_READY = "NOT_READY"

    NOT_REGISTERED = "NOT_REGISTERED"
    REGISTERED = "REGISTERED"
    REGISTERING = "REGISTERING"
    UNREGISTERING = "UNREGISTERING"

    NOT_CONFIGURED = "NOT_CONFIGURED"
    CONFIGURED = "CONFIGURED"
    CONFIGURING = "CONFIGURING"

    NOT_CONNECTED = "NOT_CONNECTED"
    CONNECTED = "CONNECTED"
    CONNECTING = "CONNECTING"

    OK = "OK"
    NOT_OK = "NOT_OK"

    UNKNOWN = "UNKNOWN"

    def __init__(
        self,
        enabled_status=None,
        run_status=None,
        config_status=None,
        connection_status=None,
        health_status=None,
    ) -> None:

        self.status_types = [
            "enabled_status",
            "run_status",
            "config_status",
            "registration_status",
            "connection_status",
            "health_status",
        ]
        self.status_map = dict()

        if enabled_status:
            self.set_enabled_status(enabled_status)
        else:
            self.set_enabled_status(Status.DISABLED)

        if run_status:
            self.set_run_status(run_status)
        else:
            self.set_run_status(Status.STOPPED)

        if config_status:
            self.set_config_status(config_status)
        else:
            self.set_config_status(Status.NOT_CONFIGURED)

        if config_status:
            self.set_registration_status(config_status)
        else:
            self.set_registration_status(Status.NOT_REGISTERED)

        if connection_status:
            self.set_connection_status(connection_status)
        else:
            self.set_run_status(Status.NOT_CONNECTED)

        if health_status:
            self.set_health_status(connection_status)
        else:
            self.set_health_status(Status.NOT_OK)


    def set_status(self, status_type, status):

        self.status_map[status_type] = status
        # print(f"status: {self.status_map}")

    def get_status(self, status_type):

        try:
            return self.status_map[status_type]
        except KeyError:
            return Status.UNKNOWN

    def set_enabled_status(self, status):
        self.set_status("enabled_status", status)

    def get_enabled_status(self):
        return self.get_status("enabled_status")

    def set_run_status(self, status):
        self.set_status("run_status", status)

    def get_run_status(self):
        return self.get_status("run_status")

    def set_config_status(self, status):
        self.set_status("config_status", status)

    def get_config_status(self):
        return self.get_status("config_status")

    def set_registration_status(self, status):
        self.set_status("registration_status", status)

    def get_registration_status(self):
        return self.get_status("registration_status")

    def set_connection_status(self, status):
        self.set_status("connection_status", status)

    def get_connection_status(self):
        return self.get_status("connection_status")

    def set_health_status(self, status):
        self.set_status("health_status", status)

    def get_health_status(self):
        return self.get_status("health_status")

    def to_message(self, sender_id=None):
        if sender_id:

            # status_dict = dict()
            # for st in self.status_types:
            #     status_dict[st] = self.get_status(st)

            msg = Message(
                sender_id=sender_id,
                msgtype='GENERIC',
                subject="STATUS",
                body={
                    'purpose': 'UPDATE',
                    'status': self.to_dict()
                    # 'status_object': self
                    # 'note': note,
                }
            )

            return msg

    def from_message(self, msg):

        if msg:
            try:
                status_msg = msg["message"]["BODY"]["status"]
                self.from_dict(status_msg)
                # for status_type, status in status_msg.items():
                #     self.set_status(status_type, status)
            except KeyError:
                print("could not get status from message")

    def to_dict(self):
        status_dict = dict()
        for st in self.status_types:
            # print(f"st: {st}")
            status_dict[st] = self.get_status(st)
            # print(f"status_dict: {status_dict}")
        return status_dict

    def from_dict(self, status_dict):
        if status_dict:
            for status_type, status in status_dict.items():
                if status_type in self.status_types:
                    self.set_status(status_type, status)

