from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import re
import random
from .models import *
import time
import requests


# Create your views here.


@csrf_exempt
def index(request):
	if request.method=='POST':
		data = request.body

		
		# Extract the image content from the boundary
		boundary = b'------WebKitFormBoundary7MA4YWxkTrZu0gW'
		parts = data.split(boundary)

		image_data = None
		text_data = None

		for part in parts:
			if b'Content-Disposition: form-data; name="file"; filename="image.jpeg"' in part:
        		# Extract the image binary data, after Content-Type header
				image_data = part.split(b'\r\n\r\n')[1:]  # Skip headers and get image content
			if b'Content-Disposition: form-data; name="text"' in part:
				text_data = part.split(b'\r\n\r\n')[1:]

			
		if image_data:
			name = str(random.randint(10000000000, 99999999999999))

			f = b'\r\n\r\n'.join(image_data)
			photo = ContentFile(f, name=f"{name}.jpeg")


			if text_data:
				text_content = b'\r\n\r\n'.join(text_data).decode('utf-8')  # Join and decode text
				print(text_content)
				Shoot.objects.create(photo = photo, text = text_content)
			else:
				Shoot.objects.create(photo = photo)
		print('posted')
		pass
	return HttpResponse(status=200)

def viewer(request):
	if not request.user.is_superuser:
		return HttpResponse(status = 404)
	snaps = Shoot.objects.all().order_by('-id')[0:100]
	context = {'snaps' : snaps}
	return render(request, 'base/viewer.html', context)

def pinger(request):
	while True:
		resp = requests.get('https://www.dosojincargos.online')
		time.sleep(random.randint(300, 600))
	
