from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse

@api_view(['GET'])
def hello_world(request):
    return Response({"message": "Welcome to 024Global connect"})
def root_view(request):
    return JsonResponse({'message': 'Welcome to the Django API backend!'})
