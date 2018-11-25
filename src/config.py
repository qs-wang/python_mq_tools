import os, sys

if sys.version_info >= (3,0):
    isPython3 = True
    import configparser
else:
    isPython3 = False
    import ConfigParser

def create_config(path):
    """
    Create a config file
    """
    config = get_config_parser()
    cofing_dir = os.path.dirname(path)
    if not os.path.exists(cofing_dir):
        os.makedirs(cofing_dir)
        
    with open(path, "wb") as config_file:
        config.write(config_file)

    return config_file

def parse_config(config_filename):
    if not os.path.isfile(config_filename):
        sys.stderr.write(
            'Config file not found: {:s}\nCWD: {:s}\n\n'.format(config_filename, os.getcwd()))

    cfg = get_config_parser()
    cfg.read(config_filename)

    return cfg

def get_config_dict(cfg, profile='DEFAULT'):
    # implements a read-only dict
    return dict(cfg.items(profile))

def get_config_parser():
    if isPython3:
        cfg = configparser.ConfigParser()
    else:
        cfg = ConfigParser.SafeConfigParser()
    return cfg