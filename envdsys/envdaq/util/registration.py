import uuid
import asyncio


class RegistrationManager:
    _registry = dict()
    # TODO: need a way to stop/shutdown gracefully
    run_state = "STOPPED"

    # number of seconds before daq_server is considered 
    #   disconnected
    disconnected_limit = 10

    # number of seconds before daq_server is removed 
    #   from registry
    auto_clean_limit = 600  # 10 minutes 

    def start_checks():
        if RegistrationManager.run_state == "STOPPED":

            asyncio.create_task(RegistrationManager.run_checks())
            RegistrationManager.run_state = "STARTED"

    @staticmethod
    def ping(id, type="DAQServer"):

        try:
            RegistrationManager._registry[type][id]["age"] = 0
            RegistrationManager._registry[type][id]["status"] = "CONNECTED"
        except KeyError:
            # registration does not exist
            pass

    @staticmethod
    def add(id, config={}, type="DAQServer"):

        RegistrationManager.start_checks()

        if type not in RegistrationManager._registry:
            RegistrationManager._registry[type] = dict()

        registration = {
            "regkey": f"{uuid.uuid4()}",
            "config": config,
            "age": 0,
            "status": "CONNECTED"
        }

        RegistrationManager._registry[type][id] = registration
        return registration

    @staticmethod
    def get(id, type="DAQServer"):

        RegistrationManager.start_checks()

        if type not in RegistrationManager._registry:
            RegistrationManager._registry[type] = dict()

        if id not in RegistrationManager._registry[type]:
            return None
        else:
            return RegistrationManager._registry[type][id]

    @staticmethod
    def update(id, registration, type="DAQServer"):

        RegistrationManager.start_checks()

        old_reg = RegistrationManager.get(id, type)

        if not old_reg:
            RegistrationManager.add(id, type)

        RegistrationManager._registry[type][id] = registration

    @staticmethod
    def remove(id, type="DAQServer"):

        RegistrationManager.start_checks()

        try:
            RegistrationManager._registry.pop(id)
        except KeyError:
            # already gone
            pass

    @staticmethod
    def get_registry(type="DAQServer"):

        RegistrationManager.start_checks()

        try:
            registry = RegistrationManager._registry[type]
        except KeyError:
            registry = None
        return registry

    async def run_checks():

        while True:
            # print("registry check")
            for type, registry in RegistrationManager._registry.items():
                for k, v in registry.items():
                    v["age"] += 2
                    if v["age"] > RegistrationManager.auto_clean_limit:
                        RegistrationManager.remove(k, type)
                        print(f'Removing {type} {id} from registry')
                        continue
                    elif v["age"] > RegistrationManager.disconnected_limit:
                        v['status'] = "DISCONNECTED"
                        print(f'{type} {k} looks to be disconnected') 
                    RegistrationManager._registry[type][k] = v
                # print(f'registry: {registry}')
            await asyncio.sleep(2)
