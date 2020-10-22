import errno
import fcntl
import os
import time

class lock_file:
    """Lock and open a file.

    If the file is opened for writing, an exclusive lock is used,
    otherwise it is a shared lock

    """
    def __init__(self, path, mode, timeout=None, **fileopts):
        self.path = path
        self.mode = mode
        self.fileopts = fileopts
        self.timeout = timeout
        # lock in exclusive mode when writing or appending (including r+)
        self._exclusive = set('wa+').intersection(mode)
        self._lockfh = None
        self._file = None

    def _acquire(self):
        if self._exclusive:
            # open the file in write & create mode, but *without the 
            # truncate flag* to make sure it is created only if it 
            # doesn't exist yet
            lockfhmode, lockmode = os.O_WRONLY | os.O_CREAT, fcntl.LOCK_EX
        else:
            lockfhmode, lockmode = os.O_RDONLY, fcntl.LOCK_SH
        self._lockfh = os.open(self.path, lockfhmode)
        start = time.time()
        while True:
            try:
                fcntl.lockf(self._lockfh, lockmode | fcntl.LOCK_NB)
                return
            except OSError as e:
                if e.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise
            if self.timeout is not None and time.time() - start > self.timeout:
                raise Exception()
            time.sleep(0.1)

    def _release(self):
        fcntl.lockf(self._lockfh, fcntl.LOCK_UN)
        os.close(self._lockfh)

    def __enter__(self):
        if self._file is not None:
            raise Exception('Lock already taken')
        self._acquire()
        self._file = open(self.path, self.mode, **self.fileopts)
        return self._file

    def __exit__(self, *exc):
        if self._file is None:
            raise Exception('Not locked')
        self._file.close()
        self._file = None
        self._release()