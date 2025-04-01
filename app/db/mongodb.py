from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB]

    def close(self):
        if self.client:
            self.client.close()

    def get_db(self):
        if self.db is None:
            self.connect()
        return self.db

mongodb = MongoDB() 