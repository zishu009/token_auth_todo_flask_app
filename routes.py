from flask import request
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import db, User, Task
from schemas import UserSchema, TaskSchema
from flask_bcrypt import Bcrypt
from marshmallow import ValidationError

api = Api()
bcrypt = Bcrypt()

user_schema = UserSchema()
task_schema = TaskSchema()
task_list_schema = TaskSchema(many=True)

class UserRegistration(Resource):
    def post(self):
        json_data = request.get_json()
        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            return {'errors': err.messages}, 400

        if User.query.filter_by(username=data['username']).first():
            return {'message': 'Username already exists'}, 400

        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return {
            'message': 'User created successfully',
            'user': user_schema.dump(new_user)
        }, 201

class UserLogin(Resource):
    def post(self):
        json_data = request.get_json()
        try:
            data = user_schema.load(json_data, partial=True)
        except ValidationError as err:
            return {'errors': err.messages}, 400

        user = User.query.filter_by(username=data.get('username')).first()

        if user and bcrypt.check_password_hash(user.password, data.get('password')):
            access_token = create_access_token(identity=str(user.id))
            return {'token': access_token}, 200

        return {'message': 'Invalid credentials'}, 401

class AddTask(Resource):
    @jwt_required()
    def post(self):
        current_user_id = int(get_jwt_identity())
        json_data = request.get_json()
        try:
            data = task_schema.load(json_data)
        except ValidationError as err:
            return {'errors': err.messages}, 400

        task = Task(
            title=data['title'],
            description=data.get('description'),
            user_id=current_user_id
        )
        db.session.add(task)
        db.session.commit()

        return {
            'message': 'Task added successfully',
            'task': task_schema.dump(task)
        }, 201

class GetAllTasks(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        tasks = Task.query.filter_by(user_id=current_user_id).all()
        return task_list_schema.dump(tasks), 200

class UpdateTask(Resource):
    @jwt_required()
    def put(self, task_id):
        current_user_id = int(get_jwt_identity())
        task = Task.query.get(task_id)

        if not task:
            return {'message': 'Task not found'}, 404
        if task.user_id != current_user_id:
            return {'message': 'Unauthorized'}, 403

        json_data = request.get_json()
        try:
            data = task_schema.load(json_data, partial=True)
        except ValidationError as err:
            return {'errors': err.messages}, 400

        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        db.session.commit()

        return {'message': 'Task updated successfully'}, 200

class DeleteTask(Resource):
    @jwt_required()
    def delete(self, task_id):
        current_user_id = int(get_jwt_identity())
        task = Task.query.get(task_id)

        if not task:
            return {'message': 'Task not found'}, 404
        if task.user_id != current_user_id:
            return {'message': 'Unauthorized'}, 403

        db.session.delete(task)
        db.session.commit()

        return {'message': 'Task deleted successfully'}, 200

# Register routes
api.add_resource(UserRegistration, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(AddTask, '/add-task')
api.add_resource(GetAllTasks, '/get-tasks')
api.add_resource(UpdateTask, '/update-task/<int:task_id>')
api.add_resource(DeleteTask, '/delete-task/<int:task_id>')
