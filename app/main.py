import os
import time
import paramiko

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


app = FastAPI()


# Router Configuration
ROUTER_USERNAME = os.getenv("ROUTER_USERNAME", "admin")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD", "cisco")


# Request Model
class RouterRequest(BaseModel):
    ip: str = "192.168.79.134"
    command: str = "show ip interface brief"


# Frontend
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


@app.get("/")
def index():
    return FileResponse("app/static/index.html")


# SSH Router
@app.post("/ssh")
def ssh_router(request: RouterRequest):

    client = paramiko.SSHClient()

    client.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    try:

        print(f"Connecting to {request.ip}...")

        client.connect(
            hostname=request.ip,
            port=22,
            username=ROUTER_USERNAME,
            password=ROUTER_PASSWORD,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )

        print("SSH connected!")

        shell = client.invoke_shell()

        time.sleep(1)

        if shell.recv_ready():
            shell.recv(65535)

        shell.send(request.command + "\n")

        time.sleep(2)

        output = ""

        while shell.recv_ready():

            output += shell.recv(65535).decode(
                "utf-8",
                errors="ignore"
            )

            time.sleep(0.2)

        return {
            "success": True,
            "ip": request.ip,
            "command": request.command,
            "output": output,
        }

    except paramiko.AuthenticationException:

        raise HTTPException(
            status_code=401,
            detail="SSH authentication failed"
        )

    except paramiko.SSHException as e:

        raise HTTPException(
            status_code=500,
            detail=f"SSH error: {str(e)}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        client.close()

        print("SSH connection closed.")
