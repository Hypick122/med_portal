import logging

from app import app

for logger in ["apscheduler.scheduler", "apscheduler.executors.default"]:
    logging.getLogger(logger).disabled = True

if __name__ == "__main__":
    app.run(port=80, host='0.0.0.0', debug=False)
    # app.run(port=80, host='127.0.0.1', debug=True)
