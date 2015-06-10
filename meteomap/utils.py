import math, gzip, io, os
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from meteomap.settings import DATABASE_STR


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
                print('done {} in {} @ {:0.2f}/s'.format(
                    nb_done, delta, speed))
            # with a nb_total specified, we can have more stats (like an ETA)
            else:
                print('done {} out of {} in {} @ {:0.2f}/s eta {}s'.format(
                    nb_done, self.nb_total, delta, speed,
                    timedelta(seconds=(self.nb_total - nb_done) / speed)))


def open(filename, *args, **kwargs):
    if filename.endswith('.gz'):
        return gzip.open(filename, *args, **kwargs)
    else:
        return io.open(filename, *args, **kwargs)


def ask_before_overwrite(filename):
    """ if `filename` already exists, will prompt before overwriting """
    if os.path.exists(filename):
        while True:
            choice = input(u'The file {} already exists. Overwrite? (Y/N) '.format(filename))
            if choice == 'Y':
                return True
            elif choice == 'N':
                return False
    else:
        return True


def init_session(verbose=False):
    engine = create_engine(DATABASE_STR, echo=verbose)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@contextmanager
def session_scope(dryrun=False):
    """Provide a transactional scope around a series of operations."""
    session = init_session()
    try:
        yield session
        if dryrun:
            print('would add %i new objects, modify %i and delete %i' %
                  session.new, session.dirty, session.deleted)
            session.rollback()
        else:
            session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
