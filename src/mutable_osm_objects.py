class MutableLocation:
    def __init__(self, base):
        self._valid = base.valid()
        self.x = base.x
        self.y = base.y
        # TODO add checks to lat and lon
        self.lat = base.lat_without_check()
        self.lon = base.lon_without_check()

    def valid(self):
        return self._valid

    def lat_without_check(self):
        return self.lat

    def lon_without_check(self):
        return self.lon


class MutableNodeRef:
    def __init__(self, base):
        self.location = MutableLocation(base.location)
        self.ref = base.ref


class MutableNodeRefList():
    def __init__(self, base):
        # TODO imitate correct interface
        self._nodes = []
        for n in base:
            self._nodes.append(MutableNodeRef(n))

    def __iter__(self):
        return self._nodes.__iter__()


class MutableWayNodeList(MutableNodeRefList):
    def __init__(self, base):
        MutableNodeRefList.__init__(self, base)


class MutableTagList():
    def __init__(self, base):
        # TODO imitate correct interface
        self._tags = dict()
        for t in base:
            self._tags[t.k] = t.v

    def __iter__(self):
        return self._tags.__iter__()

    def __getitem__(self, key):
        return self._tags[key]

    def __setitem__(self, key, value):
        self._tags[key] = value

    def __contains__(self, item):
        return item in self._tags

    def items(self):
        return self._tags.items()


class MutableRelationMember():
    def __init__(self, base):
        self.ref = base.ref
        self.type = base.type
        self.role = base.role


class MutableRelationMemberList():
    def __init__(self, base):
        # TODO imitate correct interface
        self.members = []
        for m in base:
            self.members.apend(MutableRelationMember(m))
