from logging.handlers import SMTPHandler
import smtplib
from threading import Thread

# mostly copied from
# http://stackoverflow.com/questions/8616617/how-to-make-smtphandler-not-block

def send_mail(mailhost, port, username, password, fromaddr, toaddrs, msg):
    smtp = smtplib.SMTP(mailhost, port)
    if username:
        smtp.ehlo() # for tls add this line
        smtp.starttls() # for tls add this line
        smtp.ehlo() # for tls add this line
        smtp.login(username, password)
    smtp.sendmail(fromaddr, toaddrs, msg)
    smtp.quit()

class ThreadedTlsSMTPHandler(SMTPHandler):
    """
        Usage example:

        logger = logging.getLogger()

        gm = ThreadedTlsSMTPHandler(("smtp.gmail.com", 587), 'bugs@my_company.com', ['admin@my_company.com'], 'Error found!', ('my_company_account@gmail.com', 'top_secret_gmail_password'))
        gm.setLevel(logging.ERROR)

        logger.addHandler(gm)

        try:
            1/0
        except:
            logger.exception('FFFFFFFFFFFFFFFFFFFFFFFUUUUUUUUUUUUUUUUUUUUUU-')
    """
    def emit(self, record):
        try:
            import string # for tls add this line
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            string.join(self.toaddrs, ","),
                            self.getSubject(record),
                            formatdate(), msg)
            thread = Thread(target=send_mail, args=(self.mailhost, port, self.username, self.password, self.fromaddr, self.toaddrs, msg))
            thread.start()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

