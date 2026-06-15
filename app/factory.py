from flask import Flask
from .extensions import configure_extensions

def create_app():
    """The absolute master app factory, isolated from the initialization layer."""
    app = Flask(__name__)
    
    configure_extensions(app)
    
    from .routes.main_routes import main
    app.register_blueprint(main)
    
    return app
