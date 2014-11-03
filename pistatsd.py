import json
import argparse
import pika
import pika.exceptions
import signal
import sys
import time
import subprocess

# Global variable that controls running the app
publish_stats = True


def stop_stats_service(signal, frame):
    global publish_stats
    """
    A signal handler, that will cause the main execution loop to stop

    :param signal: (int) A number if a intercepted signal caused this handler
                   to be run, otherwise None
    :param frame: A Stack Frame object, if an intercepted signal caused this
                  handler to be run
    :return: None
    """
    publish_stats = False

def read_cpu_utilization():
    """
    Returns a dictionary with the total uptime and idle time for the system

    :return: (dict) The system 'uptime' and 'idle' time stored in keys using
                    their respective names
    """
    with open('/proc/uptime') as uptime:
        upt = [float(x) for x in uptime.readline().split()]
        cores = int(subprocess.check_output(["nproc"]))
        print cores
        upt[1] /= cores
        return upt


def read_net_throughput():
    """
    Returns a dictionary with the number of bytes each installed network
    interface has transmitted (tx) and received (rx)

    :return: (dict) A dictionary of network interfaces, where each network
             interface contains dictionaries with the transmitted and received
             bytes for the respective interface
    """
    with open("/proc/net/dev") as net_info:
        return {key: value for (key, value) in 
                [(interface[0][:-1], {'rx': int(interface[1]), 'tx': int(interface[9])}) for interface in 
                    [line.split() for line in net_info.readlines()[2:]]]}

# Application Entry Point
# ^^^^^^^^^^^^^^^^^^^^^^^

# Guard try clause to catch any errors that aren't expected
try:

    # The message broker host name or IP address
    host = None
    # The virtual host to connect to
    vhost = "/" # Defaults to the root virtual host
    # The credentials to use
    credentials = None
    # The topic to subscribe to
    topic = None

    # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is
    # sent to this app
    # For more info about signals, see: https://scholar.vt.edu/portal/site/0a8757e9-4944-4e33-9007-40096ecada02/page/e9189bdb-af39-4cb4-af04-6d263949f5e2?toolstate-701b9d26-5d9a-4273-9019-dbb635311309=%2FdiscussionForum%2Fmessage%2FdfViewMessageDirect%3FforumId%3D94930%26topicId%3D3507269%26messageId%3D2009512
    signal_num = signal.SIGINT
    try:
        signal.signal(signal_num, stop_stats_service)
        signal_num = signal.SIGTERM
        signal.signal(signal_num, stop_stats_service)

    except ValueError, ve:
        print "Warning: Greceful shutdown may not be possible: Unsupported " \
              "Signal: " + signal_num


    # TODO: Parse the command line arguments
    parser = argparse.ArgumentParser(description='Read JSON utilization stats from \
    a RabbitMQ message broker and print them in human-readable form.')

    parser.add_argument('-b', dest='broker', nargs=1, required=True, help='RabbitMQ\
    message broker')

    parser.add_argument('-p', dest='virtualhost', nargs=1, required=False,
                        default=['/'], help='Virtual host to connect to')
    parser.add_argument('-c', dest='credentials', nargs=1, required=False,
                        default=['guest:guest'], help='user:password')
    parser.add_argument('-k', dest='key', nargs=1, required=True,
                        help='Routing key')

    args = parser.parse_args()

    def args_to_pikaargs(args):
        # Make sure the credentials are formatted correctly
        if ":" not in args.credentials[0]:
            print('Credentials are not formatted correctly. Exiting.')
            sys.exit(1)

        cred_list = args.credentials[0].split(':')
        credentials = pika.PlainCredentials(cred_list[0], cred_list[1])
        broker = args.broker[0]
        vhost = args.virtualhost[0]

        pika_params = pika.ConnectionParameters(broker, 5672, vhost, credentials)

        return pika_params


    # Ensure that the user specified the required arguments

    message_broker = None
    channel = None
    try:
        # DONE: Connect to the message broker using the given broker address (host)
        # Use the virtual host (vhost) and credential information (credentials),
        # if provided
        connection = pika.BlockingConnection(args_to_pikaargs(args))

        # DONE: Setup the channel and exchange
        channel = connection.channel()
        channel.exchange_declare(exchange='pi_utilization', type='direct')

        # Create a data structure to hold the stats read from the previous
        # sampling time
        last_stat_sample = {"cpu": None, "net": None}

        # Set the initial values for the last stat data structure
        last_stat_sample["cpu"] = read_cpu_utilization()
        last_stat_sample["net"] = read_net_throughput()

        # Sleep for one second
        last_sample_time = time.time()
        time.sleep(1.0)

        # Loop until the application is asked to quit
        while(publish_stats):
            # Read cpu and net stats
            current_stat_sample = {"cpu": None, "net": None}
            current_stat_sample["cpu"] = read_cpu_utilization()
            current_stat_sample["net"] = read_net_throughput()

            current_sample_time = time.time()

            # Calculate time from last sample taken
            sample_period = current_sample_time - last_sample_time

            # Setup the JSON message to send
            utilization_msg = {"cpu": None, "net": dict()}

            # Calculate CPU utilization during the sleep_time
            utilization_msg["cpu"] = max([0.0, 1 - ((current_stat_sample['cpu'][1] - last_stat_sample['cpu'][1])/(current_stat_sample['cpu'][0] - last_stat_sample['cpu'][0]))])

            # Calculate the throughout for each installed network interface
            # -------------------------------------------------------------
            # General Note: sample_period is the amount of time between samples, and
            # is in seconds. Therefore sample_period can be used to calculate the
            # throughput in bytes/second
            for iface in current_stat_sample["net"].keys():
                utilization_msg["net"][iface] = {"rx": (current_stat_sample['net'][iface]['rx'] - last_stat_sample['net'][iface]['rx'])/(sample_period),
                                                 "tx": (current_stat_sample['net'][iface]['tx'] - last_stat_sample['net'][iface]['tx'])/(sample_period)
                                                }

            # TODO: Publish the message (utilization_msg) in JSON format to the
            #       broker under the user specified topic.
            print utilization_msg
            channel.basic_publish(exchange="pi_utilization", routing_key=args.key[0], body=json.dumps(utilization_msg))

            # Save the current stats as the last stats
            last_stat_sample = current_stat_sample
            last_sample_time = current_sample_time

            # Sleep and then loop
            time.sleep(1.0)


    except pika.exceptions.AMQPError, ae:
        print "Error: An AMQP Error occured: " + ae.message

    except pika.exceptions.ChannelError, ce:
        print "Error: A channel error occured: " + ce.message

    except Exception, eee:
        print "Error: An unexpected exception occured: " + eee.message

    finally:
        # For closing the channel gracefully see: http://pika.readthedocs.org/en/0.9.14/modules/channel.html#pika.channel.Channel.close
        if channel is not None:
            channel.close()
        # For closing the connection gracefully see: http://pika.readthedocs.org/en/0.9.14/modules/connection.html#pika.connection.Connection.close
        if message_broker is not None:
            message_broker.close()

except Exception, ee:
    print(ee.message)
    sys.exit()

