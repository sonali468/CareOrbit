from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, make_response
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from functools import wraps
import os
import logging
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config["MONGO_URI"] = "mongodb://localhost:27017/careorbit_db"

# Initialize PyMongo
mongo = PyMongo(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

class User(UserMixin):
    def __init__(self, user_id, username, role, name):
        self.id = user_id
        self.username = username
        self.role = role
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    # Try to find user in admin collection
    admin = mongo.db.admin.find_one({'_id': ObjectId(user_id)})
    if admin:
        return User(str(admin['_id']), admin['username'], 'admin', admin['name'])
    
    # Try to find user in doctor collection
    doctor = mongo.db.doctor.find_one({'_id': ObjectId(user_id)})
    if doctor:
        return User(str(doctor['_id']), doctor['username'], 'doctor', doctor['name'])
    
    return None

def role_required(roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/doctor/login')
def doctor_login():
    return render_template('doctor_login.html')

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/departments')
@role_required('admin')
def admin_departments():
    patient_id = request.args.get('patient_id')
    if not patient_id:
        return redirect(url_for('admin_dashboard'))
    
    patient = mongo.db.patient.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        return redirect(url_for('admin_dashboard'))
    
    # Calculate age
    today = datetime.now()
    age = today.year - patient['date_of_birth'].year
    if today.month < patient['date_of_birth'].month or \
       (today.month == patient['date_of_birth'].month and today.day < patient['date_of_birth'].day):
        age -= 1
    
    patient['age'] = age
    return render_template('departments.html', patient=patient)

@app.route('/admin/doctors')
@role_required('admin')
def admin_doctors():
    patient_id = request.args.get('patient_id')
    department_id = request.args.get('department_id')
    department_name = request.args.get('department_name')
    
    if not patient_id or not department_id:
        return redirect(url_for('admin_dashboard'))
    
    patient = mongo.db.patient.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        return redirect(url_for('admin_dashboard'))
    
    # Calculate age
    today = datetime.now()
    age = today.year - patient['date_of_birth'].year
    if today.month < patient['date_of_birth'].month or \
       (today.month == patient['date_of_birth'].month and today.day < patient['date_of_birth'].day):
        age -= 1
    
    patient['age'] = age
    return render_template('doctors.html', patient=patient, department_name=department_name)

@app.route('/admin/search-results')
@role_required(['admin'])
def admin_search_results():
    return render_template('search_results.html')

@app.route('/admin/patients')
@role_required('admin')
def admin_patients():
    return render_template('patient_management.html')

@app.route('/doctor/dashboard')
@role_required('doctor')
def doctor_dashboard():
    try:
        doctor_id = current_user.id
        
        doctor = mongo.db.doctor.find_one({'_id': ObjectId(doctor_id)})
        doctor_info = {
            'name': doctor.get('name', session.get('username', 'Unknown')),
            'department': 'Unknown Department'  # Default value
        } if doctor else None
        
        if doctor and 'department_id' in doctor:
            department = mongo.db.department.find_one({'_id': ObjectId(doctor['department_id'])})
            if department:
                doctor_info['department'] = department.get('department_name', 'Unknown Department')
        
        # Get today's assigned patients with patient details
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        print(f"Doctor {doctor_id} looking for visits between {start_of_day} and {end_of_day}")
        
        visits = list(mongo.db.visit.find({
            'doctor_id': ObjectId(doctor_id),
            'visit_date': {'$gte': start_of_day, '$lte': end_of_day}
        }).sort('visit_date', 1))
        
        print(f"Found {len(visits)} visits for doctor {doctor_id}")
        
        patients_data = []
        for visit in visits:
            patient = mongo.db.patient.find_one({'_id': visit['patient_id']})
            if patient:
                # Calculate age
                try:
                    today_date = datetime.now()
                    if isinstance(patient['date_of_birth'], datetime):
                        age = today_date.year - patient['date_of_birth'].year
                        if today_date.month < patient['date_of_birth'].month or \
                           (today_date.month == patient['date_of_birth'].month and today_date.day < patient['date_of_birth'].day):
                            age -= 1
                    else:
                        age = 0
                except:
                    age = 0
                
                visit_data = {
                    '_id': str(visit['_id']),
                    'patient_details': {
                        'patient_id': patient['patient_id'],
                        'name': patient['name'],
                        'contact_number': patient['contact_number'],
                        'gender': patient['gender'],
                        'address': patient['address'],
                        'age': age,  # Added age to patient_details
                        'allergies': patient.get('allergies', 'None'),
                        'chronic_conditions': patient.get('chronic_illness', 'None')  # Fixed field name
                    },
                    'reason_for_visit': visit.get('reason_for_visit', 'General consultation'),
                    'visit_date': visit['visit_date'],  # Fixed field name
                    'status': visit['status'],
                    'symptoms': visit.get('symptoms', ''),
                    'diagnosis': visit.get('diagnosis', ''),
                    'medications': visit.get('medications', ''),
                    'instructions': visit.get('instructions', ''),
                    'follow_up_date': visit.get('follow_up_date')
                }
                patients_data.append(visit_data)
        
        print(f"Returning {len(patients_data)} patients to template")
        return render_template('doctor_dashboard.html', patients=patients_data, doctor_info=doctor_info)
        
    except Exception as e:
        print(f"Doctor dashboard error: {str(e)}")
        return render_template('doctor_dashboard.html', patients=[], doctor_info=None)

@app.route('/api/doctor/search-patients', methods=['POST'])
@role_required('doctor')
def doctor_search_patients():
    try:
        data = request.get_json()
        search_term = data.get('search_term', '').strip()
        
        if not search_term:
            return jsonify({'success': False, 'message': 'Search term is required'})
        
        # Search patients by name, phone, or patient ID
        search_regex = re.compile(search_term, re.IGNORECASE)
        patients = list(mongo.db.patient.find({
            '$or': [
                {'name': search_regex},
                {'contact_number': search_regex},
                {'patient_id': search_regex}
            ]
        }))
        
        patients_data = []
        for patient in patients:
            # Get recent visit count and last visit date
            recent_visits = mongo.db.visit.count_documents({'patient_id': patient['_id']})
            last_visit = mongo.db.visit.find_one(
                {'patient_id': patient['_id']}, 
                sort=[('visit_date', -1)]
            )
            
            # Calculate age
            try:
                today_date = datetime.now()
                if isinstance(patient['date_of_birth'], datetime):
                    age = today_date.year - patient['date_of_birth'].year
                    if today_date.month < patient['date_of_birth'].month or \
                       (today_date.month == patient['date_of_birth'].month and today_date.day < patient['date_of_birth'].day):
                        age -= 1
                else:
                    age = 0
            except:
                age = 0
            
            patient_data = {
                'patient_id': patient['patient_id'],
                'name': patient['name'],
                'contact_number': patient['contact_number'],
                'gender': patient['gender'],
                'age': age,
                'allergies': patient.get('allergies', 'None'),
                'chronic_conditions': patient.get('chronic_illness', 'None'),
                'recent_visits': recent_visits,
                'last_visit': last_visit['visit_date'].strftime('%b %d, %Y') if last_visit else 'Never'
            }
            patients_data.append(patient_data)
        
        return jsonify({
            'success': True,
            'patients': patients_data
        })
        
    except Exception as e:
        print(f"Doctor patient search error: {str(e)}")
        return jsonify({'success': False, 'message': 'Search error occurred'})

@app.route('/api/admin/login', methods=['POST'])
def admin_login_api():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        admin = mongo.db.admin.find_one({'username': username})
        
        if admin and check_password_hash(admin['password_hash'], password):
            user = User(str(admin['_id']), admin['username'], 'admin', admin['name'])
            login_user(user)
            return jsonify({
                'success': True, 
                'message': 'Login successful',
                'redirect': '/admin/dashboard'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'Login error occurred'})

@app.route('/api/doctor/login', methods=['POST'])
def doctor_login_api():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        doctor = mongo.db.doctor.find_one({'username': username})
        
        if doctor and check_password_hash(doctor['password_hash'], password):
            user = User(str(doctor['_id']), doctor['username'], 'doctor', doctor['name'])
            login_user(user)
            return jsonify({
                'success': True, 
                'message': 'Login successful',
                'redirect': '/doctor/dashboard'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'Login error occurred'})

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/patient/search', methods=['POST'])
@role_required('admin')
def search_patient():
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        name = data.get('name', '').strip()
        
        query = {}
        if phone:
            query['contact_number'] = phone
        if name:
            query['name'] = {'$regex': name, '$options': 'i'}
            
        if not query:
            return jsonify({'success': False, 'message': 'Please provide search criteria'})
        
        print(f"Searching for patient with query: {query}")
        patient = mongo.db.patient.find_one(query)
        print(f"Patient found: {patient is not None}")
        
        if patient:
            try:
                today = datetime.now()
                if isinstance(patient['date_of_birth'], datetime):
                    age = today.year - patient['date_of_birth'].year
                    if today.month < patient['date_of_birth'].month or \
                       (today.month == patient['date_of_birth'].month and today.day < patient['date_of_birth'].day):
                        age -= 1
                else:
                    age = 0  # Default age if date_of_birth is not a datetime
            except Exception as age_error:
                print(f"Age calculation error: {age_error}")
                age = 0

            patient_data = {
                '_id': str(patient['_id']),
                'patient_id': patient['patient_id'],
                'name': patient['name'],
                'contact_number': patient['contact_number'],
                'age': age,
                'gender': patient['gender'],
                'address': patient['address'],
                'allergies': patient.get('allergies', ''),
                'chronic_illness': patient.get('chronic_illness', ''),
                'aadhaar_number': patient.get('aadhaar_number', ''),
                'date_of_birth': patient['date_of_birth']
            }

            try:
                visits = list(mongo.db.visit.find(
                    {'patient_id': patient['_id']}
                ))
                
                # Sort visits by visit_date if it exists, otherwise by _id
                visits.sort(key=lambda x: x.get('visit_date', x.get('_id')), reverse=True)

                visit_history = []
                for visit in visits:
                    try:
                        doctor = mongo.db.doctor.find_one({'_id': visit.get('doctor_id')})
                        department = mongo.db.department.find_one({'_id': visit.get('department_id')})

                        # Handle visit_date safely
                        visit_date = visit.get('visit_date')
                        if visit_date:
                            if isinstance(visit_date, datetime):
                                visit_date_str = visit_date.strftime('%Y-%m-%d %H:%M')
                            else:
                                visit_date_str = str(visit_date)
                        else:
                            visit_date_str = 'Date not available'

                        visit_data = {
                            'visit_id': str(visit['_id']),
                            'visit_date_time': visit_date_str,
                            'doctor_name': doctor['name'] if doctor else 'Unknown',
                            'department_name': department['department_name'] if department else 'Unknown',
                            'diagnosis': visit.get('diagnosis', ''),
                            'medications': visit.get('medications', ''),
                            'follow_up_date': visit['follow_up_date'].strftime('%Y-%m-%d') if visit.get('follow_up_date') else ''
                        }
                        visit_history.append(visit_data)
                    except Exception as visit_error:
                        print(f"Error processing visit: {visit_error}")
                        continue

            except Exception as visit_history_error:
                print(f"Error retrieving visit history: {visit_history_error}")
                visit_history = []

            patient_data['visits'] = visit_history

            return jsonify({'success': True, 'patient': patient_data})
        else:
            return jsonify({'success': False, 'message': 'Patient not found'})
            
    except Exception as e:
        print(f"Patient search error: {str(e)}")
        return jsonify({'success': False, 'message': f'Search error: {str(e)}'})

@app.route('/api/patient/register', methods=['POST'])
@role_required('admin')
def register_patient():
    try:
        data = request.get_json()
        
        # Generate patient ID
        last_patient = mongo.db.patient.find_one(sort=[('patient_id', -1)])
        if last_patient:
            last_id = int(last_patient['patient_id'][2:])  # Remove 'PT' prefix
            new_patient_id = f"PT{last_id + 1:04d}"
        else:
            new_patient_id = "PT0001"
        
        patient_data = {
            'patient_id': new_patient_id,
            'name': data['name'],
            'contact_number': data['phone'],  # Frontend sends 'phone'
            'aadhaar_number': data.get('aadhaar', ''),  # Frontend sends 'aadhaar'
            'date_of_birth': datetime.strptime(data['dob'], '%Y-%m-%d'),  # Frontend sends 'dob'
            'gender': data['gender'],
            'address': data['address'],
            'allergies': data.get('allergies', ''),
            'chronic_illness': data.get('chronic_illness', ''),
            'created_at': datetime.now()
        }
        
        result = mongo.db.patient.insert_one(patient_data)
        
        if result.inserted_id:
            # Calculate age for response
            today = datetime.now()
            age = today.year - patient_data['date_of_birth'].year
            if today.month < patient_data['date_of_birth'].month or \
               (today.month == patient_data['date_of_birth'].month and today.day < patient_data['date_of_birth'].day):
                age -= 1
            
            patient_data['_id'] = str(result.inserted_id)
            patient_data['age'] = age
            patient_data['visits'] = []  # New patient has no visits
            
            return jsonify({
                'success': True, 
                'message': 'Patient registered successfully',
                'patient': patient_data
            })
        else:
            return jsonify({'success': False, 'message': 'Registration failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Registration error: {str(e)}'})

@app.route('/api/patients/by-phone', methods=['POST'])
@role_required(['admin'])
def search_patients_by_phone():
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        if not phone:
            return jsonify({'success': False, 'message': 'Phone number is required'})
        
        # Find all patients with this phone number
        patients = list(mongo.db.patient.find({'contact_number': phone}))
        
        patients_data = []
        for patient in patients:
            # Calculate age
            try:
                today = datetime.now()
                if isinstance(patient['date_of_birth'], datetime):
                    age = today.year - patient['date_of_birth'].year
                    if today.month < patient['date_of_birth'].month or \
                       (today.month == patient['date_of_birth'].month and today.day < patient['date_of_birth'].day):
                        age -= 1
                else:
                    age = 0
            except:
                age = 0

            # Get visit history
            try:
                visits = list(mongo.db.visit.find({'patient_id': patient['_id']}))
                visits.sort(key=lambda x: x.get('visit_date', x.get('_id')), reverse=True)

                visit_history = []
                for visit in visits:
                    try:
                        doctor = mongo.db.doctor.find_one({'_id': visit.get('doctor_id')})
                        department = mongo.db.department.find_one({'_id': visit.get('department_id')})

                        visit_date = visit.get('visit_date')
                        if visit_date:
                            if isinstance(visit_date, datetime):
                                visit_date_str = visit_date.strftime('%Y-%m-%d %H:%M')
                            else:
                                visit_date_str = str(visit_date)
                        else:
                            visit_date_str = 'Date not available'

                        visit_data = {
                            'visit_id': str(visit['_id']),
                            'visit_date_time': visit_date_str,
                            'doctor_name': doctor['name'] if doctor else 'Unknown',
                            'department_name': department['department_name'] if department else 'Unknown',
                            'diagnosis': visit.get('diagnosis', ''),
                            'medications': visit.get('medications', ''),
                            'follow_up_date': visit['follow_up_date'].strftime('%Y-%m-%d') if visit.get('follow_up_date') else ''
                        }
                        visit_history.append(visit_data)
                    except Exception as visit_error:
                        continue
            except:
                visit_history = []

            patient_data = {
                '_id': str(patient['_id']),
                'patient_id': patient['patient_id'],
                'name': patient['name'],
                'contact_number': patient['contact_number'],
                'age': age,
                'gender': patient['gender'],
                'address': patient['address'],
                'allergies': patient.get('allergies', ''),
                'chronic_illness': patient.get('chronic_illness', ''),
                'aadhaar_number': patient.get('aadhaar_number', ''),
                'date_of_birth': patient['date_of_birth'],
                'visits': visit_history
            }
            patients_data.append(patient_data)
        
        return jsonify({'success': True, 'patients': patients_data})
        
    except Exception as e:
        print(f"Phone search error: {str(e)}")
        return jsonify({'success': False, 'message': f'Search error: {str(e)}'})

@app.route('/api/patients/by-name', methods=['POST'])
@role_required(['admin'])
def search_patients_by_name():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Name is required'})
        
        # Find patients with similar names
        patients = list(mongo.db.patient.find({'name': {'$regex': name, '$options': 'i'}}))
        
        patients_data = []
        for patient in patients:
            # Calculate age
            try:
                today = datetime.now()
                if isinstance(patient['date_of_birth'], datetime):
                    age = today.year - patient['date_of_birth'].year
                    if today.month < patient['date_of_birth'].month or \
                       (today.month == patient['date_of_birth'].month and today.day < patient['date_of_birth'].day):
                        age -= 1
                else:
                    age = 0
            except:
                age = 0

            # Get visit history
            try:
                visits = list(mongo.db.visit.find({'patient_id': patient['_id']}))
                visits.sort(key=lambda x: x.get('visit_date', x.get('_id')), reverse=True)

                visit_history = []
                for visit in visits:
                    try:
                        doctor = mongo.db.doctor.find_one({'_id': visit.get('doctor_id')})
                        department = mongo.db.department.find_one({'_id': visit.get('department_id')})

                        visit_date = visit.get('visit_date')
                        if visit_date:
                            if isinstance(visit_date, datetime):
                                visit_date_str = visit_date.strftime('%Y-%m-%d %H:%M')
                            else:
                                visit_date_str = str(visit_date)
                        else:
                            visit_date_str = 'Date not available'

                        visit_data = {
                            'visit_id': str(visit['_id']),
                            'visit_date_time': visit_date_str,
                            'doctor_name': doctor['name'] if doctor else 'Unknown',
                            'department_name': department['department_name'] if department else 'Unknown',
                            'diagnosis': visit.get('diagnosis', ''),
                            'medications': visit.get('medications', ''),
                            'follow_up_date': visit['follow_up_date'].strftime('%Y-%m-%d') if visit.get('follow_up_date') else ''
                        }
                        visit_history.append(visit_data)
                    except Exception as visit_error:
                        continue
            except:
                visit_history = []

            patient_data = {
                '_id': str(patient['_id']),
                'patient_id': patient['patient_id'],
                'name': patient['name'],
                'contact_number': patient['contact_number'],
                'age': age,
                'gender': patient['gender'],
                'address': patient['address'],
                'allergies': patient.get('allergies', ''),
                'chronic_illness': patient.get('chronic_illness', ''),
                'aadhaar_number': patient.get('aadhaar_number', ''),
                'date_of_birth': patient['date_of_birth'],
                'visits': visit_history
            }
            patients_data.append(patient_data)
        
        return jsonify({'success': True, 'patients': patients_data})
        
    except Exception as e:
        print(f"Name search error: {str(e)}")
        return jsonify({'success': False, 'message': f'Search error: {str(e)}'})

@app.route('/api/departments')
@role_required('admin')
def get_departments():
    try:
        departments = list(mongo.db.department.find({}, {'_id': 1, 'department_name': 1}))
        for dept in departments:
            dept['_id'] = str(dept['_id'])
        return jsonify(departments)
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error fetching departments'})

@app.route('/api/doctors/<department_id>')
@role_required('admin')
def get_doctors_by_department(department_id):
    try:
        doctors = list(mongo.db.doctor.find(
            {'department_id': ObjectId(department_id)},
            {'_id': 1, 'name': 1, 'specialization': 1, 'room_no': 1}
        ))
        
        # Calculate current load for each doctor
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        for doctor in doctors:
            doctor['_id'] = str(doctor['_id'])
            # Count today's visits for this doctor
            visit_count = mongo.db.visit.count_documents({
                'doctor_id': ObjectId(doctor['_id']),
                'visit_date': {'$gte': start_of_day, '$lte': end_of_day},
                'status': {'$in': ['assigned', 'in_progress']}
            })
            
            doctor['current_load'] = visit_count
            
            if visit_count <= 3:
                doctor['load'] = 'Light'
            elif visit_count <= 6:
                doctor['load'] = 'Medium'
            else:
                doctor['load'] = 'Heavy'
            
        return jsonify(doctors)
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error fetching doctors'})

@app.route('/api/assign-patient', methods=['POST'])
@role_required('admin')
def assign_patient():
    try:
        data = request.get_json()
        
        visit_data = {
            'patient_id': ObjectId(data['patient_id']),
            'doctor_id': ObjectId(data['doctor_id']),
            'department_id': ObjectId(data['department_id']),
            'reason_for_visit': data.get('reason_for_visit', 'General consultation'),
            'visit_date': datetime.now(),
            'status': 'assigned',
            'created_at': datetime.now()
        }
        
        result = mongo.db.visit.insert_one(visit_data)
        
        if result.inserted_id:
            return jsonify({
                'success': True, 
                'message': 'Patient assigned to doctor successfully',
                'visit_id': str(result.inserted_id)
            })
        else:
            return jsonify({'success': False, 'message': 'Assignment failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Assignment error: {str(e)}'})

@app.route('/api/visit/assign', methods=['POST'])
@role_required('admin')
def assign_visit():
    try:
        data = request.get_json()
        
        visit_data = {
            'patient_id': ObjectId(data['patient_id']),
            'doctor_id': ObjectId(data['doctor_id']),
            'department_id': ObjectId(data['department_id']),
            'reason_for_visit': data['reason_for_visit'],
            'visit_date': datetime.now(),
            'status': 'assigned',
            'created_at': datetime.now()
        }
        
        result = mongo.db.visit.insert_one(visit_data)
        
        if result.inserted_id:
            return jsonify({
                'success': True, 
                'message': 'Patient assigned to doctor successfully',
                'visit_id': str(result.inserted_id)
            })
        else:
            return jsonify({'success': False, 'message': 'Assignment failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'Assignment error occurred'})

@app.route('/api/doctor/patients')
@role_required('doctor')
def get_doctor_patients():
    try:
        doctor_id = current_user.id
        
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        visits = list(mongo.db.visit.find({
            'doctor_id': ObjectId(doctor_id),
            'visit_date': {'$gte': start_of_day, '$lte': end_of_day},
            'status': {'$in': ['assigned', 'in_progress']}
        }))
        
        patients = []
        for visit in visits:
            patient = mongo.db.patient.find_one({'_id': visit['patient_id']})
            if patient:
                # Calculate age
                try:
                    today_date = datetime.now()
                    if isinstance(patient['date_of_birth'], datetime):
                        age = today_date.year - patient['date_of_birth'].year
                        if today_date.month < patient['date_of_birth'].month or \
                           (today_date.month == patient['date_of_birth'].month and today_date.day < patient['date_of_birth'].day):
                            age -= 1
                    else:
                        age = 0
                except:
                    age = 0
                
                patients.append({
                    'visit_id': str(visit['_id']),
                    'patient_id': patient['patient_id'],
                    'name': patient['name'],
                    'age': age,
                    'gender': patient['gender'],
                    'reason_for_visit': visit['reason_for_visit'],
                    'status': visit['status'],
                    'visit_time': visit['visit_date'].strftime('%H:%M')
                })
        
        return jsonify({'success': True, 'patients': patients})
        
    except Exception as e:
        print(f"Get doctor patients error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching patients: {str(e)}'})

@app.route('/api/prescription/add', methods=['POST'])
@role_required('doctor')
def add_prescription():
    try:
        data = request.get_json()
        visit_id = data['visit_id']
        
        # Get visit details
        visit = mongo.db.visit.find_one({'_id': ObjectId(visit_id)})
        if not visit:
            return jsonify({'success': False, 'message': 'Visit not found'})
        
        prescription_data = {
            'symptoms': data['symptoms'],
            'diagnosis': data['diagnosis'],
            'medications': data['medications'],
            'instructions': data.get('instructions', ''),
            'follow_up_date': datetime.strptime(data['follow_up_date'], '%Y-%m-%d') if data.get('follow_up_date') else None,
            'prescription_timestamp': datetime.now(),
            'status': 'completed'
        }
        
        # Update visit with prescription data
        result = mongo.db.visit.update_one(
            {'_id': ObjectId(visit_id)},
            {'$set': prescription_data}
        )
        
        # Also create a separate prescription record for history
        prescription_record = {
            'visit_id': ObjectId(visit_id),
            'patient_id': visit['patient_id'],
            'doctor_id': visit['doctor_id'],
            'department_id': visit['department_id'],
            'visit_date': visit['visit_date'],
            'symptoms': data['symptoms'],
            'diagnosis': data['diagnosis'],
            'medications': data['medications'],
            'instructions': data.get('instructions', ''),
            'follow_up_date': datetime.strptime(data['follow_up_date'], '%Y-%m-%d') if data.get('follow_up_date') else None,
            'prescription_timestamp': datetime.now(),
            'created_at': datetime.now()
        }
        
        mongo.db.prescription.insert_one(prescription_record)
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Prescription added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add prescription'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding prescription: {str(e)}'})

@app.route('/api/patient/<patient_id>/history')
@role_required(['admin', 'doctor'])  # Allow both admin and doctor to access patient history
def get_patient_history(patient_id):
    try:
        visits = list(mongo.db.visit.find(
            {'patient_id': ObjectId(patient_id)},
            sort=[('visit_date', -1)]
        ))
        
        history = []
        for visit in visits:
            doctor = mongo.db.doctor.find_one({'_id': visit['doctor_id']})
            department = mongo.db.department.find_one({'_id': visit['department_id']})
            
            visit_data = {
                'visit_id': str(visit['_id']),
                'visit_date': visit['visit_date'].strftime('%Y-%m-%d %H:%M'),
                'doctor_name': doctor['name'] if doctor else 'Unknown',
                'department': department['name'] if department else 'Unknown',
                'reason_for_visit': visit['reason_for_visit'],
                'status': visit['status'],
                'symptoms': visit.get('symptoms', ''),
                'diagnosis': visit.get('diagnosis', ''),
                'medications': visit.get('medications', ''),
                'instructions': visit.get('instructions', ''),
                'follow_up_date': visit['follow_up_date'].strftime('%Y-%m-%d') if visit.get('follow_up_date') else ''
            }
            history.append(visit_data)
        
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error fetching patient history'})

@app.route('/api/prescription/<visit_id>')
@role_required('doctor')
def get_prescription(visit_id):
    try:
        visit = mongo.db.visit.find_one({'_id': ObjectId(visit_id)})
        if not visit:
            return jsonify({'success': False, 'message': 'Visit not found'})
        
        patient = mongo.db.patient.find_one({'_id': visit['patient_id']})
        doctor = mongo.db.doctor.find_one({'_id': visit['doctor_id']})
        
        prescription_data = {
            'visit_id': str(visit['_id']),
            'symptoms': visit.get('symptoms', ''),
            'diagnosis': visit.get('diagnosis', ''),
            'medications': visit.get('medications', ''),
            'instructions': visit.get('instructions', ''),
            'follow_up_date': visit['follow_up_date'].strftime('%Y-%m-%d') if visit.get('follow_up_date') else '',
            'patient': {
                'name': patient['name'],
                'patient_id': patient['patient_id'],
                'age': patient['age'],
                'gender': patient['gender'],
                'allergies': patient.get('allergies', 'None'),
                'chronic_conditions': patient.get('chronic_illness', 'None')
            },
            'doctor': {
                'name': doctor['name'],
                'department': doctor['department']
            },
            'visit_date': visit['visit_date'],
            'prescription_timestamp': visit.get('prescription_timestamp')
        }
        
        return jsonify({'success': True, 'prescription': prescription_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching prescription: {str(e)}'})

@app.route('/api/visit/<visit_id>/details')
@role_required(['admin', 'doctor'])
def get_visit_details(visit_id):
    try:
        # Get visit details
        visit = mongo.db.visit.find_one({'_id': ObjectId(visit_id)})
        if not visit:
            return jsonify({'success': False, 'message': 'Visit not found'})
        
        # Get patient, doctor, and department information
        patient = mongo.db.patient.find_one({'_id': visit['patient_id']})
        doctor = mongo.db.doctor.find_one({'_id': visit['doctor_id']})
        department = mongo.db.department.find_one({'_id': visit['department_id']})
        
        # Get prescription details from prescription collection
        prescription = mongo.db.prescription.find_one({'visit_id': ObjectId(visit_id)})
        
        visit_details = {
            'visit_id': str(visit['_id']),
            'visit_date': visit['visit_date'].strftime('%Y-%m-%d %H:%M') if visit.get('visit_date') else 'Date not available',
            'patient': {
                'name': patient['name'] if patient else 'Unknown',
                'patient_id': patient['patient_id'] if patient else 'Unknown',
                'age': patient.get('age', 0) if patient else 0,
                'gender': patient['gender'] if patient else 'Unknown',
                'contact_number': patient['contact_number'] if patient else 'Unknown'
            },
            'doctor': {
                'name': doctor['name'] if doctor else 'Unknown',
                'department': doctor['department'] if doctor else 'Unknown'
            },
            'department_name': department['department_name'] if department else 'Unknown',
            'reason_for_visit': visit.get('reason_for_visit', ''),
            'symptoms': visit.get('symptoms', prescription.get('symptoms', '') if prescription else ''),
            'diagnosis': visit.get('diagnosis', prescription.get('diagnosis', '') if prescription else ''),
            'medications': visit.get('medications', prescription.get('medications', '') if prescription else ''),
            'instructions': visit.get('instructions', prescription.get('instructions', '') if prescription else ''),
            'follow_up_date': visit['follow_up_date'].strftime('%Y-%m-%d') if visit.get('follow_up_date') else (prescription['follow_up_date'].strftime('%Y-%m-%d') if prescription and prescription.get('follow_up_date') else ''),
            'status': visit.get('status', 'pending'),
            'prescription_timestamp': visit.get('prescription_timestamp', prescription.get('prescription_timestamp') if prescription else None)
        }
        
        return jsonify({'success': True, 'visit_details': visit_details})
        
    except Exception as e:
        print(f"Error fetching visit details: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching visit details: {str(e)}'})

@app.route('/api/prescription/edit', methods=['POST'])
@role_required(['doctor'])
def edit_prescription():
    try:
        data = request.get_json()
        visit_id = data.get('visit_id')
        
        if not visit_id:
            return jsonify({'success': False, 'message': 'Visit ID is required'})
        
        # Get current visit data for audit trail
        current_visit = mongo.db.visit.find_one({'_id': ObjectId(visit_id)})
        if not current_visit:
            return jsonify({'success': False, 'message': 'Visit not found'})
        
        # Create audit trail entry
        audit_entry = {
            'visit_id': ObjectId(visit_id),
            'doctor_id': ObjectId(session['user_id']),
            'edited_at': datetime.now(),
            'original_data': {
                'symptoms': current_visit.get('symptoms', ''),
                'diagnosis': current_visit.get('diagnosis', ''),
                'medications': current_visit.get('medications', ''),
                'instructions': current_visit.get('instructions', ''),
                'follow_up_date': current_visit.get('follow_up_date')
            },
            'new_data': {
                'symptoms': data.get('symptoms', ''),
                'diagnosis': data.get('diagnosis', ''),
                'medications': data.get('medications', ''),
                'instructions': data.get('instructions', ''),
                'follow_up_date': datetime.strptime(data['follow_up_date'], '%Y-%m-%d') if data.get('follow_up_date') else None
            }
        }
        
        # Save audit trail
        mongo.db.prescription_audit.insert_one(audit_entry)
        
        # Update visit record
        update_data = {
            'symptoms': data.get('symptoms', ''),
            'diagnosis': data.get('diagnosis', ''),
            'medications': data.get('medications', ''),
            'instructions': data.get('instructions', ''),
            'last_modified': datetime.now(),
            'modified_by': ObjectId(session['user_id'])
        }
        
        if data.get('follow_up_date'):
            update_data['follow_up_date'] = datetime.strptime(data['follow_up_date'], '%Y-%m-%d')
        
        mongo.db.visit.update_one(
            {'_id': ObjectId(visit_id)},
            {'$set': update_data}
        )
        
        # Update prescription record if exists
        prescription_data = {
            'visit_id': ObjectId(visit_id),
            'patient_id': current_visit['patient_id'],
            'doctor_id': ObjectId(session['user_id']),
            'symptoms': data.get('symptoms', ''),
            'diagnosis': data.get('diagnosis', ''),
            'medications': data.get('medications', ''),
            'instructions': data.get('instructions', ''),
            'follow_up_date': datetime.strptime(data['follow_up_date'], '%Y-%m-%d') if data.get('follow_up_date') else None,
            'created_at': current_visit.get('created_at', datetime.now()),
            'last_modified': datetime.now(),
            'modified_by': ObjectId(session['user_id'])
        }
        
        mongo.db.prescription.update_one(
            {'visit_id': ObjectId(visit_id)},
            {'$set': prescription_data},
            upsert=True
        )
        
        return jsonify({'success': True, 'message': 'Prescription updated successfully'})
        
    except Exception as e:
        logging.error(f"Error editing prescription: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update prescription'})

@app.route('/api/prescription/<visit_id>/audit')
@role_required(['doctor', 'admin'])
def get_prescription_audit(visit_id):
    try:
        audit_entries = list(mongo.db.prescription_audit.find(
            {'visit_id': ObjectId(visit_id)},
            sort=[('edited_at', -1)]
        ))
        
        audit_history = []
        for entry in audit_entries:
            doctor = mongo.db.doctor.find_one({'_id': entry['doctor_id']})
            audit_history.append({
                'edited_at': entry['edited_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'doctor_name': doctor['name'] if doctor else 'Unknown',
                'original_data': entry['original_data'],
                'new_data': entry['new_data']
            })
        
        return jsonify({'success': True, 'audit_history': audit_history})
        
    except Exception as e:
        logging.error(f"Error fetching audit trail: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch audit trail'})

@app.route('/api/patient/update', methods=['POST'])
@role_required(['admin'])
def update_patient():
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({'success': False, 'message': 'Patient ID is required'})
        
        # Find patient by ObjectId
        patient = mongo.db.patient.find_one({'_id': ObjectId(patient_id)})
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'})
        
        # Prepare update data
        update_data = {
            'name': data.get('name'),
            'date_of_birth': datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d'),
            'gender': data.get('gender'),
            'contact_number': data.get('contact_number'),
            'address': data.get('address'),
            'allergies': data.get('allergies') or None,
            'chronic_illness': data.get('chronic_illness') or None,
            'aadhaar_number': data.get('aadhaar_number') or None,
            'updated_at': datetime.now(),
            'updated_by': session.get('user_id')
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Update patient
        result = mongo.db.patient.update_one(
            {'_id': ObjectId(patient_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Patient updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'No changes made'})
            
    except Exception as e:
        print(f"Patient update error: {str(e)}")
        return jsonify({'success': False, 'message': f'Update failed: {str(e)}'})

@app.route('/api/patients/stats')
@role_required(['admin'])
def get_patients_stats():
    try:
        # Total patients
        total_patients = mongo.db.patient.count_documents({})
        
        # Recent registrations (this month)
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        recent_registrations = mongo.db.patient.count_documents({
            'created_at': {'$gte': start_of_month}
        })
        
        # Patients with visits
        patients_with_visits = len(list(mongo.db.visit.distinct('patient_id')))
        
        # Age distribution
        pipeline = [
            {
                '$addFields': {
                    'age': {
                        '$floor': {
                            '$divide': [
                                {'$subtract': [datetime.now(), '$date_of_birth']},
                                365.25 * 24 * 60 * 60 * 1000
                            ]
                        }
                    }
                }
            },
            {
                '$bucket': {
                    'groupBy': '$age',
                    'boundaries': [0, 20, 40, 60, 80, 100],
                    'default': 'Unknown',
                    'output': {'count': {'$sum': 1}}
                }
            }
        ]
        
        age_distribution = list(mongo.db.patient.aggregate(pipeline))
        
        return jsonify({
            'total_patients': total_patients,
            'recent_registrations': recent_registrations,
            'patients_with_visits': patients_with_visits,
            'age_distribution': age_distribution
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/patients/list')
@role_required(['admin'])
def get_patients_list():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        gender = request.args.get('gender', '').strip()
        sort_by = request.args.get('sort', 'created_at')
        order = int(request.args.get('order', -1))
        
        # Build query
        query = {}
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'contact_number': {'$regex': search, '$options': 'i'}},
                {'patient_id': {'$regex': search, '$options': 'i'}}
            ]
        if gender:
            query['gender'] = gender
        
        # Get total count
        total = mongo.db.patient.count_documents(query)
        
        # Get patients with pagination
        skip = (page - 1) * per_page
        patients = list(mongo.db.patient.find(query)
                       .sort(sort_by, order)
                       .skip(skip)
                       .limit(per_page))
        
        patients_data = []
        for patient in patients:
            # Calculate age
            try:
                today = datetime.now()
                if isinstance(patient['date_of_birth'], datetime):
                    age = today.year - patient['date_of_birth'].year
                    if today.month < patient['date_of_birth'].month or \
                       (today.month == patient['date_of_birth'].month and today.day < patient['date_of_birth'].day):
                        age -= 1
                else:
                    age = 0
            except:
                age = 0
            
            # Get visit count
            visit_count = mongo.db.visit.count_documents({'patient_id': patient['_id']})
            
            last_visit = mongo.db.visit.find_one(
                {'patient_id': patient['_id']}, 
                sort=[('visit_date', -1)]
            )
            last_visit_date = None
            if last_visit and 'visit_date' in last_visit:
                last_visit_date = last_visit['visit_date'].strftime('%b %d, %Y')
            
            patient_data = {
                '_id': str(patient['_id']),
                'patient_id': patient['patient_id'],
                'name': patient['name'],
                'contact_number': patient['contact_number'],
                'age': age,
                'gender': patient['gender'],
                'address': patient['address'],
                'visit_count': visit_count,
                'last_visit_date': last_visit_date  # Added last visit date
            }
            patients_data.append(patient_data)
        
        return jsonify({
            'success': True,
            'patients': patients_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/patient/<patient_id>')
@role_required(['admin'])
def get_patient_details(patient_id):
    try:
        patient = mongo.db.patient.find_one({'_id': ObjectId(patient_id)})
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'})
        
        # Calculate age
        try:
            today = datetime.now()
            if isinstance(patient['date_of_birth'], datetime):
                age = today.year - patient['date_of_birth'].year
                if today.month < patient['date_of_birth'].month or \
                   (today.month == patient['date_of_birth'].month and today.day < patient['date_of_birth'].day):
                    age -= 1
            else:
                age = 0
        except:
            age = 0
        
        patient_data = {
            '_id': str(patient['_id']),
            'patient_id': patient['patient_id'],
            'name': patient['name'],
            'contact_number': patient['contact_number'],
            'age': age,
            'gender': patient['gender'],
            'address': patient['address'],
            'allergies': patient.get('allergies', ''),
            'chronic_illness': patient.get('chronic_illness', ''),
            'aadhaar_number': patient.get('aadhaar_number', ''),
            'date_of_birth': patient['date_of_birth'].strftime('%Y-%m-%d') if isinstance(patient['date_of_birth'], datetime) else str(patient['date_of_birth'])
        }

        try:
            visits = list(mongo.db.visit.find(
                {'patient_id': ObjectId(patient_id)},
                sort=[('visit_date', -1)]
            ))
            
            visit_history = []
            for visit in visits:
                try:
                    doctor = mongo.db.doctor.find_one({'_id': visit.get('doctor_id')})
                    department = mongo.db.department.find_one({'_id': visit.get('department_id')})

                    # Handle visit_date safely
                    visit_date = visit.get('visit_date')
                    if visit_date:
                        if isinstance(visit_date, datetime):
                            visit_date_str = visit_date.strftime('%Y-%m-%d %H:%M')
                        else:
                            visit_date_str = str(visit_date)
                    else:
                        visit_date_str = 'Date not available'

                    visit_data = {
                        'visit_id': str(visit['_id']),
                        'visit_date_time': visit_date_str,
                        'doctor_name': doctor['name'] if doctor else 'Unknown',
                        'department_name': department['department_name'] if department else 'Unknown',
                        'reason_for_visit': visit.get('reason_for_visit', ''),
                        'status': visit.get('status', ''),
                        'symptoms': visit.get('symptoms', ''),
                        'diagnosis': visit.get('diagnosis', ''),
                        'medications': visit.get('medications', ''),
                        'instructions': visit.get('instructions', ''),
                        'follow_up_date': visit['follow_up_date'].strftime('%Y-%m-%d') if visit.get('follow_up_date') else ''
                    }
                    visit_history.append(visit_data)
                except Exception as visit_error:
                    print(f"Error processing visit: {visit_error}")
                    continue

        except Exception as visit_history_error:
            print(f"Error retrieving visit history: {visit_history_error}")
            visit_history = []

        patient_data['visits'] = visit_history
        
        return jsonify({'success': True, 'patient': patient_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error fetching patient details'})

@app.route('/api/patient/<patient_id>/update', methods=['PUT'])
@role_required(['admin'])
def update_patient_details(patient_id):
    try:
        data = request.get_json()
        
        # Find patient
        patient = mongo.db.patient.find_one({'_id': ObjectId(patient_id)})
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'})
        
        # Prepare update data
        update_data = {
            'name': data.get('name'),
            'date_of_birth': datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d'),
            'gender': data.get('gender'),
            'contact_number': data.get('contact_number'),
            'address': data.get('address'),
            'allergies': data.get('allergies') or None,
            'chronic_illness': data.get('chronic_illness') or None,
            'aadhaar_number': data.get('aadhaar_number') or None,
            'updated_at': datetime.now()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Update patient
        result = mongo.db.patient.update_one(
            {'_id': ObjectId(patient_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Patient updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'No changes made'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/patient/<patient_id>/delete', methods=['DELETE'])
@role_required(['admin'])
def delete_patient(patient_id):
    try:
        # Check if patient has visits
        visit_count = mongo.db.visit.count_documents({'patient_id': ObjectId(patient_id)})
        if visit_count > 0:
            return jsonify({'success': False, 'message': 'Cannot delete patient with existing visits'})
        
        # Delete patient
        result = mongo.db.patient.delete_one({'_id': ObjectId(patient_id)})
        
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Patient deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Patient not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/patients/export')
@role_required(['admin'])
def export_patients():
    try:
        patients = list(mongo.db.patient.find({}))
        
        # Create CSV content
        csv_content = "Patient ID,Name,Phone,Gender,Age,Address,Allergies,Chronic Illness,Registration Date\n"
        
        for patient in patients:
            # Calculate age
            try:
                today = datetime.now()
                if isinstance(patient['date_of_birth'], datetime):
                    age = today.year - patient['date_of_birth'].year
                    if today.month < patient['date_of_birth'].month or \
                       (today.month == patient['date_of_birth'].month and today.day < patient['date_of_birth'].day):
                        age -= 1
                else:
                    age = 0
            except:
                age = 0
            
            csv_content += f"{patient['patient_id']},{patient['name']},{patient['contact_number']},{patient['gender']},{age},\"{patient['address']}\",\"{patient.get('allergies', '')}\",\"{patient.get('chronic_illness', '')}\",{patient.get('created_at', datetime.now()).strftime('%Y-%m-%d')}\n"
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=patients_export_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
