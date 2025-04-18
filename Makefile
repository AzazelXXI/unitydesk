run:
	cls
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem

run-local:
	cls
	uvicorn src.main:app --reload --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem