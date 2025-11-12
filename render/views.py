import json

import requests
from django.core.paginator import Paginator
from django.shortcuts import render


# Create your views here.
def index(request):
	url = 'https://iottinaco.onrender.com/readings/all'
	try:
		response = requests.get(url)
		response.raise_for_status()
		data = response.json()
	except requests.RequestException as e:
		data = []
		print(f"Error fetching data: {e}")

	# Paginación: 10 registros por página
	paginator = Paginator(data, 10)
	page_number = request.GET.get("page")
	page_obj = paginator.get_page(page_number)

	return render(request, "render/index.html", {"page_obj": page_obj})

def readings_chart(request):
	url = "https://iottinaco.onrender.com/readings/all"
	try:
			response = requests.get(url)
			response.raise_for_status()
			data = response.json()
	except requests.exceptions.RequestException as e:
			data = []
			print(f"Error al obtener datos: {e}")

	# Serializar correctamente para JavaScript
	data_json = json.dumps(data)

	return render(request, "render/readings_chart.html", {"readings_json": data_json})
