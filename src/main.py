from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from src.manager import MeetingManager
import ssl
import logging
from logging.handlers import RotatingFileHandler
import asyncio

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = "app.log"
log_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

app_logger = logging.getLogger("fastapi")
app_logger.setLevel(logging.INFO)
app_logger.addHandler(log_handler)

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('cert.pem', keyfile='key.pem')


templates = Jinja2Templates(directory="src/templates")

meeting_manager = MeetingManager()

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Log uncaught exceptions
@app.middleware("http")
async def log_exceptions(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        app_logger.exception("Unhandled exception occurred")
        raise e

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")

@app.websocket("/ws/{room_name}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, client_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "OFFER":
                print("Received SDP offer:", data["message"]["sdp"])
                
                # Tạo SDP answer (giả lập)
                answer = {
                    "type": "ANSWER",
                    "message": {
                        "type": "answer",
                        "sdp": "v=0\r\no=- 123456789 2 IN IP4 127.0.0.1\r\n..."
                    }
                }
                await websocket.send_json(answer)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: room_name={room_name}, client_id={client_id}")

@app.get("/room/{roomName}")
def get_video(request: Request, roomName:str):
    return templates.TemplateResponse(request=request, name="index.html")

# Gracefully handle asyncio.CancelledError
@app.on_event("shutdown")
async def shutdown_event():
    try:
        # Perform any cleanup tasks here
        app_logger.info("Application is shutting down...")
    except asyncio.CancelledError:
        app_logger.warning("Shutdown process was interrupted by CancelledError.")
        raise