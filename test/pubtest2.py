#!/usr/bin/env python
#
# Copyright 2014 Virginia Polytechnic Institute and State University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ECE 4564
Message Publisher Example

An example of publishing messages to an exchange on the RabbitMQ message broker.

In this example, we create a chat room by publishing messages to
an exchange named 'chat_room'. This part of the example can only publish (send)
messages.
"""

__author__ = 'Thaddeus Czauski'

import pika
import json

screen_name = "<name goes here>"
chat_msg = "Hello Room!"

# Connect to the message broker
msg_broker = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost",
                              virtual_host="/",
                              credentials=pika.PlainCredentials("guest",
                                                                "guest",
                                                                True)))
# Setup the exchange
channel = msg_broker.channel()
channel.exchange_declare(exchange="pi_utilization",
                         type="fanout")

# Send the message
ex_msg = json.dumps({'cpu': 0.27777, 'net':{'lo':{'rx':0,'tx':5}, 'eth0':{'rx':0, 'tx': 4}}})
ex_msg2 = json.dumps({'cpu': 0.123, 'net':{'lo':{'rx':4000,'tx':2000}, 'eth0':{'rx':0, 'tx': 2}, 'wlan0':{'rx':500, 'tx':900}}})

channel.basic_publish(exchange="pi_utilization",
                      routing_key='foobar', # We're using a fanout, so this is ignored
                      body=ex_msg) # screen_name + ": " + chat_msg)

channel.basic_publish(exchange="pi_utilization",
                      routing_key='foobar', # We're using a fanout, so this is ignored
                      body= screen_name + ": " + chat_msg)

channel.basic_publish(exchange="pi_utilization",
                      routing_key='foobar', # We're using a fanout, so this is ignored
                      body=ex_msg2) # screen_name + ": " + chat_msg)

# Close the connection
msg_broker.close()

