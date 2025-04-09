from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi import staticfiles
from manager import MeetingManager
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('cert.pem', keyfile='key.pem')


templates = Jinja2Templates(directory="templates")

meeting_manager = MeetingManager()

app = FastAPI()
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")

@app.websocket("/ws/{room_name}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, client_id: str):
    await meeting_manager.join(room_name, websocket)
    try:
        while True:
            # Receive signaling data from a client
            data = await websocket.receive_json()
            # Broadcast signaling data to other clients in the same room
            await meeting_manager.broadcast(room_name, data, websocket)
    except WebSocketDisconnect:
        meeting_manager.leave(room_name, websocket)

@app.get("/room/{roomName}")
def get_video(request: Request, roomName:str):
    return templates.TemplateResponse(request=request, name="index.html")