import multiprocessing
import pyttsx3

_queue: multiprocessing.Queue
_process: multiprocessing.Process


class Audio:
    def __init__(self, text, rate=200):
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.say(text)
        engine.runAndWait()
        del self


def api_process(queue: multiprocessing.Queue):
    while True:
        message = queue.get()
        if message == "STOP":
            break
        text = message['text']
        rate = message.get('rate', 200)
        Audio(text, rate)


def speak(text, rate=200):
    global _queue  # Make sure to reference the global queue
    message = {'text': text, 'rate': rate}
    _queue.put(message)


def init_audio():
    global _queue, _process  # Make sure to reference the global variables
    _queue = multiprocessing.Queue()
    _process = multiprocessing.Process(target=api_process, args=(_queue,))
    _process.start()


def terminate_audio():
    global _queue, _process  # Make sure to reference the global variables
    _queue.put("STOP")
    _process.join()
