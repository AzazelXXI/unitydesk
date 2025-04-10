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