from flask import Flask, jsonify, request
import logging
import boto3
import base64

app = Flask(__name__)
logging.basicConfig(filename='flask.log', level=logging.DEBUG)

@app.route('/',methods=['GET'])
def index():
    response = {'message':"Welcome to flask controller!"}
    return jsonify(response),200

@app.route('/upload',methos=['POST'])
def upload():
    if 'image' not in request.json:
        return jsonify({'message': 'Bad Request'}), 400
    try:
        file = request.files['myfile']
        sqs = boto3.client('sqs')
        queue_list = sqs.list_queues(QueueNamePrefix='request_queue')
        if len(queue_list) == 0:
            queue = sqs.create_queue(QueueName="request_queue")
        queueUrl = sqs.get_queue_url(QueueName="request_queue")['QueueUrl']
        image_data = file.read()
        message = {
            'Id':"Id",
            'image':""
        }
        response = sqs.send_message(
            QueueUrl= queueUrl,
            MessageBody=image_data
        )
        app.logger.info("Image sent to SQS successfully.")
# Do we need to decouple response logic from request logic?
        queue_list = sqs.list_queues(QueueNamePrefix="response_queue")
        if len(queue_list) == 0:
            queue = sqs.create_queue(QueueName="response_queue")
        queueUrl = sqs.get_queue_url(QueueName="response_queue")['QueueUrl']
        response = sqs.receive_message(
            QueueUrl=queueUrl,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20
        )
        


    except Exception as exp:
        app.logger.error(exp)
        return jsonify({'message':"Some issue with the server"}),500
    
