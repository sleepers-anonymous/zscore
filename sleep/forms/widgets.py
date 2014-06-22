#!/usr/bin/python
from django import forms
from django.utils.safestring import mark_safe

#from https://stackoverflow.com/questions/7852609/django-setting-class-of-ul-instead-of-input-with-checkboxselectmultiple-widg 
#with some alterations
class CheckboxSelectMultipleULAttrs(forms.CheckboxSelectMultiple):
    """
    Class to allow setting attributes on containing ul in a CheckboxSelectMultiple

    ulattrs is a dictionary like attrs
    """
    def __init__(self, ulattrs=None, attrs=None, choices=()):
        self.ulattrs = ulattrs
        super(CheckboxSelectMultipleULAttrs, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None, choices=()):
        html = super(CheckboxSelectMultipleULAttrs, self).render(name, value, attrs, choices)
        if not self.ulattrs: return html
        ulattributes = " ".join(i + "='" + self.ulattrs[i] + "'" for i in self.ulattrs)
        return mark_safe(html.replace('<ul', '<ul ' + ulattributes, 1))

