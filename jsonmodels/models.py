import six

from . import parsers, errors
from .errors import ValidationError
from .fields import BaseField


class Base(object):

    _strict_ = False

    """Base class for all models."""

    def __init__(self, **kwargs):
        self._update_names()
        self.populate(**kwargs)

    def _update_names(self):
        for name, field in self:
            field._set_name(name)

    def populate(self, **kw):
        """Populate values to fields. Skip non-existing."""
        name_to_field = {
            name: field for name, field in self.iterate_over_fields()}
        diff = [name for name in kw if name not in name_to_field]
        if diff and self._strict_:
            raise ValidationError('non expected arguments {}'.format(diff))

        for name, value in kw.iteritems():
            if name in diff:
                continue
            name_to_field[name].__set__(self, value)

    def get_field(self, field_name):
        """Get field associated with given attribute."""
        for attr_name, field in self:
            if field_name == attr_name:
                return field

        raise errors.FieldNotFound('Field not found', field_name)

    def __iter__(self):
        """Iterate through fields and values."""
        for name, field in self.iterate_over_fields():
            yield name, field

    def validate(self):
        """Explicitly validate all the fields."""
        for name, field in self:
            try:
                field.validate_for_object(self)
            except ValidationError as error:
                raise ValidationError(
                    "Error for field '{name}'.".format(name=name),
                    error,
                )

    @classmethod
    def iterate_over_fields(cls):
        """Iterate through fields and values."""
        for attr in dir(cls):
            clsattr = getattr(cls, attr)
            if isinstance(clsattr, BaseField):
                yield attr, clsattr

    def to_struct(self):
        """Cast model to Python structure."""
        return parsers.to_struct(self)

    @classmethod
    def to_json_schema(cls):
        """Generate JSON schema for model."""
        return parsers.to_json_schema(cls)

    def __repr__(self):
        try:
            txt = six.text_type(self)
        except TypeError:
            txt = ''
        return '<{name}: {text}>'.format(
            name=self.__class__.__name__,
            text=txt,
        )

    def __str__(self):
        return '{name} object'.format(name=self.__class__.__name__)

    def __setattr__(self, name, value):
        try:
            return super(Base, self).__setattr__(name, value)
        except ValidationError as error:
            raise ValidationError(
                "Error for field '{name}'.".format(name=name),
                error
            )
