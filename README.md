# ECE 4564, HW 2

Python Raspberry Pi CPU and network load monitoring and statistics apps
using RabbitMQ. A client/server to publish and subscribe to utilization
metrics.


### Files in submission
pistatsview.py  A client application to subscribe to the RabbitMQ exchange
                and print out calculated statistics.

pistatsd.py     A server that parses system information and /proc and 
                publishes it to the RabbitMQ 'pi_utilization' exchange.


### Dependencies
The following python modules must be present:
- json
- pika

This application is currently only compatible with python2.

### Usage
To run the client, do:
python2 pistatsview.py -b <broker> -c <user:pass> -p <vhost> -k <key>

If the '-c' flag is not specified, the guest account will be used.
If the '-p' flag is not specified, the root virtualhost will be used.
