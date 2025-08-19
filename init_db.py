from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import logging
from database_setup import setup_database_indexes, validate_database_integrity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the CareOrbit database with sample data"""
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client.careorbit_db
        
        logger.info("Connected to MongoDB successfully")
        
        # Clear existing collections
        collections = ['admin', 'patient', 'doctor', 'department', 'visit']
        for collection in collections:
            db[collection].drop()
            logger.info(f"Cleared {collection} collection")

        # Initialize departments
        departments = [
            {'department_name': 'ENT', 'description': 'Ear, Nose & Throat', 'created_at': datetime.now()},
            {'department_name': 'Cardiology', 'description': 'Heart & Cardiovascular', 'created_at': datetime.now()},
            {'department_name': 'Dentist', 'description': 'Dental Care', 'created_at': datetime.now()},
            {'department_name': 'Dermatology', 'description': 'Skin Care', 'created_at': datetime.now()},
            {'department_name': 'General', 'description': 'General Medicine', 'created_at': datetime.now()},
            {'department_name': 'OPD', 'description': 'Outpatient Department', 'created_at': datetime.now()},
            {'department_name': 'Gynecology', 'description': 'Women\'s Health', 'created_at': datetime.now()},
            {'department_name': 'Pediatrics', 'description': 'Child Care', 'created_at': datetime.now()},
            {'department_name': 'Orthopedics', 'description': 'Bone & Joint Care', 'created_at': datetime.now()},
            {'department_name': 'Neurology', 'description': 'Brain & Nervous System', 'created_at': datetime.now()}
        ]

        dept_results = db.department.insert_many(departments)
        dept_ids = dept_results.inserted_ids
        logger.info(f"Created {len(departments)} departments")

        # Initialize admin users
        admins = [
            {
                'username': 'admin1',
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin',
                'contact_info': 'admin1@careorbit.com',
                'name': 'System Administrator',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'reception',
                'password_hash': generate_password_hash('reception123'),
                'role': 'admin',
                'contact_info': 'reception@careorbit.com',
                'name': 'Reception Desk',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            }
        ]

        db.admin.insert_many(admins)
        logger.info(f"Created {len(admins)} admin users")

        # Initialize doctors with enhanced data
        doctors = [
            {
                'username': 'dr_martin',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Laura Martin',
                'department_id': dept_ids[5],  # OPD
                'availability_status': 'on_leave',
                'available_days': ['Monday', 'Thursday'],
                'daily_appointments': 10,
                'room_no': 'R601',
                'specialization': 'Outpatient Specialist',
                'experience_years': 7,
                'qualification': 'MBBS',
                'contact_number': '+91-9876543215',
                'email': 'dr.martin@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_clark',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. James Clark',
                'department_id': dept_ids[6],  # Gynecology
                'availability_status': 'busy',
                'available_days': ['Tuesday', 'Friday'],
                'daily_appointments': 14,
                'room_no': 'R701',
                'specialization': 'Gynecologist',
                'experience_years': 9,
                'qualification': 'MBBS, MD (Gynecology)',
                'contact_number': '+91-9876543216',
                'email': 'dr.clark@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_lee',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Angela Lee',
                'department_id': dept_ids[7],  # Pediatrics
                'availability_status': 'available',
                'available_days': ['Monday', 'Wednesday', 'Saturday'],
                'daily_appointments': 20,
                'room_no': 'R801',
                'specialization': 'Pediatrician',
                'experience_years': 11,
                'qualification': 'MBBS, MD (Pediatrics)',
                'contact_number': '+91-9876543217',
                'email': 'dr.lee@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_khan',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Aamir Khan',
                'department_id': dept_ids[8],  # Orthopedics
                'availability_status': 'available',
                'available_days': ['Monday', 'Tuesday', 'Thursday'],
                'daily_appointments': 16,
                'room_no': 'R901',
                'specialization': 'Orthopedic Surgeon',
                'experience_years': 13,
                'qualification': 'MBBS, MS (Ortho)',
                'contact_number': '+91-9876543218',
                'email': 'dr.khan@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_taylor',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Rachel Taylor',
                'department_id': dept_ids[9],  # Neurology
                'availability_status': 'available',
                'available_days': ['Wednesday', 'Thursday', 'Friday'],
                'daily_appointments': 12,
                'room_no': 'R1001',
                'specialization': 'Neurologist',
                'experience_years': 14,
                'qualification': 'MBBS, DM (Neurology)',
                'contact_number': '+91-9876543219',
                'email': 'dr.taylor@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_smith',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. John Smith',
                'department_id': dept_ids[0],  # ENT
                'availability_status': 'available',
                'available_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'daily_appointments': 15,
                'room_no': 'R101',
                'specialization': 'ENT Specialist',
                'experience_years': 8,
                'qualification': 'MBBS, MS (ENT)',
                'contact_number': '+91-9876543210',
                'email': 'dr.smith@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_johnson',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Sarah Johnson',
                'department_id': dept_ids[1],  # Cardiology
                'availability_status': 'available',
                'available_days': ['Monday', 'Wednesday', 'Friday'],
                'daily_appointments': 12,
                'room_no': 'R201',
                'specialization': 'Cardiologist',
                'experience_years': 12,
                'qualification': 'MBBS, MD (Cardiology)',
                'contact_number': '+91-9876543211',
                'email': 'dr.johnson@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_brown',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Michael Brown',
                'department_id': dept_ids[2],  # Dentist
                'availability_status': 'available',
                'available_days': ['Tuesday', 'Thursday', 'Saturday'],
                'daily_appointments': 20,
                'room_no': 'R301',
                'specialization': 'Dental Surgeon',
                'experience_years': 6,
                'qualification': 'BDS, MDS',
                'contact_number': '+91-9876543212',
                'email': 'dr.brown@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_davis',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Emily Davis',
                'department_id': dept_ids[3],  # Dermatology
                'availability_status': 'available',
                'available_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'daily_appointments': 18,
                'room_no': 'R401',
                'specialization': 'Dermatologist',
                'experience_years': 10,
                'qualification': 'MBBS, MD (Dermatology)',
                'contact_number': '+91-9876543213',
                'email': 'dr.davis@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_wilson',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Robert Wilson',
                'department_id': dept_ids[4],  # General
                'availability_status': 'available',
                'available_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
                'daily_appointments': 25,
                'room_no': 'R501',
                'specialization': 'General Physician',
                'experience_years': 15,
                'qualification': 'MBBS, MD (General Medicine)',
                'contact_number': '+91-9876543214',
                'email': 'dr.wilson@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
                        {
                'username': 'dr_kapoor',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Ritu Kapoor',
                'department_id': dept_ids[0],  # ENT
                'availability_status': 'available',
                'available_days': ['Monday', 'Thursday'],
                'daily_appointments': 14,
                'room_no': 'R103',
                'specialization': 'Rhinologist',
                'experience_years': 11,
                'qualification': 'MBBS, MS (ENT)',
                'contact_number': '+91-9810011001',
                'email': 'dr.kapoor@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_verma',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Ashok Verma',
                'department_id': dept_ids[1],  # Cardiology
                'availability_status': 'busy',
                'available_days': ['Tuesday', 'Friday'],
                'daily_appointments': 12,
                'room_no': 'R203',
                'specialization': 'Heart Failure Specialist',
                'experience_years': 19,
                'qualification': 'MBBS, DM (Cardiology)',
                'contact_number': '+91-9810011002',
                'email': 'dr.verma@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_iyer',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Meenakshi Iyer',
                'department_id': dept_ids[2],  # Dentistry
                'availability_status': 'available',
                'available_days': ['Wednesday', 'Saturday'],
                'daily_appointments': 16,
                'room_no': 'R303',
                'specialization': 'Endodontist',
                'experience_years': 8,
                'qualification': 'BDS, MDS (Endodontics)',
                'contact_number': '+91-9810011003',
                'email': 'dr.iyer@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_reddy',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Anil Reddy',
                'department_id': dept_ids[3],  # Dermatology
                'availability_status': 'on_leave',
                'available_days': ['Friday'],
                'daily_appointments': 10,
                'room_no': 'R403',
                'specialization': 'Dermatopathologist',
                'experience_years': 13,
                'qualification': 'MBBS, MD (Dermatology)',
                'contact_number': '+91-9810011004',
                'email': 'dr.reddy@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_malhotra',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Suresh Malhotra',
                'department_id': dept_ids[4],  # General
                'availability_status': 'available',
                'available_days': ['Monday', 'Tuesday', 'Thursday'],
                'daily_appointments': 18,
                'room_no': 'R503',
                'specialization': 'General Practitioner',
                'experience_years': 25,
                'qualification': 'MBBS, MD',
                'contact_number': '+91-9810011005',
                'email': 'dr.malhotra@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_choudhary',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Anita Choudhary',
                'department_id': dept_ids[5],  # OPD
                'availability_status': 'available',
                'available_days': ['Tuesday', 'Friday'],
                'daily_appointments': 15,
                'room_no': 'R603',
                'specialization': 'OPD Consultant',
                'experience_years': 6,
                'qualification': 'MBBS',
                'contact_number': '+91-9810011006',
                'email': 'dr.choudhary@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_sharma',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Priya Sharma',
                'department_id': dept_ids[6],  # Gynecology
                'availability_status': 'available',
                'available_days': ['Wednesday', 'Saturday'],
                'daily_appointments': 20,
                'room_no': 'R703',
                'specialization': 'Fertility Specialist',
                'experience_years': 15,
                'qualification': 'MBBS, MD (Gynecology)',
                'contact_number': '+91-9810011007',
                'email': 'dr.sharma@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_mukherjee',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Raj Mukherjee',
                'department_id': dept_ids[7],  # Pediatrics
                'availability_status': 'busy',
                'available_days': ['Monday', 'Thursday'],
                'daily_appointments': 18,
                'room_no': 'R803',
                'specialization': 'Pediatric Pulmonologist',
                'experience_years': 10,
                'qualification': 'MBBS, MD (Pediatrics)',
                'contact_number': '+91-9810011008',
                'email': 'dr.mukherjee@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_jain',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Kavya Jain',
                'department_id': dept_ids[8],  # Orthopedics
                'availability_status': 'available',
                'available_days': ['Tuesday', 'Friday'],
                'daily_appointments': 12,
                'room_no': 'R903',
                'specialization': 'Spine Specialist',
                'experience_years': 9,
                'qualification': 'MBBS, MS (Ortho)',
                'contact_number': '+91-9810011009',
                'email': 'dr.jain@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_nair',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Vivek Nair',
                'department_id': dept_ids[9],  # Neurology
                'availability_status': 'available',
                'available_days': ['Thursday', 'Saturday'],
                'daily_appointments': 14,
                'room_no': 'R1003',
                'specialization': 'Stroke Specialist',
                'experience_years': 17,
                'qualification': 'MBBS, DM (Neurology)',
                'contact_number': '+91-9810011010',
                'email': 'dr.nair@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_roberts',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Hannah Roberts',
                'department_id': dept_ids[0],  # ENT
                'availability_status': 'available',
                'available_days': ['Tuesday', 'Thursday'],
                'daily_appointments': 10,
                'room_no': 'R102',
                'specialization': 'ENT Surgeon',
                'experience_years': 6,
                'qualification': 'MBBS, MS (ENT)',
                'contact_number': '+91-9876543220',
                'email': 'dr.roberts@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_walker',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Daniel Walker',
                'department_id': dept_ids[1],  # Cardiology
                'availability_status': 'busy',
                'available_days': ['Monday', 'Tuesday', 'Thursday'],
                'daily_appointments': 14,
                'room_no': 'R202',
                'specialization': 'Interventional Cardiologist',
                'experience_years': 17,
                'qualification': 'MBBS, DM (Cardiology)',
                'contact_number': '+91-9876543221',
                'email': 'dr.walker@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_yadav',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Neha Yadav',
                'department_id': dept_ids[2],  # Dentist
                'availability_status': 'available',
                'available_days': ['Wednesday', 'Friday'],
                'daily_appointments': 18,
                'room_no': 'R302',
                'specialization': 'Orthodontist',
                'experience_years': 9,
                'qualification': 'BDS, MDS (Orthodontics)',
                'contact_number': '+91-9876543222',
                'email': 'dr.yadav@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_patel',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Rohan Patel',
                'department_id': dept_ids[3],  # Dermatology
                'availability_status': 'on_leave',
                'available_days': ['Saturday'],
                'daily_appointments': 8,
                'room_no': 'R402',
                'specialization': 'Cosmetic Dermatologist',
                'experience_years': 7,
                'qualification': 'MBBS, MD (Dermatology)',
                'contact_number': '+91-9876543223',
                'email': 'dr.patel@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_thomas',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. William Thomas',
                'department_id': dept_ids[4],  # General
                'availability_status': 'available',
                'available_days': ['Monday', 'Wednesday', 'Friday'],
                'daily_appointments': 22,
                'room_no': 'R502',
                'specialization': 'Family Physician',
                'experience_years': 20,
                'qualification': 'MBBS, MD',
                'contact_number': '+91-9876543224',
                'email': 'dr.thomas@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_mehra',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Kavita Mehra',
                'department_id': dept_ids[5],  # OPD
                'availability_status': 'available',
                'available_days': ['Tuesday', 'Thursday', 'Saturday'],
                'daily_appointments': 12,
                'room_no': 'R602',
                'specialization': 'OPD Consultant',
                'experience_years': 5,
                'qualification': 'MBBS',
                'contact_number': '+91-9876543225',
                'email': 'dr.mehra@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_fernandez',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Maria Fernandez',
                'department_id': dept_ids[6],  # Gynecology
                'availability_status': 'available',
                'available_days': ['Monday', 'Tuesday', 'Friday'],
                'daily_appointments': 15,
                'room_no': 'R702',
                'specialization': 'Obstetrician & Gynecologist',
                'experience_years': 18,
                'qualification': 'MBBS, MD (Gynecology)',
                'contact_number': '+91-9876543226',
                'email': 'dr.fernandez@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_banerjee',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Arjun Banerjee',
                'department_id': dept_ids[7],  # Pediatrics
                'availability_status': 'busy',
                'available_days': ['Wednesday', 'Thursday'],
                'daily_appointments': 19,
                'room_no': 'R802',
                'specialization': 'Neonatologist',
                'experience_years': 12,
                'qualification': 'MBBS, MD (Pediatrics)',
                'contact_number': '+91-9876543227',
                'email': 'dr.banerjee@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_jones',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Richard Jones',
                'department_id': dept_ids[8],  # Orthopedics
                'availability_status': 'available',
                'available_days': ['Monday', 'Thursday', 'Saturday'],
                'daily_appointments': 15,
                'room_no': 'R902',
                'specialization': 'Joint Replacement Surgeon',
                'experience_years': 16,
                'qualification': 'MBBS, MS (Ortho)',
                'contact_number': '+91-9876543228',
                'email': 'dr.jones@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            },
            {
                'username': 'dr_singh',
                'password_hash': generate_password_hash('doctor123'),
                'name': 'Dr. Manish Singh',
                'department_id': dept_ids[9],  # Neurology
                'availability_status': 'available',
                'available_days': ['Tuesday', 'Friday'],
                'daily_appointments': 11,
                'room_no': 'R1002',
                'specialization': 'Neurosurgeon',
                'experience_years': 21,
                'qualification': 'MBBS, MCh (Neurosurgery)',
                'contact_number': '+91-9876543229',
                'email': 'dr.singh@careorbit.com',
                'created_at': datetime.now(),
                'last_login': None,
                'is_active': True
            }

        ]

        doctor_results = db.doctor.insert_many(doctors)
        doctor_ids = doctor_results.inserted_ids
        logger.info(f"Created {len(doctors)} doctors")

        # Create sample patients for testing
        sample_patients = [
            {
                'patient_id': 'P001',
                'name': 'John Doe',
                'contact_number': '9876543210',
                'aadhaar_number': '1234-5678-9012',
                'date_of_birth': datetime(1985, 5, 15),
                'gender': 'Male',
                'address': '123 Main Street, City, State - 123456',
                'allergies': 'None',
                'chronic_illness': 'None',
                'created_at': datetime.now() - timedelta(days=30),
                'updated_at': datetime.now() - timedelta(days=30)
            },
            {
                'patient_id': 'P002',
                'name': 'Jane Smith',
                'contact_number': '9876543211',
                'aadhaar_number': '2345-6789-0123',
                'date_of_birth': datetime(1990, 8, 22),
                'gender': 'Female',
                'address': '456 Oak Avenue, City, State - 123457',
                'allergies': 'Penicillin',
                'chronic_illness': 'Hypertension',
                'created_at': datetime.now() - timedelta(days=25),
                'updated_at': datetime.now() - timedelta(days=25)
            },
            {
                'patient_id': 'P003',
                'name': 'Robert Johnson',
                'contact_number': '9876543212',
                'aadhaar_number': '3456-7890-1234',
                'date_of_birth': datetime(1975, 12, 10),
                'gender': 'Male',
                'address': '789 Pine Road, City, State - 123458',
                'allergies': 'Dust',
                'chronic_illness': 'Diabetes',
                'created_at': datetime.now() - timedelta(days=20),
                'updated_at': datetime.now() - timedelta(days=20)
            }
        ]

        patient_results = db.patient.insert_many(sample_patients)
        patient_ids = patient_results.inserted_ids
        logger.info(f"Created {len(sample_patients)} sample patients")

        # Create sample visits
        sample_visits = [
            {
                'patient_id': patient_ids[0],
                'doctor_id': doctor_ids[0],
                'department_id': dept_ids[0],
                'visit_date_time': datetime.now() - timedelta(days=5),
                'reason_for_visit': 'Ear infection',
                'status': 'completed',
                'symptoms': 'Ear pain, hearing difficulty',
                'diagnosis': 'Acute Otitis Media',
                'medications': 'Amoxicillin 500mg - 1 tablet twice daily for 7 days',
                'instructions': 'Keep ear dry, complete the course of antibiotics',
                'follow_up_date': datetime.now() + timedelta(days=7),
                'prescription_timestamp': datetime.now() - timedelta(days=5),
                'created_at': datetime.now() - timedelta(days=5)
            },
            {
                'patient_id': patient_ids[1],
                'doctor_id': doctor_ids[1],
                'department_id': dept_ids[1],
                'visit_date_time': datetime.now() - timedelta(days=3),
                'reason_for_visit': 'Chest pain',
                'status': 'completed',
                'symptoms': 'Chest discomfort, shortness of breath',
                'diagnosis': 'Angina - Stable',
                'medications': 'Aspirin 75mg - 1 tablet daily\nAtenolol 25mg - 1 tablet daily',
                'instructions': 'Avoid strenuous activities, follow up in 2 weeks',
                'follow_up_date': datetime.now() + timedelta(days=14),
                'prescription_timestamp': datetime.now() - timedelta(days=3),
                'created_at': datetime.now() - timedelta(days=3)
            },
            {
                'patient_id': patient_ids[2],
                'doctor_id': doctor_ids[4],
                'department_id': dept_ids[4],
                'visit_date_time': datetime.now() - timedelta(days=1),
                'reason_for_visit': 'Diabetes follow-up',
                'status': 'assigned',
                'created_at': datetime.now() - timedelta(days=1)
            }
        ]

        db.visit.insert_many(sample_visits)
        logger.info(f"Created {len(sample_visits)} sample visits")

        # Setup database indexes for performance
        logger.info("Setting up database indexes...")
        setup_success = setup_database_indexes('mongodb://localhost:27017/')
        if setup_success:
            logger.info("Database indexes created successfully")
        else:
            logger.warning("Some indexes may not have been created")

        # Validate database integrity
        logger.info("Validating database integrity...")
        integrity_issues = validate_database_integrity('mongodb://localhost:27017/')
        if not integrity_issues:
            logger.info("Database integrity validation passed")
        else:
            logger.warning(f"Database integrity issues found: {integrity_issues}")

        logger.info("Database initialization completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    success = initialize_database()
    
    if success:
        print("\n" + "="*60)
        print("CareOrbit Database Initialized Successfully!")
        print("="*60)
        print("\nLogin Credentials:")
        print("\nAdmin Portal:")
        print("  Username: admin1, Password: admin123")
        print("  Username: reception, Password: reception123")
        print("\nDoctor Portal:")
        print("  Username: dr_smith, Password: doctor123 (ENT)")
        print("  Username: dr_johnson, Password: doctor123 (Cardiology)")
        print("  Username: dr_brown, Password: doctor123 (Dentist)")
        print("  Username: dr_davis, Password: doctor123 (Dermatology)")
        print("  Username: dr_wilson, Password: doctor123 (General)")
        print("\nSample Patients Created:")
        print("  Patient ID: P001, Phone: 9876543210 (John Doe)")
        print("  Patient ID: P002, Phone: 9876543211 (Jane Smith)")
        print("  Patient ID: P003, Phone: 9876543212 (Robert Johnson)")
        print("\nNext Steps:")
        print("1. Start the Flask application: python app.py")
        print("2. Access Admin Portal: http://localhost:5000/admin/login")
        print("3. Access Doctor Portal: http://localhost:5000/doctor/login")
        print("="*60)
    else:
        print("Database initialization failed. Please check the logs for details.")
