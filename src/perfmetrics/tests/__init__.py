# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from hamcrest.core.base_matcher import BaseMatcher


# XXX These matchers are temporary for Python 3.10 pending zodbpickle 2.2
# (nti.testing can't be imported on 3.10 before that version)

try:
    from nti.testing.matchers import is_true # pylint:disable=unused-import
except ImportError: # pragma: no cover
    class BoolMatcher(BaseMatcher):
        def __init__(self, value):
            super(BoolMatcher, self).__init__()
            self.value = value

        def _matches(self, item):
            return bool(item) == self.value

        def describe_to(self, description):
            description.append_text('object with bool() value ').append(str(self.value))

        def __repr__(self):
            return 'object with bool() value ' + str(self.value)

    def is_true():
        """
        Matches an object with a true boolean value.
        """
        return BoolMatcher(True)

try:
    from nti.testing.matchers import implements # pylint:disable=unused-import
except ImportError: # pragma: no cover
    class Implements(BaseMatcher):

        def __init__(self, iface):
            super(Implements, self).__init__()
            self.iface = iface

        def _matches(self, item):
            return self.iface.implementedBy(item)

        def describe_to(self, description):
            description.append_text('object implementing')
            description.append_description_of(self.iface)

    def implements(iface):
        """
        Matches if the object implements (is a factory for) the given
        interface.

        .. seealso:: :meth:`zope.interface.interfaces.ISpecification.implementedBy`
        """
        return Implements(iface)

try:
    from nti.testing.matchers import validly_provides # pylint:disable=unused-import
except ImportError: # pragma: no cover
    from zope.schema import ValidationError
    from zope.schema import getValidationErrors
    from zope.interface.exceptions import Invalid
    from zope.interface.verify import verifyObject
    import hamcrest

    class VerifyProvides(BaseMatcher):

        def __init__(self, iface):
            super(VerifyProvides, self).__init__()
            self.iface = iface

        def _matches(self, item):
            try:
                verifyObject(self.iface, item)
                return True
            except Invalid:
                return False

        def describe_to(self, description):
            description.append_text('object verifiably providing ').append_description_of(
                self.iface)

        def describe_mismatch(self, item, mismatch_description):
            md = mismatch_description

            try:
                verifyObject(self.iface, item)
            except Invalid as x:
                # Beginning in zope.interface 5, the Invalid exception subclasses
                # like BrokenImplementation, DoesNotImplement, etc, all typically
                # have a much nicer error message than they used to, better than we
                # were producing. This is especially true now that MultipleInvalid
                # is a thing.
                x = str(x).strip()

                md.append_text("Using class ").append_description_of(type(item)).append_text(' ')
                if x.startswith('The object '):
                    x = x[len("The object "):]
                    x = 'the object ' + x
                x = x.replace('\n    ', '\n          ')
                md.append_text(x)


    def verifiably_provides(*ifaces):
        """
        Matches if the object verifiably provides the correct interface(s),
        as defined by :func:`zope.interface.verify.verifyObject`. This means having
        the right attributes
        and methods with the right signatures.

        .. note:: This does **not** test schema compliance. For that
            (stricter) test, see :func:`validly_provides`.
        """
        if len(ifaces) == 1:
            return VerifyProvides(ifaces[0])

        return hamcrest.all_of(*[VerifyProvides(x) for x in ifaces])

    class VerifyValidSchema(BaseMatcher):
        def __init__(self, iface):
            super(VerifyValidSchema, self).__init__()
            self.iface = iface

        def _matches(self, item):
            errors = getValidationErrors(self.iface, item)
            return not errors

        def describe_to(self, description):
            description.append_text('object validly providing ').append(str(self.iface))

        def describe_mismatch(self, item, mismatch_description):
            x = None
            md = mismatch_description
            md.append_text(str(type(item)))

            errors = getValidationErrors(self.iface, item)

            for attr, exc in errors:
                try:
                    raise exc
                except ValidationError:
                    md.append_text(' has attribute "')
                    md.append_text(attr)
                    md.append_text('" with error "')
                    md.append_text(repr(exc))
                    md.append_text('"\n\t ')
                except Invalid as x: # pragma: no cover
                    md.append_text(str(x))

    def validly_provides(*ifaces):
        """
        Matches if the object verifiably and validly provides the given
        schema (interface(s)).

        Verification is done with :mod:`zope.interface` and
        :func:`verifiably_provides`, while validation is done with
        :func:`zope.schema.getValidationErrors`.
        """
        if len(ifaces) == 1:
            the_schema = ifaces[0]
            return hamcrest.all_of(verifiably_provides(the_schema), VerifyValidSchema(the_schema))

        prov = verifiably_provides(*ifaces)
        valid = [VerifyValidSchema(x) for x in ifaces]

        return hamcrest.all_of(prov, *valid)
