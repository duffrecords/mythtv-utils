#!/usr/bin/env python

from app.core import config, lambda_handler
from flask import Flask, request
import json
from lambda_local.context import Context
from lambda_local.main import call

app = Flask(__name__)

# arn_string = 'arn:aws:lambda:us-west-2:593206642875:function:tv-bot'

@app.route('/', methods=['GET', 'POST'])
def index():
    # context = Context(8, arn_string=arn_string, version_name='$LATEST')
    response = call(lambda_handler, request.json, Context(8))
    return (json.dumps(response), 200, {'Content-Type': 'application/json'})

if __name__ == ('__main__'):
    app.run()

