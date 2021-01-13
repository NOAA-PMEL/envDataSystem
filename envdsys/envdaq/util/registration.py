import uuid


class RegistrationManager:
    _registry = dict()
    # TODO: need a way to stop/shutdown gracefully

    @staticmethod
    def add(id, type="DAQServer"):

        if type not in RegistrationManager._registry:
            RegistrationManager._registry[type] = dict()

        registration = {
            "regkey": f"{uuid.uuid4()}",
            "config": None,
        }

        RegistrationManager._registry[type][id] = registration
        return registration

    @staticmethod
    def get(id, type="DAQServer"):

        if type not in RegistrationManager._registry:
            RegistrationManager._registry[type] = dict()

        if id not in RegistrationManager._registry[type]:
            return None
        else:
            return RegistrationManager._registry[type][id]

    @staticmethod
    def update(id, registration, type="DAQServer"):

        old_reg = RegistrationManager.get(id, type)

        if not old_reg:
            RegistrationManager.add(id, type)

        RegistrationManager._registry[type][id] = registration

    @staticmethod
    def remove(id, type="DAQServer"):

        try:
            RegistrationManager._registry.pop(id)
        except KeyError:
            # already gone
            pass

    @staticmethod
    def get_registry(type="DAQServer"):

        try:
            registry = RegistrationManager._registry[type]
        except KeyError:
            registry = None
        return registry
