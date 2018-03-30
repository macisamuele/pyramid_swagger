# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest
from six import string_types

from pyramid_swagger.settings import _DEFAULT_SETTINGS
from pyramid_swagger.settings import InvalidPyramidSwaggerSettings
from pyramid_swagger.settings import PyramidSwaggerSettings
from pyramid_swagger.settings import SUPPORTED_SWAGGER_VERSIONS


_EXCEPTION_TEMPLATE = 'TypeError: {setting.settings_key} should be of type {expected_type}. Current value {value.__class__}({value})'


@pytest.mark.parametrize(
    'python_attr, setting_value, expected_setting_value',
    (
        ('schema_directory', '1', '1'),
        ('swagger_versions', ['2.0'], {'2.0'}),
        ('use_models', True, True),
    )
)
def test_setting_normalization_succeed(python_attr, setting_value, expected_setting_value):
    setting = _DEFAULT_SETTINGS[python_attr]
    pyramid_swagger_settings = PyramidSwaggerSettings.normalize({setting.settings_key: setting_value})
    assert getattr(pyramid_swagger_settings, python_attr) == expected_setting_value


@pytest.mark.parametrize(
    'python_attr, setting_value, expected_types',
    (
        ('schema_directory', 1, string_types),
        ('swagger_versions', 1, (list, string_types)),
        ('use_models', None, (bool, string_types)),
    )
)
def test_setting_normalization_fails_due_to_type_validation(python_attr, setting_value, expected_types):
    setting = _DEFAULT_SETTINGS[python_attr]
    with pytest.raises(InvalidPyramidSwaggerSettings) as excinfo:
        PyramidSwaggerSettings.normalize({setting.settings_key: setting_value})

    assert _EXCEPTION_TEMPLATE.format(
        setting=setting,
        expected_type=expected_types,
        value=setting_value,
    ) in str(excinfo)


@pytest.mark.parametrize(
    'setting_key, setting_value, exception_content',
    (
        [
            'pyramid_swagger.swagger_versions', ['1'],
            'ValueError: {setting.settings_key} items should be in {expected_values}.'.format(
                setting=_DEFAULT_SETTINGS['swagger_versions'],
                expected_values=SUPPORTED_SWAGGER_VERSIONS,
            ),
        ],
        [
            'pyramid_swagger.swagger_versions', [],
            'ValueError: {setting.settings_key} items should be in {expected_values}.'.format(
                setting=_DEFAULT_SETTINGS['swagger_versions'],
                expected_values=SUPPORTED_SWAGGER_VERSIONS,
            ),
        ],
    )
)
def test_setting_normalization_fails_due_to_setting_content(setting_key, setting_value, exception_content):
    with pytest.raises(InvalidPyramidSwaggerSettings) as excinfo:
        PyramidSwaggerSettings.normalize({setting_key: setting_value})

    assert exception_content in str(excinfo)


def test_ensure_default_settings_are_valid():
    try:
        PyramidSwaggerSettings.normalize({})
    except:  # noqa E722 do not use bare except
        pytest.fail('Default settings are not valid')
