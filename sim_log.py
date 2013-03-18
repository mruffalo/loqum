from datetime import datetime
import logging
from os import makedirs
from os.path import join as ospj

def init_logger(name=None, level=logging.DEBUG):
    log_dir = 'logs'
    try:
        makedirs(log_dir)
    except OSError:
        # probably already exists
        pass
    desc = '{}_'.format(name) if name else ''
    log_filename_template = ospj(log_dir, 'log_{}{}.txt')
    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_filename = log_filename_template.format(desc, now)
    fh = logging.FileHandler(log_filename)
    fmt = logging.Formatter('{asctime}|{name}|{levelname}|{message}', style='{')
    fh.setFormatter(fmt)
    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(fh)
    return log

class LazyInitLogger:
    def __init__(self, name=None, level=logging.DEBUG):
        self.log = None
        self.name = name
        self.level = level

    def __getattr__(self, attr):
        if self.log is None:
            self.log = init_logger(self.name, self.level)
        return self.log.__getattribute__(attr)
