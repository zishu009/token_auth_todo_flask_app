from flask_restful import Api, Resource
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import db, User, Task
from flask_bcrypt import Bcrypt

api = Api()  # Flask-RESTful API object (app is attached later in app.py)
bcrypt = Bcrypt()  # This will be initialized with the app in app.py

class UserRegistration(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'message': 'Missing username or password'}, 400
        
        if User.query.filter_by(username=username).first():
            return {'message': 'Username already exists'}, 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return {
            'message': 'User created successfully',
            'user': {'id': new_user.id, 'username': new_user.username}
        }, 201

class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=str(user.id))
            return {'token': access_token}, 200

        return {'message': 'Invalid credentials'}, 401

class AddTask(Resource):
    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')

        if not title:
            return {'message': 'Title is required'}, 400

        task = Task(title=title, description=description, user_id=current_user_id)
        db.session.add(task)
        db.session.commit()

        return {
            'message': 'Task added successfully',
            'task': {'id': task.id, 'title': task.title, 'description': task.description}
        }, 201

class GetAllTasks(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        tasks = Task.query.filter_by(user_id=current_user_id).all()
        return jsonify([task.to_dict() for task in tasks])

class UpdateTask(Resource):
    @jwt_required()
    def put(self, task_id):
        current_user_id = get_jwt_identity()
        task = Task.query.get(task_id)

        if not task or task.user_id != current_user_id:
            return {'message': 'Task not found or unauthorized'}, 404

        data = request.get_json()
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        db.session.commit()
        return {'message': 'Task updated successfully'}

class DeleteTask(Resource):
    @jwt_required()
    def delete(self, task_id):
        current_user_id = get_jwt_identity()
        task = Task.query.get(task_id)

        if not task or task.user_id != current_user_id:
            return {'message': 'Task not found or unauthorized'}, 404

        db.session.delete(task)
        db.session.commit()
        return {'message': 'Task deleted successfully'}

# Registering all resources (routes) to the API
api.add_resource(UserRegistration, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(AddTask, '/add-task')
api.add_resource(GetAllTasks, '/get-tasks')
api.add_resource(UpdateTask, '/update-task/<int:task_id>')
api.add_resource(DeleteTask, '/delete-task/<int:task_id>')
