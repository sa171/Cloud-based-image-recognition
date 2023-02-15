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
        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName='request_queue')
        # if len(queue_list) == 0:
        #     sqs.create_queue(QueueName="request_queue")
        app.logger.info("Received SQS queue url:",queue.url)
        queueUrl = queue.url
        message = {
            'Id':str(uuid.uuid4()),
            'image':base64.b64encode(file.read())
        }
        response = sqs.send_message(
            QueueUrl= queueUrl,
            MessageBody=message
        )
        app.logger.info(response)
        app.logger.info("Image sent to SQS successfully.")
        # Receive logic - Check all messages from receive queue and delete the one that matches the ID
        '''
        queue = sqs.get_queue_by_name(QueueName="response_queue")
        response = sqs.receive_message(
            QueueUrl=queue.url,
            MaxNumberOfMessages=20,
            WaitTimeSeconds=20
        )
        '''
        return jsonify({'message':'Message sent successfully'}),200
    except Exception as exp:
        app.logger.error(exp)
        return jsonify({'message':"Some issue with the server"}),500
    
if __name__ == '__main__':
    app.run(threaded=True,host="127.0.0.1",port=5000,debug=True)