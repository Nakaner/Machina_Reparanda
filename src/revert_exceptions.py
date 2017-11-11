class OSMException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Unknown error"
        super(OSMException, self).__init__(msg)


class TagInvalidException(OSMException):
    def __init__(self, tag, msg=None):
        super(TagInvalidException, self).__init__(msg)
        self.tag = tag


class ProgrammingError(RuntimeError):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Unknown programming error"
        super(OSMException, self).__init__(msg)
