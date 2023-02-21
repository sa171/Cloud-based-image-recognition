import json

from flask import Flask, jsonify, request
import logging
import boto3
import base64
import uuid

app = Flask(__name__)
logging.basicConfig(filename='flask.log', level=logging.DEBUG)

@app.route('/',methods=['GET'])
def index():
    response = {'message':"Welcome to flask controller!"}
    return jsonify(response),200

@app.route('/upload',methods=['POST'])
def upload():
    # if 'myfile' not in request.json:
    #     return jsonify({'message': 'Bad Request'}), 400
    try:
        file = request.files['myfile']
        sqsClient = boto3.client('sqs',region_name="us-east-1")
        # queue = sqsClient.get_queue_url(QueueName='request_queue')
        queueUrl = "https://sqs.us-east-1.amazonaws.com/874290406143/request_queue"
        response_queue_url = 'https://sqs.us-east-1.amazonaws.com/874290406143/response-queue'
        # if len(queue_list) == 0:
        #     sqs.create_queue(QueueName="request_queue")
        # app.logger.info("Received SQS queue url:",queue['QueueUrl'])
        # queueUrl = queue['QueueUrl']
        id = str(uuid.uuid4())
        message = {
            'id':id,
            'image':base64.b64encode(file.read()).decode("utf-8")
        }
        response = sqsClient.send_message(
            QueueUrl= queueUrl,
            MessageBody= json.dumps(message),
            WaitTimeSeconds=20
        )
        app.logger.info(response)
        app.logger.info("Image sent to SQS successfully.")
        input_bucket_name = 'input-bucket-1523'
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.put_object(
            Bucket=input_bucket_name,
            Key=id,
            Body=file
        )
        app.logger.info("Image sent to Input Bucket successfully.")
        while True:
            response = sqsClient.receive_message(
                QueueUrl=response_queue_url,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=20
            )
            if 'Messages' in response:
                for message in response['Messages']:
                    message_body = json.loads(message['Body'])
                    if message_body['id'] == id:
                        app.logger.info("Image Id matched, result is {}".format(message_body['results']))
                        sqsClient.delete_message(
                            QueueUrl=response_queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        return jsonify({'result': message_body['results']}), 200

        # Receive logic - Check all messages from receive queue and delete the one that matches the ID
        return jsonify({'message':'Classification result not available'}),200
    except Exception as exp:
        app.logger.error(exp)
        return jsonify({'message':"Some issue with the server"}),500
    
if __name__ == '__main__':
    app.run(threaded=True,host="0.0.0.0",port=5000,debug=True)