# -*- coding: utf-8 -*-
"""
Import this module to add the validation tween to your pyramid app.
"""
from __future__ import absolute_import

import re
from collections import namedtuple

from cached_property import cached_property
from pyramid.settings import asbool
from pyramid.settings import aslist
from six import iterkeys
from six import itervalues
from six import string_types


class InvalidPyramidSwaggerSettings(ValueError):
    pass


_Setting = namedtuple('_Setting', ['python_attr', 'settings_key', 'type', 'default_value'])
_DEFAULT_SETTINGS = {
    'schema_directory': _Setting('schema_directory', 'pyramid_swagger.schema_directory', string_types, 'api_docs/'),
    'schema_file': _Setting('schema_file', 'pyramid_swagger.schema_file', string_types, 'swagger.json'),
    'swagger_versions': _Setting('swagger_versions', 'pyramid_swagger.swagger_versions', (list, string_types), ['2.0']),  # gets converted to set
    'enable_swagger_spec_validation': _Setting('enable_swagger_spec_validation', 'pyramid_swagger.enable_swagger_spec_validation', (bool, string_types), True),
    'exclude_paths': _Setting('exclude_paths', 'pyramid_swagger.exclude_paths', (list, string_types), ['^/static/?', '^/api-docs/?', '^/swagger.(json|yaml)']),  # gets converted to set
    'exclude_routes': _Setting('exclude_routes', 'pyramid_swagger.exclude_routes', (list, string_types), ['catchall', 'no-validation']),  # gets converted to set
    'enable_request_validation': _Setting('enable_request_validation', 'pyramid_swagger.enable_request_validation', (bool, string_types), True),
    'enable_response_validation': _Setting('enable_response_validation', 'pyramid_swagger.enable_response_validation', (bool, string_types), True),
    'enable_path_validation': _Setting('enable_path_validation', 'pyramid_swagger.enable_path_validation', (bool, string_types), True),
    'use_models': _Setting('use_models', 'pyramid_swagger.use_models', (bool, string_types), False),
    'include_missing_properties': _Setting('include_missing_properties', 'pyramid_swagger.include_missing_properties', (bool, string_types), True),
    'validation_context_path': _Setting('validation_context_path', 'pyramid_swagger.validation_context_path', (string_types, type(None)), None),
    'enable_api_doc_views': _Setting('enable_api_doc_views', 'pyramid_swagger.enable_api_doc_views', (bool, string_types), True),
    'base_path_api_docs': _Setting('base_path_api_docs', 'pyramid_swagger.base_path_api_docs', string_types, ''),
    'generate_resource_listing': _Setting('generate_resource_listing', 'pyramid_swagger.generate_resource_listing', (bool, string_types), False),
    'dereference_served_schema': _Setting('dereference_served_schema', 'pyramid_swagger.dereference_served_schema', (bool, string_types), False),
    'prefer_20_routes': _Setting('prefer_20_routes', 'pyramid_swagger.prefer_20_routes', (list, string_types), []),  # gets converted to set
}


SWAGGER_12 = '1.2'
SWAGGER_20 = '2.0'
DEFAULT_SWAGGER_VERSIONS = [SWAGGER_20]
SUPPORTED_SWAGGER_VERSIONS = [SWAGGER_12, SWAGGER_20]
DEFAULT_EXCLUDED_PATHS = _DEFAULT_SETTINGS['exclude_paths'].default_value


def _load_setting(setting, setting_value):
    if not isinstance(setting_value, setting.type):
        raise InvalidPyramidSwaggerSettings(
            'TypeError: {setting.settings_key} should be of type {setting.type}. Current value {value.__class__}({value})'.format(
                setting=setting,
                value=setting_value,
            ),
        )

    if list in setting.type:
        return aslist(setting_value)
    elif bool in setting.type:
        return asbool(setting_value)
    else:
        return setting_value


def _is_valid_regex(pattern):
    try:
        re.compile(pattern)
        return True
    except:  # noqa E722 do not use bare except
        return False


class PyramidSwaggerSettings(
    namedtuple(
        'PyramidSwaggerSettings',
        list(iterkeys(_DEFAULT_SETTINGS)),
    )
):
    @classmethod
    def _validate(cls, kwargs):
        try:
            # Setting content validation
            assert kwargs['swagger_versions'] and all(item in SUPPORTED_SWAGGER_VERSIONS for item in kwargs['swagger_versions']), \
                'ValueError: {setting.settings_key} items should be in {expected_values}. Current value {value.__class__}({value})'.format(
                    setting=_DEFAULT_SETTINGS['swagger_versions'],
                    expected_values=SUPPORTED_SWAGGER_VERSIONS,
                    value=kwargs['swagger_versions'],
            )

            assert not kwargs['exclude_paths'] or all(_is_valid_regex(item) for item in kwargs['exclude_paths']), \
                'ValueError: {setting.settings_key} items should be valid regular expressions.'.format(
                    setting=_DEFAULT_SETTINGS['exclude_paths'],
            )
        except AssertionError as e:
            raise InvalidPyramidSwaggerSettings(e)

    @classmethod
    def normalize(cls, settings):
        """
        Normalize pyramid settings injecting default values
        :param settings: pyramid settings
        :type settings: dict
        :return: PyramidSwaggerSettings instance
        :rtype: PyramidSwaggerSettings
        """
        # Filter out all the settings not defined by pyramid_swagger and apply default values
        pyramid_swagger_settings = dict(
            (
                setting.python_attr,
                _load_setting(setting, settings[setting.settings_key]) if setting.settings_key in settings else setting.default_value,
            )
            for setting in itervalues(_DEFAULT_SETTINGS)
        )

        cls._validate(pyramid_swagger_settings)

        # Convert settings to set
        for python_attr in {'swagger_versions', 'exclude_paths', 'exclude_routes', 'prefer_20_routes'}:
            pyramid_swagger_settings[python_attr] = set(pyramid_swagger_settings[python_attr])

        return cls(**pyramid_swagger_settings)

    @cached_property
    def exclude_paths_regexes(self):
        return {re.compile(regex) for regex in self.exclude_paths}
