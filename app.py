import json
from flask import Flask, jsonify, request
import logging
import boto3
import base64
import uuid
import os

app = Flask(__name__)
logging.basicConfig(filename='flask.log', level=logging.DEBUG)

@app.route('/',methods=['GET'])
def index():
    response = {'message':"Welcome to flask controller!"}
    return jsonify(response),200

@app.route('/upload',methods=['POST'])
def upload():
    try:
        # my_set = set()
        # my_map = dict()

        file = request.files['myfile']
        filename = file.filename.split('.')[0]
        id = str(uuid.uuid4())+','+filename
        image_name = './'+id+'_input_image.jpeg'

        # my_set.add(id)
        # my_map[id] = filename
        # print("Entry : {}".format(len(my_map)))

        with open(image_name, 'wb') as f:
            f.write(file.read())
            # print('{} image saved to file'.format(filename))
        
        sqsClient = boto3.client('sqs',region_name="us-east-1")
        queueUrl = "https://sqs.us-east-1.amazonaws.com/874290406143/request_queue"
        response_queue_url = 'https://sqs.us-east-1.amazonaws.com/874290406143/response-queue'

        input_bucket_name = 'input-bucket-1523'
        s3 = boto3.client('s3', region_name='us-east-1')

        with open(image_name, 'rb') as f:
            image_data = f.read()
            # print('{} image loaded'.format(filename))
        encoded_image = base64.b64encode(image_data).decode("utf-8")

        message = {
            'id':id,
            'image':encoded_image
        }
        response = sqsClient.send_message(
            QueueUrl= queueUrl,
            MessageBody= json.dumps(message),
        )
        app.logger.info(response)
        app.logger.info("Image sent to SQS successfully.")

        with open(image_name, 'rb') as file:
            s3.upload_fileobj(
                file,input_bucket_name,id
            )
        app.logger.info("Image {} sent to Input Bucket successfully.".format(filename))
        print("Image {} sent to Input Bucket successfully.".format(filename))
        os.remove(image_name)

        while True:
            response = sqsClient.receive_message(
                QueueUrl=response_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
                VisibilityTimeout=2
            )
            if 'Messages' in response:
                for message in response['Messages']:
                    message_body = json.loads(message['Body'])
                    # if id == message_body['id']:
                    app.logger.info("Image {} result is {}".format(message_body['id'], message_body['results']))

                    sqsClient.delete_message(
                        QueueUrl=response_queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    
                    print('Result for {} is {}'.format(message_body['id'].split(',')[1], message_body['results']))
                    return jsonify({'result': message_body['results'], 'id': message_body['id'].split(',')[1]}), 200
        return jsonify({'message':'Classification result not available'}),200

    # Receive logic - Check all messages from receive queue and delete the one that matches the ID
        return jsonify({'message':'Classification result not available'}),200
    except Exception as exp:
        app.logger.error("Error while processing")
        app.logger.error(exp)
        return jsonify({'message':"Some issue with the server"}),500
    
if __name__ == '__main__':
    app.run(threaded=True,host="0.0.0.0",port=5000,debug=True)