from app.main import create_app
from app import blueprint

app = create_app()
app.register_blueprint(blueprint)
app.app_context().push()

if __name__ == '__main__':
    app.run(port=5000)
