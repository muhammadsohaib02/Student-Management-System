from flask import Flask
from routes import register_routes
from student_controller import StudentController
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '0000'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/uploads')  # Ensure upload folder exists

# Create an instance of StudentController
controller = StudentController()

# Register routes with the app and controller
register_routes(app, controller)

if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)