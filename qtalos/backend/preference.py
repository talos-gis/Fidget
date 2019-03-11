from typing import Dict, Union, Optional

from warnings import warn

from qtalos.backend.qtbackend import QtBackend, PyQt5_backend, PySide2_backend

priority: Optional[QtBackend] = None
fail_ok = True

backends: Dict[str, QtBackend] = {'PySide2': PySide2_backend, 'PyQt5': PyQt5_backend}

loaded: Optional[QtBackend] = None


def prefer(backend: Union[QtBackend, str], try_all=False):
    global priority, fail_ok

    if loaded:
        warn('a backend was already loaded (call prefer before importing qtalos)')

    if priority:
        warn('a previous priority backend was already set')

    if isinstance(backend, str):
        backend = backends[backend]

    priority = backend
    fail_ok = try_all


def load() -> QtBackend:
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
            return loaded

    raise first_err or Exception('no backend are configured')
