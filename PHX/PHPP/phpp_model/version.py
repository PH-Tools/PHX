# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Class for managing PHPP Version data."""


class PHPPVersion:
    """Manage the PHPP Version number and language information."""

    def __init__(self, _number_major: str, _number_minor: str, _language: str):
        self.number_major = self.clean_input(_number_major)
        self.number_minor = self.clean_input(_number_minor)
        self.language = self.clean_input(_language)

    def clean_input(self, _input):
        """Upper, strip, replace spaces."""
        return str(_input).upper().strip().replace(" ", "").replace(".", "_")

    def number(self) -> str:
        """Return the full version number (ie: "9.6", "10.4", etc..)"""
        return f"{self.number_major}.{self.number_minor}"
