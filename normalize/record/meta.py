
from __future__ import absolute_import

from normalize.property import Property


class RecordMeta(type):
    """Metaclass to reify descriptors properly"""
    def __new__(mcs, name, bases, attrs):

        properties = dict()

        for base in bases:
            if hasattr(base, "properties"):
                for propname, prop in base.properties.iteritems():
                    if propname in properties:
                        raise Exception(
                            "Property '%s' defined by multiple base "
                            "classes of %s" % (propname, name)
                        )
                    else:
                        properties[propname] = prop

        local_props = dict()

        for attrname, attrval in attrs.items():
            # don't allow clobbering of these meta-properties in class
            # definitions
            if attrname in frozenset(('properties', 'required')):
                raise Exception("Attribute '%s' is reserved")
            if isinstance(attrval, Property):
                properties[attrname] = attrval
                if not attrval.bound:
                    local_props[attrname] = attrval

        all_properties = set(properties.values())

        def coerce_prop_list(prop_list_field):
            proplist = attrs.get(prop_list_field, None)
            good_props = []
            if proplist:
                for prop in proplist:
                    if isinstance(prop, basestring):
                        prop = properties[prop]
                    if not isinstance(prop, Property) or (
                        prop not in all_properties
                    ):
                        raise Exception(
                            "%s must be a collection of Properties "
                            "in this class (names or Property objects)" % (
                                prop_list_field
                            )
                        )
                good_props.append(prop)
            return tuple(good_props)

        attrs['primary_key'] = coerce_prop_list('primary_key')
        attrs['properties'] = properties
        attrs['required'] = frozenset(
            k for k, v in properties.iteritems() if v.required
        )

        self = super(RecordMeta, mcs).__new__(mcs, name, bases, attrs)

        for propname, prop in local_props.iteritems():
            prop.bind(self, propname)

        return self
