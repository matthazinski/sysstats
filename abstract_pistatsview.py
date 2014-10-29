"""
This file contains pseudo code which describes at a high level what should be
implemented for the stats client (i.e. pistatsview).

This is the basic algorithm you will want to follow, although there are other
ways to implement this pseudo code.
"""

import json
import pika
import pika.channel
import pika.exceptions
import signal
import sys

# Create a data structure for holding the maximum and minimum values
stats_history = { "cpu": {"max": 0.0, "min": float("inf"), "current": 0.0},
                  "net": dict()}

class StatsClientChannelHelper:
    """
    This helper class is used to manage a channel and invoke event handlers when
    signals are intercepted
    """

    def __init__(self, channel):
        """
        Create a new StatsClientChannelEvents object

        :param channel: (pika.channel.Channel) The channel object to manage
        :raises ValueError: if channel does not appear to be valid
        :return: None
        """

        if isinstance(channel, pika.channel.Channel):
            self.__channel = channel

        else:
            raise ValueError("No valid channel to manage was passed in")


    def stop_stats_client(self, signal=None, frame=None):
        """
        Stops the pika event loop for the managed channel

        :param signal: (int) A number if a intercepted signal caused this handler
                       to be run, otherwise None
        :param frame: A Stack Frame object, if an intercepted signal caused this
                      handler to be run
        :return: None
        """
        # TODO: Attempt to gracefully stop pika's event loop
        # See: https://pika.readthedocs.org/en/0.9.14/modules/adapters/blocking.html#pika.adapters.blocking_connection.BlockingChannel.stop_consuming
        self.__channel.stop_consuming()


def on_new_msg(channel, delivery_info, msg_properties, msg):
    """
    Event handler that processes new messages from the message broker

    For details on interface for this pika event handler, see:
    https://pika.readthedocs.org/en/0.9.14/examples/blocking_consume.html

    :param channel: (pika.Channel) The channel object this message was received
                    from
    :param delivery_info: (pika.spec.Basic.Deliver) Delivery information related
                          to the message just received
    :param msg_properties: (pika.spec.BasicProperties) Additional metadata about
                           the message just received
    :param msg: The message received from the server
    :return: None
    """

    # Parse the JSON message into a dict
    try:
        stats = json.loads(msg)

        # Check that the message appears to be well formed
        if "cpu" not in stats:
            print "Warning: ignoring message: missing 'cpu' field"

        elif "net" not in stats:
            print "Warning: ignoring message: missing 'net' field"

        else:
            # Message appears well formed

            # Evaluate CPU field for max/min status
            # TODO: Store new global max if stats["cpu"] > stats_history["cpu"]["max"]

            # TODO: Store new global min if stats["cpu"] < stats_history["cpu"]["min"]

            # Store the current value
            stats_history["cpu"]["current"] = stats["cpu"]

            # evaluate NET field for max/min status
            for iface in stats["net"].keys():

                # Has the current iface been seen before?
                if iface not in stats_history["net"]:
                    # No, create a new entry for the iface
                    stats_history["net"][iface] = {"rx": {"max": 0.0, "min": float("inf"), "current": 0.0},
                                                   "tx": {"max": 0.0, "min": float("inf"), "current": 0.0}
                                                  }

                # Check if the iface key is well formed
                if "rx" not in stats["net"][iface]:
                    print "Warning: ignoring interface: " + iface + ": no 'rx' field"
                    continue

                elif "tx" not in stats["net"][iface]:
                    print "Warning: ignoring interface: " + iface + ": no 'tx' field"
                    continue

                else:
                    # Evaluate max and min for each iface mode
                    for iface_mode in ("rx", "tx"):
                        # TODO: Store new global max if stats["net"][iface][iface_mode] > stats_history["net"][iface][iface_mode]["max"]

                        # TODO: Store new global min if stats["net"][iface][iface_mode] < stats_history["net"][iface][iface_mode]["min"]

                        # Store the current value
                        stats_history["net"][iface][iface_mode]["current"] = stats["net"][iface][iface_mode]

            # TODO: Print the max, min, and current stats value to stdout

    except ValueError, ve:
        # Thrown by json.loads() if it could not parse a JSON object
        print "Warning: Discarding Message: received message could not be parsed"



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

    # TODO: Parse the command line arguments

    # Ensure that the user specified the required arguments
    if host is None:
        print "You must specify a message broker to connect to"
        sys.exit()

    if topic is None:
        print "You must specify a topic to subscribe to"
        sys.exit()

    message_broker = None
    channel = None
    try:
        # TODO: Connect to the message broker using the given broker address (host)
        # Use the virtual host (vhost) and credential information (credentials),
        # if provided

        # TODO: Setup the channel and exchange
        channel = # Setup channel from connected message broker

        # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is
        # sent to this app
        # For more info about signals, see: https://scholar.vt.edu/portal/site/0a8757e9-4944-4e33-9007-40096ecada02/page/e9189bdb-af39-4cb4-af04-6d263949f5e2?toolstate-701b9d26-5d9a-4273-9019-dbb635311309=%2FdiscussionForum%2Fmessage%2FdfViewMessageDirect%3FforumId%3D94930%26topicId%3D3507269%26messageId%3D2009512
        signal_num = signal.SIGINT
        try:
            # Create a StatsClientChannelEvents object to store a reference to
            # the channel that will need to be shutdown if a signal is caught
            channel_manager = StatsClientChannelHelper(channel)
            signal.signal(signal_num, channel_manager.stop_stats_client)
            signal_num = signal.SIGTERM
            signal.signal(signal_num, channel_manager.stop_stats_client)

        except ValueError, ve:
            print "Warning: Greceful shutdown may not be possible: Unsupported " \
                  "Signal: " + signal_num

        # TODO: Create a queue
        # --------------------
        # It is up to you to determine what type of queue to create...
        # For example, if you create an exclusive queue, then the queue will
        # only exist as long as your client is connected
        # or you could create a queue that will continue to receive messages
        # even after your client app disconnects.
        #
        # In the short report, you should document what type of queue you create
        # and the series of events that occur at your client and the message broker
        # when your client connects or disconnects. (Slide 10).

        # TODO: Bind your queue to the message exchange, and register your
        #       new message event handler

        # TODO: Start pika's event loop

    except pika.exceptions.AMQPError, ae:
        print "Error: An AMQP Error occured: " + ae.message

    except pika.exceptions.ChannelError, ce:
        print "Error: A channel error occured: " + ce.message

    except Exception, eee:
        print "Error: An unexpected exception occured: " + eee.message

    finally:
        # TODO: Attempt to gracefully shutdown the connection to the message broker
        # For closing the channel gracefully see: http://pika.readthedocs.org/en/0.9.14/modules/channel.html#pika.channel.Channel.close
        if channel is not None:
            channel.close()
        # For closing the connection gracefully see: http://pika.readthedocs.org/en/0.9.14/modules/connection.html#pika.connection.Connection.close
        if message_broker is not None:
            message_broker.close()

except Exception, ee:
    # Add code here to handle the exception, print an error, and exit gracefully