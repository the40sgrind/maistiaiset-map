import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# 1. Point to your service account key JSON file
cred = credentials.Certificate("firebase_key.json")

# 2. Initialize the Firebase app
firebase_admin.initialize_app(cred)

# 3. Get a reference to Firestore
db = firestore.client()

# 4. Create a test event document
event_data = {
    "product_name": "Test Yogurt Tasting",
    "brand_id": "test_brand_123",
    "store_name": "Test Prisma Helsinki",
    "address": "Helsinki, Finland",
    "latitude": 60.1699,
    "longitude": 24.9384,
    "start_time": datetime(2025, 3, 1, 12, 0),
    "end_time": datetime(2025, 3, 1, 15, 0),
    "description": "This is a test event created from Python.",
    "approved": True,
    "created_at": datetime.utcnow()
}

# 5. Add document to 'events' collection
doc_ref = db.collection("events").add(event_data)

print("Event created with ID:", doc_ref[1].id)
