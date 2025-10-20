import requests
from django.shortcuts import render


# Create your views here.
def index(request):
	return render(request, 'render/index.html', {})

def readings_list(request):
	url = 'https://iottinaco.onrender.com/readings/all'
	try:
		response = requests.get(url)
		response.raise_for_status()
		data = response.json()
	except requests.RequestException as e:
		data = []
		print(f"Error fetching data: {e}")

	return render(request, 'render/readings.html', {'readings': data})
