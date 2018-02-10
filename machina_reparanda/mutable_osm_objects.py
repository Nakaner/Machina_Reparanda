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

    def __str__(self):
        return "lat: {} lon: {}".format(self.lat, self.lon)


class MutableNodeRef:
    def __init__(self, base):
        self.location = MutableLocation(base.location)
        self.ref = base.ref

    def __str__(self):
        if self.location is not None:
            return "nd: {} @ {}".format(self.ref, self.location)
        return "nd: {}".format(self.ref)


class MutableNodeRefList():
    def __init__(self, base):
        # TODO imitate correct interface
        self._nodes = []
        for n in base:
            self._nodes.append(MutableNodeRef(n))

    def __iter__(self):
        return self._nodes.__iter__()

    def __str__(self):
        result = "  nodes:\n"
        for n in self._nodes:
            result += "    {}\n".format(n.__str__())
        return result


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

    def __str__(self):
        result = "  tags:\n"
        for t in self._tags:
            result += "    {}".format(t)
        return t

    def items(self):
        return self._tags.items()

    def get(self, key, default=None):
        return self._tags.get(key, default)

    def pop(self, key, default=None):
        return self._tags.pop(key, default)


class MutableRelationMember():
    def __init__(self, base):
        self.ref = base.ref
        self.type = base.type
        self.role = base.role

    def __str__(self):
        return "    {} {} as {}\n".format(self.type, self.ref, self.role)


class MutableRelationMemberList():
    def __init__(self, base):
        # TODO imitate correct interface
        self.members = []
        for m in base:
            self.members.append(MutableRelationMember(m))

    def __str__(self):
        result = "  tags:\n"
        for m in self.members:
            result += m.__str__()
