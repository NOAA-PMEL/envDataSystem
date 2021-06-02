import json
from pathlib import Path


class Namespace:

    DEFAULT_HOST = "localhost"
    # DEFAULT_IP = "127.0.0.1"

    DEFAULT_NAME = "default"

    DAQSERVER = "daqserver"
    CONTROLLER = "controller"
    INSTRUMENT = "instrument"

    def __init__(self, name=None, host=None, ns_type=None, parent_ns=None):

        self.namespace = dict()

        self.set_name(name)
        # if not name:
        #     self.name = Namespace.DEFAULT_NAME
        # self.set_name(name)

        self.host = None
        self.parent = None

        self.host = None
        if host:
            self.host = host
            # self.set_host_name(host_name)

        # self.host_ip = None
        # if host_ip:
        #     # self.host_ip = host_ip
        #     self.set_host_name(host_ip)

        if not ns_type:
            ns_type = Namespace.DAQSERVER
        self.ns_type = ns_type

        # overides host/ip values
        if parent_ns:
            self.add_to_parent_ns(parent_ns)

        # if not any(k in self.namespace for k in ["host_name", "host_ip"]):
        #     self.namespace = Namespace.DEFAULT_HOST

    def set_name(self, name):
        if not name:
            name = Namespace.DEFAULT_NAME

        not_allowed = [" ", "/", "<", ">", "?", "@", "&", ",", ";", ":", "!"]
        for na in not_allowed:
            name = name.replace(na, "_")
        self.name = name

    # def set_host_name(self, name):
    #     # if not self.host:
    #     #     self.host = dict()
    #     self.host = name
    # if "server" not in self.namespace:
    #     self.namespace["server"] = dict()
    # self.namespace["server"]["host_name"] = name

    # def set_host_ip(self, ip):
    #     self.host["host_ip"] = ip
    # if "server" not in self.namespace:
    #     self.namespace["server"] = dict()
    # self.namespace["server"]["host_ip"] = ip

    # def set_server(self, server):
    #     self.namespace["server"] = server

    # only top level namespace will hold host?
    def has_host(self):
        if self.host:
            return True
        else:
            return False

    # def get_host(self):

    #     if self.has_host():
    #         return self.host
    #     else:
    #         if self.parent():
    #             return self.parent.get_host()
    #         else:
    #             if "host_name" not in self.host and "host_ip" not in self.host:
    #                 self.set_host_name(Namespace.DEFAULT_HOST)
    #             return self.host
    # if "server" not in self.namespace:
    #     self.set_host_name(Namespace.DEFAULT_HOST)
    #     # self.host_name = Namespace.DEFAULT_HOST
    #     # self.namespace["server"] = {"host_name": Namespace.DEFAULT_HOST}

    # return self.namespace["server"]

    # def set_name(self, name):
    #     self.namespace["name"] = name

    # def get_name(self):
    #     name = self.namespace["name"]

    # def set_parent(self, parent):
    #     self.namespace["parent"] = parent

    # def get_parent(self):
    #     return self.namespace["parent"]

    # def set_namespace(self, ns):
    #     if ns:
    #         self.namespace["name"] = ns.get_namespace()

    # def get_namespace(self):

    #     ns = {
    #         "name": self.get_name(),
    #         "parent": self.get_parent()
    #     }

    def add_to_parent_ns(self, parent_ns):

        if parent_ns:
            # self.host = parent_ns.get_host()
            self.parent = parent_ns
            # self.set_server(parent_ns.get_server())
            # self.namespace["parent"] = parent_ns.get_namespace()

    # return string representing ns
    def get_namespace(self):
        # ns = ""
        # print(f"self.name: {ns}")
        parent_ns = ""
        host = ""
        if self.parent:
            # print(f"self.name: {ns}")
            parent_ns = self.parent.get_namespace()
            ns = f"{parent_ns}-{self.name}"
            # print(f"self.name: {ns}")
            # ns = f"{parent_ns}-"
        else:
            if not self.host:
                self.host = Namespace.DEFAULT_HOST
            # if "host_name" in self.host:
            #     host = self.host["host_name"].split(".")[0]
            #     # print(f"self.host: {host}")
            # elif "host_ip" in self.host:
            #     host = self.host["host_ip"]
            #     # print(f"self.host: {host}")
            # else:
            #     host = Namespace.DEFAULT_HOST
            #     # print(f"self.host: {host}")
            # # ns = f"{host}-"

            ns = f"{self.host}-{self.name}"

        # print(f"self.name: {ns}")
        return ns

    def get_namespace_sig(self, section="ALL"):

        sig = dict()
        if section == "PARENT":
            sig = None
            if self.parent:
                sig = self.parent.get_namespace_sig()
            return sig
        elif section == "LOCAL":
            sig["host"] = self.get_host()
            sig["name"] = self.name
            sig["type"] = self.ns_type
            sig["namespace"] = f"{self.name}"
            return sig
        else:
            sig["host"] = self.get_host()
            sig["name"] = self.name
            sig["type"] = self.ns_type
            namespace = ""
            if self.parent:
                parent_sig = self.parent.get_namespace_sig()
                sig["namespace"] = f"{parent_sig['namespace']}-{self.name}"
            else:
                sig["namespace"] = f"{self.name}"

            return sig

    def get_host(self):

        if self.parent:
            host = self.parent.get_host()
        else:
            if not self.host:
                self.host = Namespace.DEFAULT_HOST
            host = self.host

        return host

    def get_parent_namespace(self):
        ns = None
        if self.parent:
            ns = f"{self.parent.get_namespace()}"
        return ns

    def get_local_namespace(self):
        if not self.host:
            self.host = Namespace.DEFAULT_HOST
        return f"{self.host}-{self.name}"

    def get_namespace_as_path(self):
        parent_path = None
        if self.parent:
            ns_path = self.parent.get_namespace_as_path()
            ns_path /= self.name
            return ns_path
        else:
            return Path(self.name)

    # return dictionary repr of ns
    def to_dict(self):

        ns_dict = {
            "name": self.name,
            "ns_type": self.ns_type,
        }
        if self.host:
            ns_dict["host"] = self.host

        if self.parent:
            ns_dict["parent"] = self.parent.to_dict()

        return ns_dict
        # ns_dict = dict()
        # if self.parent:
        #     ns_dict["parent"] = self.parent.to_dict()
        # else:
        #     ns_dict=["host"] = self.host

    # create from dictionary repr of ns
    def from_dict(self, ns_dict):
        if ns_dict:

            try:
                self.name = ns_dict["name"]
            except KeyError:
                self.name = Namespace.DEFAULT_NAME

            try:
                self.ns_type = ns_dict["ns_type"]
            except KeyError:
                self.ns_type = Namespace.DAQSERVER

            try:
                self.host = ns_dict["host"]
            except KeyError:
                pass

            try:
                parent_dict = ns_dict["parent"]
                self.parent = Namespace().from_dict(parent_dict)
            except KeyError:
                pass

        return self
