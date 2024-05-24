import pymongo
from fastapi import FastAPI

app = FastAPI()
db = pymongo.MongoClient('mongodb+srv://vaibhav:Vaibhav%40143@cluster0.nm9w35r.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')['ids']

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get('/fetch')
async def fetchLogs():
    logs = list(db['logs'].find())
    for i in logs:
        del i['_id']
    return logs