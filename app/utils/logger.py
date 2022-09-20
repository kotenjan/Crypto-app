from datetime import datetime as dt

# logging status of each component (write "docker logs --follow <container name>" in terminal to see the logs)
class Logger():

    def log(self, text):
        print(dt.now(), '|', text)

