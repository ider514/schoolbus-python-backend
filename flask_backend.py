from flask import Flask, jsonify, json, request, render_template, abort, Blueprint
from flask_cors import CORS
from pymongo import MongoClient
import requests
from datetime import datetime
from jinja2 import TemplateNotFound

sample_page = Blueprint('sample_page', 'sample_page', template_folder='templates')

cluster = MongoClient('mongodb+srv://Ider:PrisonBreak@cluster0-m5dyv.mongodb.net/test?retryWrites=true&w=majority')
db_users = cluster['Schoolbus']['users']
db_location = cluster['Schoolbus']['location']
db_schools = cluster['Schoolbus']['schools']

app = Flask(__name__)
app.register_blueprint(sample_page, url_prefix='/')

CORS(app, resources={r'/*': {'origins': '*'}})


@app.route('/')
def get_sample():
    try:
        return render_template('index.html')
    except TemplateNotFound:
	print ('template not found')
        abort(404)

# ___Dashboard backend___

@app.route('/', methods=['GET'])
def test():
    return 'HELLO WORLD'

@app.route('/dash_schools/<email>/<password>', methods=['GET', 'POST'])
def dash_schools(email, password):
    if request.method == 'GET':
        data = []
        bus = db_schools.find()
        for x in bus:
            data.append(x)
        return jsonify(data)
    if request.method == 'POST':
        new_school = {
            '_id': email,
            'username': email,
            'password': password,
            'routes': [],
            'buses': [],
            'verification': 12345678
        }
        db_schools.insert_one(new_school)
        return 'success'

@app.route('/dash_buses/<id>', methods=['GET', 'POST'])
def dash_buses(id):
    if request.method == 'GET':
        if id == 'all':
            data = []
            bus = db_location.find()
            for x in bus:
                data.append(x)
            return jsonify(data)
        else:
            query = {'username': id}
            found_school = db_schools.find_one(query)
            buses = found_school['buses']
            return_data = []
            bus_list = []
            for x in buses:
                bus_list.append(x['bus'])
            for x in bus_list:
                found_buses = db_location.find_one({'_id': x})
                return_data.append(found_buses)
            return jsonify(return_data)
    if request.method == 'POST':
        data = request.get_json()

@app.route('/dash_routes/<id>', methods=['GET', 'POST'])
def dash_routes(id):
    if request.method == 'GET':
        if id == 'all':
            data = []
            bus = db_location.find()
            for x in bus:
                data.append(x)
            return jsonify(data)
        else:
            query = {'username': id}
            found_school = db_schools.find_one(query)
            routes = found_school['routes']
            return_data = []
            number = 1
            counter = 1
            for x in range(len(routes)):
                for y in range(len(routes[x]['stops'])):
                    data = {'name': routes[x]['name'],
                            'stop': routes[x]['stops'][y]['name'],
                            'lat': routes[x]['stops'][y]['lat'],
                            'lon': routes[x]['stops'][y]['lon'],
                            'length': len(routes[x]['stops'][y])}
                    counter += 1
                    if counter == len(routes[x]['stops'])+1:
                        number += 1
                        counter = 0
                    return_data.append(data)
            return jsonify(return_data)
    if request.method == 'POST':
        data = request.get_json()
        new_route = []
        # print (len(data['route']))
        for x in range(len(data['route'])):
            new_route.append({
                'name': data['route'][x]['name'],
                'lat': data['route'][x]['lat'],
                'lon': data['route'][x]['lon'],
                'here': 'false',
                'eta': 0,
                'usual_eta': 0
            })
        new_data = {
            'name': data['route_name'],
            'id': 0,
            'stops': new_route,
        }
        found_school = db_schools.find_one({'username': data['username']})
        found_school['routes'].append(new_data)
        db_schools.update_one({'username': data['username']}, {"$set": found_school})
        print ('route added')
        return 'success'

@app.route('/dash_users/<id>', methods=['GET','POST'])
def dash_users(id):
    if request.method == 'GET':
        if id == 'all':
            data = []
            bus = db_location.find()
            for x in bus:
                data.append(x)
            return jsonify(data)
        else:
            query = {'school': id}
            found_users = db_users.find(query,{'_id': False })
            return_data = []
            for x in found_users:
                return_data.append(x)
            return jsonify(return_data)
    if request.method == 'POST':
        data = request.get_json()
        new_user = {
            'username': data['user']['username'],
            'password': data['user']['password'],
            'school': data['username'],
            'log': [],
        }
        db_users.insert_one(new_user)
        return 'success'

@app.route('/dash_login/<email>/<password>', methods=['GET'])
def dash_login(email, password):
    document = {'username': email}
    user = db_schools.find_one(document)
    if email == 'admin' and user['password'] == password:
        print ('admin')
        return jsonify('admin')
    elif user is None :
        print (email)
        return jsonify('error')
    elif user['password'] == password:
        print (email)
        return jsonify('success')



# ___Mobile backend___

def get_list(dict):
    return list(dict.keys())

@app.route('/login/<email>/<password>', methods=['GET'])
def login(email, password):
    print (email, password)
    document = {'username': email}
    user = db_users.find_one(document)
    if user is None:
        print ('Username not found')
        return 'Username not found'
    if user['password'] == password:
        print ('success')
        return 'success' + user['school']
    else:
        print ('Wrong password')

        return 'Wrong password'

@app.route('/verify', methods=['POST'])
def verify():
    school = request.args.get('school')
    print (school)
    id = request.args.get('id')
    print (id)
    email = request.args.get('email')
    print (email)

    document = {'username': school}
    found_school = db_schools.find_one(document)
    if found_school['verification'] == int(id):
        # Record log
        user_query = {'username': email}
        user = db_users.find_one(user_query)

        # Out (second time)
        if user['log'][-1][-8:] == str(id):
            log = ('O ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + id)
            print (user['log'][-1][0])
            if user['log'][-1][0] == 'O':
                print ('logged twice')
                return 'logged twice'
        # In (first time)
        else :
            log = ('I ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + id)
        # Update log
        user['log'].append(log)
        db_users.update_one({'username': email}, {"$set": user})

        print ('logged')
        return 'logged'
    if found_school['verification'] != int(id):
        print ('wrong id')
        return 'wrong id'

@app.route('/log/<email>', methods=['GET'])
def log(email):
    document = {'username': email}
    found_user = db_users.find_one(document)
    log_list = found_user['log']
    log_list.pop(0)
    return jsonify(log_list)


@app.route('/buses/<school>', methods=['GET'])
def buses(school):
    found_school = db_schools.find_one({"username": school})
    bus_numbers = found_school['buses']
    print(bus_numbers)
    return_buses = []
    for x in bus_numbers:
        return_buses.append(db_location.find_one({'_id': x}))

    return jsonify(return_buses)


@app.route('/busStops/<school>/<busnumber>', methods=['GET'])
def bus_stops(school, busnumber):
    my_school_query = {"username": school}
    found_bus = db_schools.find_one(my_school_query)['routes']
    return_data = []
    for x in range(len(found_bus)):
        for y in range(len(found_bus[x]['stops'])):
            return_data.append(found_bus[x]['stops'][y])
    return jsonify(stop_names)

@app.route('/insert', methods=['get'])
def insert():
    db_schools.insert_one({"_id": "erdenet", 'buses':[{"52":[{'lat':1, 'lon': 1}, {'lat': 1, 'lon':1}]}, {"59":[{'lat':1, 'lon': 1}, {'lat': 1, 'lon':1}]}]})
    return 'done'


if __name__ == '__main__':
    app.run(host='0.0.0.0')