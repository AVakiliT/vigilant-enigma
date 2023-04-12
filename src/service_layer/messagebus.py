from src.domain import events


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


def send_out_of_stock_notification(event: events.OutOfStock):
    print(f"Out of Stock {event.sku}")


HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification]
}
