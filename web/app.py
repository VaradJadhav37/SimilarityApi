from flask import Flask,request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy
app=Flask(__name__)
api=Api(app)
client=MongoClient("mongodb://localhost:27017/")
db=client.SimilarityDB
users=db["users"]
def verifyPw(username, password):
    user = users.find_one({"username": username})
    if not user:
        return False
    hashedpwd = user["password"]
    return bcrypt.checkpw(password.encode('utf-8'), hashedpwd)

def countTokens(username):
    user = users.find_one({"username": username})
    return user["tokens"] if user else 0

class Register(Resource):
    def post(self):
        data = request.get_json()
        username = data['username']
        password = data['password']
        if users.find_one({"username": username}):
            return {"message": "Username already exists"}, 400
        hashedpwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users.insert_one({"username": username, "password": hashedpwd, "sentences": "", "tokens": 6})
        return {"message": "User registered successfully"}, 201

# Detection of similarity between two sentences
class Detect(Resource):
    def post(self):
        data = request.get_json()
        username = data['username']
        password = data['password']
        text1 = data['text1']
        text2 = data['text2']
        if not verifyPw(username, password):
            return {"message": "Incorrect password"}, 401

        num_tokens = countTokens(username)
        if num_tokens < 1:
            return {"message": "Not enough tokens"}, 401
        nlp=spacy.load("en_core_web_sm")
        text1=nlp(text1)
        text2=nlp(text2)
        ratio=text1.similarity(text2)
        similarity=round(ratio*100,2)
        users.update_one(
            {"username": username},
            {"$set": {"tokens": num_tokens - 1}}
        )
        return {"similarity": similarity}, 200

class Refill(Resource):
    def post(self):
        data = request.get_json()
        username = data['username']
        password = data['password']
        refill_amount = data['refill_amount']
        if refill_amount < 0:
            return {"message": "Invalid refill amount"}, 400
        if not verifyPw(username, password):
            return {"message": "Incorrect password"}, 401
        current_tokens = countTokens(username)
        users.update_one(
            {"username": username},
            {"$set": {"tokens": current_tokens+refill_amount}}
        )
        return {"message": "Tokens refilled successfully"}, 200

api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)