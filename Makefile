run: # run the project with uvicorn and reload on changes with ssl
	cls
	uvicorn src.main:app --reload --log-level debug --host 0.0.0.0 --port 8000 --ssl-keyfile .cert/key.pem --ssl-certfile .cert/cert.pem

run-local: # run the project locally with uvicorn and reload on changes without ssl
	cls
	uvicorn src.main:app --reload --port 8000

clean-windows: # clean up the project with python cache, mypy cache, and pycache files and its folders
	cls
	powershell -Command "Get-ChildItem -Path . -Directory -Filter '*cache*' -Recurse | Remove-Item -Recurse -Force"
