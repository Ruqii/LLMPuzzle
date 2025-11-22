import uvicorn
import webbrowser
import threading
import time

def open_browser():
    # Wait a bit to ensure the server starts first
    time.sleep(1)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # Launch browser in a separate thread so it doesn't block the server
    threading.Thread(target=open_browser).start()

    # Start FastAPI server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
