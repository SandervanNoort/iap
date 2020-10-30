import validate
import configobj
import numpy


def cobj_check(settings, exception=None, copy=False):
    """Check for errors in config file"""

    if not exception:
        exception = Exception

    validator = validate.Validator()

    def numpy_array(val):
        """Define float list"""
        float_list = validator.functions["float_list"](val)
        return numpy.array(float_list)
    validator.functions["numpy_array"] = numpy_array

    results = settings.validate(validator, copy=copy, preserve_errors=True)
    if results is not True:
        output = "{0}: \n".format(
            settings.filename if settings.filename is not None else
            "configobj")
        for (section_list, key, error) in configobj.flatten_errors(
                settings, results):
            if key is not None:
                val = settings
                for section in section_list:
                    val = val[section]
                val = val[key] if key in val else "<EMPTY>"
                output += "   [{sections}], {key}='{val}' ({error})\n".format(
                    sections=', '.join(section_list),
                    key=key,
                    val=val,
                    error=error)
            else:
                output += "Missing section: {0}\n".format(
                    ", ".join(section_list))
        raise exception(output)
