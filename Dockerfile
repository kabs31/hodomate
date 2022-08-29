FROM python:3.7.3
ADD main.py .
ADD recommend.py .
ADD TravelSalesman.py .
RUN pip install --upgrade pip
RUN pip install pathlib flask datetime geopy

CMD ["python","./main.py"]