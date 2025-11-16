# Імпорти
from pymongo import MongoClient
from datetime import datetime

# Параметри MongoDB
MONGO_URI = "mongodb://mongo:27017/"
DB_NAME = "webapp_db"
COLLECTION_NAME = "messages"

# Підключення до MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Тестове повідомлення
message_dict = {
    "username": "test_user",
    "message": "Hello MongoDB!",
    "date": datetime.now().isoformat()
}

# Вставка в колекцію
result = collection.insert_one(message_dict)
print("Inserted document ID:", result.inserted_id)

# Перевірка
for doc in collection.find():
    print(doc)