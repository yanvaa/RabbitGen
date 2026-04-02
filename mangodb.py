from pymongo.mongo_client import MongoClient
from datetime import datetime
from typing import List, Dict, Optional
from bson import ObjectId
import random

class RabbitMongoDB:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="rabbit_world"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.rabbits = self.db.rabbits
        self.counter = self.db.counter
        
        if self.counter.find_one({"_id": "rabbit_id"}) is None:
            self.counter.insert_one({"_id": "rabbit_id", "seq": 0})
    
    def _get_next_sequence(self) -> int:
        result = self.counter.find_one_and_update(
            {"_id": "rabbit_id"},
            {"$inc": {"seq": 1}},
            return_document=True
        )
        return result["seq"]

    def create_rabbit(self, name: str, genom: list, parents: list = None) -> dict:
        rabbit_data = {
            "_id": ObjectId(),
            "rabbit_id": self._get_next_sequence(),
            "name": name,
            "genom": genom,
            "parents": parents or [],
            "birth_date": datetime.now(),
            "gender": random.choice(["male", "female"]),
            "hp": 100,
            "generation": self._calculate_generation(parents),
            "traits": self._generate_traits(genom)
        }
        
        result = self.rabbits.insert_one(rabbit_data)
        rabbit_data["_id"] = result.inserted_id
        return rabbit_data

    def _calculate_generation(self, parents: list) -> int:
        if not parents:
            return 1
        parents_data = self.rabbits.find({"rabbit_id": {"$in": parents}})
        return max(p["generation"] for p in parents_data) + 1

    def _generate_traits(self, genom: list) -> dict:
        return {
            "speed": genom[0] % 10,
            "fertility": genom[1] % 10,
            "intelligence": genom[2] % 10,
            "appearance": genom[3] % 10,
            "unique_hash": hash(tuple(genom)) % 1000000
        }

    def get_rabbit(self, identifier) -> Optional[dict]:
        query = {}
        if isinstance(identifier, int):
            query["rabbit_id"] = identifier
        elif isinstance(identifier, ObjectId):
            query["_id"] = identifier
        else:
            query["name"] = identifier
            
        return self.rabbits.find_one(query)

    def add_relationship(self, rabbit_id, relative_id, relation_type):
        self.rabbits.update_one(
            {"_id": rabbit_id},
            {"$addToSet": {f"relations.{relation_type}": relative_id}}
        )

    def get_unique_traits(self) -> dict:
        pipeline = [
            {"$group": {
                "_id": None,
                "unique_hashes": {"$addToSet": "$traits.unique_hash"},
                "total_unique": {"$sum": {"$size": ["$traits.unique_hash"]}}
            }}
        ]
        return list(self.rabbits.aggregate(pipeline))[0]