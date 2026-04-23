import utils.clients
import utils.http_session
import utils.transport
import utils.session
from app.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=75)
