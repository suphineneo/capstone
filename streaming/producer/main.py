from producer.stream import stream_coins
from producer.historical import stream_historical


def call_stream():
    stream_coins()


def call_historical():
    stream_historical()


if __name__ == "__main__":

    call_stream()
    # call_historical()
