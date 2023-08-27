# Importing required modules from FastAPI and AWS SDK
from fastapi import FastAPI, HTTPException, Depends
import boto3
from botocore.exceptions import ClientError
# from boto3.dynamodb.table import Table  # Unused import, commented out
from typing import Any

# Defining a type hint for DynamoDB table objects. 'Any' means it can be any type.
DynamoDBTable = Any

# Initializing a FastAPI app instance
app = FastAPI()

# This function initializes a connection to a DynamoDB table.
# It returns the table object which can be used for CRUD operations.
def get_dynamodb_table():
    try:
        # Creating a DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
        
        # Connecting to the 'todos' table
        table = dynamodb.Table('todos')
        return table
    except ClientError as e:
        # Handling exceptions and raising an HTTP 500 error with details.
        raise HTTPException(status_code=500, detail=f"DynamoDB Initialization Error: {e.response['Error']['Message']}")

# Root endpoint returning a simple response
@app.get("/", tags=['root'])
async def root() -> dict:
    return {"Ping": "Pong"}

# Endpoint to list all users. It retrieves all items from the DynamoDB table.
@app.get("/users/")
def list_users(table: DynamoDBTable = Depends(get_dynamodb_table)):
    try:
        response = table.scan()
        items = response.get('Items')
        if not items:
            return {"status": "success", "message": "No users found"}
        return items
    except ClientError as e:
        raise HTTPException(status_code=500, detail=e.response['Error']['Message'])

# Endpoint to create a new user. It inserts a new item into the DynamoDB table.
@app.post("/user/")
def create_user(id: str, username: str, table: DynamoDBTable = Depends(get_dynamodb_table)):
    try:
        table.put_item(Item={'id': id, 'username': username})
        return {"status": "success", "message": "User added"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=e.response['Error']['Message'])

# Endpoint to retrieve a specific user by ID.
@app.get("/user/{id}")
def read_user(id: str, table: DynamoDBTable = Depends(get_dynamodb_table)):
    try:
        response = table.get_item(Key={'id': id})
        item = response.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail="User not found")
        return item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=e.response['Error']['Message'])

# Endpoint to update the username of a specific user by ID.
@app.put("/user/{id}")
def update_user(id: str, username: str, table: DynamoDBTable = Depends(get_dynamodb_table)):
    try:
        table.update_item(
            Key={'id': id},
            UpdateExpression="set username = :u",
            ExpressionAttributeValues={':u': username}
        )
        return {"status": "success", "message": "User updated"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=e.response['Error']['Message'])

# Endpoint to delete a specific user by ID.
@app.delete("/user/{id}")
def delete_user(id: str, table: DynamoDBTable = Depends(get_dynamodb_table)):
    try:
        table.delete_item(Key={'id': id})
        return {"status": "success", "message": "User deleted"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=e.response['Error']['Message'])

# Custom Exception Handler for AWS SDK's ClientError.
# Returns a formatted error message for any ClientError exceptions.
@app.exception_handler(ClientError)
async def dynamodb_exception_handler(request, exc: ClientError):
    return {"error": f"DynamoDB Error: {exc.response['Error']['Message']}"}
