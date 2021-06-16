# from PySide6.QtWidgets import QAction
from typing import Union, Optional, OrderedDict

from warnings import warn

from fidget.backend.qtbackend import QtBackend, PySide6_backend, PySide2_backend, PyQt6_backend, PyQt5_backend

priority: Optional[QtBackend] = None
fail_ok = True

backends_list = [PySide6_backend, PySide2_backend, PyQt5_backend]
# PyQt6_backend  # not supported yet...
backends = OrderedDict[str, QtBackend]((b.__name__, b) for b in backends_list)

loaded: Optional[QtBackend] = None


def prefer(backend: Union[QtBackend, str], try_all=True):
    """
    Set a preference for a backend to use.
    :param backend: the backend to attempt to import first.
     See "fidget.backend.preference.backends" for a full list of available backends.
    :param try_all: whether to try other backends if the preferred backend fails
    """
    global priority, fail_ok

    if loaded:
        warn('a backend was already loaded (call prefer before importing other fidget packages)')

    if priority:
        warn('a previous priority backend was already set')

    if isinstance(backend, str):
        backend = backends[backend]

    priority = backend
    fail_ok = try_all


def load() -> QtBackend:
    """
    load backends until one succeeds and returns that backend.
    :return: the first successful backend
    """
    global loaded

    if loaded:
        return loaded

    first_err = None

    if priority:
        try:
            priority.load()
        except ImportError as e:
            if not fail_ok:
                raise
            first_err = e
        else:
            loaded = priority
            print(f'Using selected backend: {loaded.__name__}')
            return loaded

    for backend in backends.values():
        if backend is priority:
            continue

        try:
            backend.load()
        except ImportError as e:
            if not first_err:
                first_err = e
        else:
            loaded = backend
            print(f'Using backend: {loaded.__name__}')
            return loaded

    if not first_err:
        raise Exception('no backend are configured')
    raise Exception('all backends failed to load') from first_err
