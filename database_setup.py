from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database_indexes(mongo_uri):
    """Setup database indexes for optimal performance"""
    try:
        client = MongoClient(mongo_uri)
        db = client.careorbit_db
        
        # Patient collection indexes
        db.patient.create_index([("contact_number", ASCENDING)])  # Removed unique constraint on contact_number to allow multiple patients with same phone
        db.patient.create_index([("patient_id", ASCENDING)], unique=True)
        db.patient.create_index([("name", ASCENDING)])
        db.patient.create_index([("created_at", DESCENDING)])
        db.patient.create_index([("aadhaar_number", ASCENDING)], sparse=True)
        
        db.patient.create_index([
            ("contact_number", ASCENDING), 
            ("name", ASCENDING), 
            ("aadhaar_number", ASCENDING)
        ], unique=True, sparse=True)  # Added compound unique index to prevent exact duplicates (same phone + name + aadhaar)
        
        # Visit collection indexes
        db.visit.create_index([("patient_id", ASCENDING)])
        db.visit.create_index([("doctor_id", ASCENDING)])
        db.visit.create_index([("department_id", ASCENDING)])
        db.visit.create_index([("visit_date_time", DESCENDING)])
        db.visit.create_index([("status", ASCENDING)])
        db.visit.create_index([("follow_up_date", ASCENDING)])
        db.visit.create_index([("doctor_id", ASCENDING), ("status", ASCENDING)])
        
        # Doctor collection indexes
        db.doctor.create_index([("username", ASCENDING)], unique=True)
        db.doctor.create_index([("department_id", ASCENDING)])
        db.doctor.create_index([("name", ASCENDING)])
        
        # Admin collection indexes
        db.admin.create_index([("username", ASCENDING)], unique=True)
        
        # Department collection indexes
        db.department.create_index([("department_name", ASCENDING)], unique=True)
        
        # Compound indexes for common queries
        db.visit.create_index([("doctor_id", ASCENDING), ("visit_date_time", DESCENDING)])
        db.visit.create_index([("patient_id", ASCENDING), ("visit_date_time", DESCENDING)])
        
        logger.info("Database indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {str(e)}")
        return False

def validate_database_integrity(mongo_uri):
    """Validate database integrity and relationships"""
    try:
        client = MongoClient(mongo_uri)
        db = client.careorbit_db
        
        issues = []
        
        # Check for orphaned visits (visits without valid patient/doctor/department)
        visits = db.visit.find()
        for visit in visits:
            if not db.patient.find_one({"_id": visit["patient_id"]}):
                issues.append(f"Visit {visit['_id']} has invalid patient_id")
            if not db.doctor.find_one({"_id": visit["doctor_id"]}):
                issues.append(f"Visit {visit['_id']} has invalid doctor_id")
            if not db.department.find_one({"_id": visit["department_id"]}):
                issues.append(f"Visit {visit['_id']} has invalid department_id")
        
        pipeline = [
            {"$group": {
                "_id": {
                    "contact_number": "$contact_number",
                    "name": "$name", 
                    "aadhaar_number": "$aadhaar_number"
                }, 
                "count": {"$sum": 1}
            }},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = list(db.patient.aggregate(pipeline))
        for dup in duplicates:
            issues.append(f"Exact duplicate patient: {dup['_id']}")
        
        if issues:
            logger.warning(f"Database integrity issues found: {issues}")
        else:
            logger.info("Database integrity check passed")
            
        return issues
        
    except Exception as e:
        logger.error(f"Error validating database integrity: {str(e)}")
        return [f"Integrity check failed: {str(e)}"]

def backup_database(mongo_uri, backup_path):
    """Create database backup"""
    try:
        import json
        import os
        from datetime import datetime
        
        client = MongoClient(mongo_uri)
        db = client.careorbit_db
        
        backup_dir = f"{backup_path}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        collections = ['patient', 'doctor', 'admin', 'department', 'visit']
        
        for collection_name in collections:
            collection = db[collection_name]
            documents = list(collection.find())
            
            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                for key, value in doc.items():
                    if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
                        doc[key] = str(value)
                    elif isinstance(value, datetime):
                        doc[key] = value.isoformat()
            
            with open(f"{backup_dir}/{collection_name}.json", 'w') as f:
                json.dump(documents, f, indent=2, default=str)
        
        logger.info(f"Database backup created at: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return None

def get_database_stats(mongo_uri):
    """Get comprehensive database statistics"""
    try:
        client = MongoClient(mongo_uri)
        db = client.careorbit_db
        
        stats = {
            'collections': {},
            'total_size': 0,
            'indexes': {}
        }
        
        collections = ['patient', 'doctor', 'admin', 'department', 'visit']
        
        for collection_name in collections:
            collection = db[collection_name]
            
            # Collection stats
            stats['collections'][collection_name] = {
                'count': collection.count_documents({}),
                'size': db.command("collStats", collection_name).get('size', 0),
                'avg_obj_size': db.command("collStats", collection_name).get('avgObjSize', 0)
            }
            
            # Index stats
            stats['indexes'][collection_name] = list(collection.list_indexes())
            
            stats['total_size'] += stats['collections'][collection_name]['size']
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return None

if __name__ == "__main__":
    # Setup database when run directly
    mongo_uri = "mongodb://localhost:27017/"
    setup_database_indexes(mongo_uri)
    validate_database_integrity(mongo_uri)
