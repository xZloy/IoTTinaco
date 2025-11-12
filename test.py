import psycopg2

try:
	conn = psycopg2.connect(
		host="dpg-d47epn3ipnbc73cqmfgg-a.oregon-postgres.render.com",
		database="tinaco_db",
		user="tinaco_user",
		password="CzFd5fydRKkABkmnpldBoyTIYdYDK84N"
	)
	print("Conexion exitosa a PostgreSQL")

	# Crea un cursor para ejecutar consultas
	cur = conn.cursor()
	cur.execute("SELECT version();")
	version = cur.fetchone()[0]
	print("Version de PostgreSQL:", version)
except Exception as e:
	print("Error al conectar:", e)
finally:
	if conn:
		conn.close()
