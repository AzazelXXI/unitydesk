run: # run the project locally with uvicorn and reload on changes without ssl
	clear
	uvicorn src.main:app --reload --log-level debug --port 8000

clean-windows: # clean up the project with python cache, mypy cache, and pycache files and its folders
	cls
	powershell -Command "Get-ChildItem -Path . -Directory -Filter '*cache*' -Recurse | Remove-Item -Recurse -Force"
