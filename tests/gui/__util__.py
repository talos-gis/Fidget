import inspect


def test_as_main(*args, **kwargs):
    def ret(func):
        calling_mod = inspect.getmodule(inspect.stack()[1][0])
        if calling_mod.__name__ == '__main__':
            from fidget.backend.QtWidgets import QApplication

            app = QApplication([])
            w = func(*args, **kwargs)
            w.show()
            res = app.exec_()
            print(w.value())
            if res != 0:
                exit(res)
        return func

    return ret
