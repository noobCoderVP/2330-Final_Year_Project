import pymongo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
db = pymongo.MongoClient('mongodb+srv://vaibhav:Vaibhav%40143@cluster0.nm9w35r.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')['ids']

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get('/fetch')
async def fetchLogs():
    logs = list(db['logs'].find())
    for i in logs:
        del i['_id']
    return logs