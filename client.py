import json, requests

print requests.post("http://localhost:5000/resources/asdf", json={ 1:2 }).json()
