from multiprocessing.dummy import Lock

class Singleton(type):
    _instances = {}

    __singleton_lock = Lock()
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls.__singleton_lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]