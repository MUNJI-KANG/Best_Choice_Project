from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, "common/index.html")

# def login(request):
#     return render(request, "login.html")

# def signup(request):
#     return render(request, "signup.html")

def reservation(request):
    return render(request, "reservation/reservation_list.html")