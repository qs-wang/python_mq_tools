import click
import os
import requests
import pika
import json
import logging
import cuid
from config import parse_config, create_config, get_config_dict

default_url_template =  'amqp://{}:{}@{}/%2F?heartbeat_interval=1'
vhost_url_template = 'amqp://{}:{}@{}/{}/%2F?heartbeat_interval=1'

# set up logging
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'),
                    format='[%(asctime)s - %(filename)s:%(lineno)s - %(funcName)s()]-12s %(levelname)-8s %(message)s))',
                    datefmt='%m-%d %H:%M')

logger = logging.getLogger(__name__)

CONFIG_DIR = '.qs'
CONFIG_FILE = 'mq_config.ini'
HOME = os.path.expanduser('~')

CONFIG_FOLDER = HOME + '/' + CONFIG_DIR
CONFIG_PATH = CONFIG_FOLDER + '/' + CONFIG_FILE


@click.group()
def cli():
    pass


@click.command()
@click.argument('key')
@click.argument('value', default='')
@click.option('--profile', '-p', default='DEFAULT', help='The profile name')
def config(key, value, profile):
    if value == '':
        config_dict = load_config_dict_for_profile(profile)
        click.echo('{} = {} for profile: {}'.format(
            key, config_dict[key], profile))
    else:
        config = parse_config(CONFIG_PATH)
        if not config.has_section(profile) and profile != 'DEFAULT':
            config.add_section(profile)
        config.set(profile, key, value)
        with open(CONFIG_PATH, 'wb') as config_file:
            config.write(config_file)

@click.command()
@click.argument('routing_key')
@click.argument('exchange_name', default='')
@click.option('--message', '-m', default=None, help='The message body')
@click.option('--data', '-d', default=None, help='The message data file')
@click.option('--vhost', '-h', default=None, help='The virtual host')
@click.option('--profile', '-p', default='DEFAULT', help='The profile name')
def sd(routing_key, exchange_name, profile,message, data,vhost):

    if not message and not data:
        click.echo('You must specify one of the -message/-data option')

    message_body = message
    if not message_body:
        message_body = load_data_file(data)

    config_dict = load_config_dict_for_profile(profile)
    if 'user' not in config_dict:
        click.echo('Please config the username')
        return

    user = config_dict.get('user')

    if 'QS_MQ_PASSWORD' not in os.environ:
        click.echo('Please set the QS_MQ_PASSWORD')
        return

    password = os.environ.get('QS_MQ_PASSWORD')

    if 'host' in config_dict:
        host = config_dict['host']
        end_point = default_url_template.format(user,password,host)
        if vhost:
            end_point = vhost_url_template.format(user,password,host,vhost)

        logger.debug('Endpoint url is {}'.format( end_point))

        params = pika.URLParameters(end_point)
        params.socket_timeout = config_dict.get('timeout', 5)

        connection = pika.BlockingConnection(params) 
        channel = connection.channel() 

        channel.queue_declare(queue=routing_key) # Declare a queue
        
        # send a message
        channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=message_body)
        logger.info ("[x] Message sent to consumer")
        connection.close()
    else:
        click.echo("Host hasn't been configured")

def load_data_file( data_file):
    if not os.path.isabs(data_file):
        data_file = os.path.abspath(data_file)
    with open(data_file) as f:
        message_body = f.read()
    return message_body

def load_config_dict_for_profile(profile):
    config_object = parse_config(CONFIG_PATH)
    config_dict = get_config_dict(config_object, profile)
    return config_dict


cli.add_command(config)
cli.add_command(sd)

if __name__ == '__main__':
    if not os.path.exists(CONFIG_PATH):
        create_config(CONFIG_PATH)
    cli()
