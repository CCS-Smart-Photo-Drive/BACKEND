from BACKEND.init_config import app
import BACKEND.general_routes
import BACKEND.event_manager_routes
import BACKEND.user_routes


if __name__ == '__main__':
    app.run(debug=True, port = 5000)