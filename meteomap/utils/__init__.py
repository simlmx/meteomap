import math, gzip, io, os, logging, logging.config, zipfile
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from meteomap.settings import DATABASE_STR, LOGGING_CONFIG

logger = logging.getLogger(__name__)


class Timer(object):
    def __init__(self, nb_total=None, dont_print_before=1, print_if=None):
        self.nb_total = nb_total
        self.min_print = dont_print_before
        self.start = datetime.utcnow()
        self.nb_done = 0

        if print_if is None:
            def f(nb_done):
                """ only prints 0,1,2,3,9,10,20,30,..,90,100,200,300,...etc.
                """
                return nb_done % (10**int(math.log10(nb_done))) == 0
            print_if = f
        self.print_if = print_if

    def update(self, nb_done=None):
        """ if nb_done is None, we will assume we did one more """
        if nb_done is None:
            self.nb_done += 1
            nb_done = self.nb_done
        else:
            self.nb_done = nb_done

        if nb_done >= self.min_print and self.print_if(nb_done):
            delta = datetime.utcnow() - self.start
            speed = 1. * nb_done /delta.total_seconds()
            # without a nb_total specified, there is not much we can tell
            if self.nb_total is None:
                logger.info('done {} in {} @ {:0.2f}/s'.format(
                    nb_done, delta, speed))
            # with a nb_total specified, we can have more stats (like an ETA)
            else:
                logger.info(
                    'done {} out of {} in {} @ {:0.2f}/s eta {}s'.format(
                    nb_done, self.nb_total, delta, speed,
                    timedelta(seconds=(self.nb_total - nb_done) / speed)))


def open(filename, *args, **kwargs):
    """ Open different types of files based on the extension """
    if filename.endswith('.gz'):
        return gzip.open(filename, *args, **kwargs)
    elif filename.endswith('.zip'):
        z = zipfile.ZipFile(filename)
        names = z.namelist()
        if len(names) != 1:
            raise ValueError('.zip files containing more than one file are not'
                             ' supported')
        return io.TextIOWrapper(z.open(names[0], 'rU'))
    else:
        return io.open(filename, *args, **kwargs)


def ask_before_overwrite(filename):
    """ if `filename` already exists, will prompt before overwriting """
    if os.path.exists(filename):
        return are_you_sure(
            u'The file {} already exists. Overwrite?'.format(filename))
    else:
        return True


def are_you_sure(msg='Are you sure?'):
    """ prompts and asks if sure to do X """
    while True:
        choice = input(msg + ' (Y/N) ')
        if choice == 'Y':
            return True
        elif choice == 'N':
            return False


def init_session(url=DATABASE_STR, verbose=False):
    engine = create_engine(url, echo=verbose)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@contextmanager
def session_scope(url=DATABASE_STR, dryrun=False):
    """Provide a transactional scope around a series of operations."""
    session = init_session(url)
    try:
        yield session
        if dryrun:
            logger.info('would add %i new objects, modify %i and delete %i',
                  len(session.new), len(session.dirty), len(session.deleted))
            # session.rollback()
        else:
            session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def configure_logging(level=None):
    """
        level : overwrites the level in the config
        everything >= `level` to console and rotating file
        critial to email

    """

    if level is None:
        level = LOGGING_CONFIG['level']
    EMAIL = LOGGING_CONFIG['email']

    common_logger_settings = {
        'level': level,
        'handlers': LOGGING_CONFIG["handlers"]
    }

    logging_config = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/logs.txt',
                'formatter': 'default'
            },
            'email': {
                'class':
                'meteomap.utils.threaded_tls_smtp_handler.ThreadedTlsSMTPHandler',
                'mailhost': (EMAIL['server'], EMAIL['port']),
                'fromaddr': EMAIL['address'],
                'toaddrs': [EMAIL['address']],
                'subject': '%(levelname)s meteomap',
                'credentials': (EMAIL['address'], EMAIL['pass']),
                'level': 'ERROR',
                'formatter': 'default'
            }
        },
        'formatters': {
            'default': {
                'format': '%(asctime)s [%(levelname)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'loggers': {
            '__main__': common_logger_settings,
            'meteomap': common_logger_settings,
        }
    }

    logging.config.dictConfig(logging_config)
