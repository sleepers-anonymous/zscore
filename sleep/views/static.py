#!/usr/bin/python
#This file is for all the static pages

from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def faq(request):
    return render(request, 'faq.html')

def privacy(request):
    return render(request, 'privacy.html')

