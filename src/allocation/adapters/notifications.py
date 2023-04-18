import abc
import smtplib


class AbstractNotifications(abc.ABC):
    @abc.abstractmethod
    def send(self, destination, message):
        raise NotImplementedError

DEFAULT_HOST=None
DEFAULT_PORT=None
class EmailNotifications(AbstractNotifications):
    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT):
        pass
        # self.server = smtplib.SMTP(smtp_host, port=port)
        # self.server.noop()

    def send(self, destination, message):
        pass
        # msg = f'Subject: allocation service notification\n{message}'
        # self.server.sendmail(
        #     from_addr='allocations@example.com',
        #     to_addrs=[destination],
        #     msg=msg
        # )
