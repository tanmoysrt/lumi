# Lumi 💧 <a href="https://hits.seeyoufarm.com"><img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FTanmoy741127%2Flumi&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false"/></a>

<img align="right" src="https://raw.githubusercontent.com/Tanmoy741127/cdn/main/lumi/lumi-logo.png" height="100px"/>

Lumi is an nano framework to convert your python functions into a REST API without any extra headache.

* This library is created by taking the concept of **RPC** and blended with **REST API** specs. 
* We need to just register the function and it will be available as a REST API. 
* Web-server written with **Gunicorn**
* Local development server provided for rapid development and prototyping.

## Installation

```bash
pip install lumi
```

## Function <--> API mapping
![function - API maaping](https://raw.githubusercontent.com/Tanmoy741127/cdn/main/lumi/function-api-map.png)


## How to use 🤔

Let's create a simple function to add two numbers.

```python
def add(a, b):
    return a + b

def substract(a, b):
    return a - b
```

Now, we want to expose this function as a REST API. We can do this by registering the function with Lumi.

```python
# app.py

from lumi import Lumi

app = Lumi()

app.register(add) # Registering the function
app.register(substract)

app.runServer(host="127.0.0.1", port=8080)
```

Noice 🎉🎉  API has been generated

Run the sever by
```
python app.py
```
You are going to see this in your terminal 
```
[2022-11-24 17:32:08 +0530] [10490] [INFO] Starting gunicorn 20.1.0
[2022-11-24 17:32:08 +0530] [10490] [INFO] Listening at: http://127.0.0.1:8080 (10490)
[2022-11-24 17:32:08 +0530] [10490] [INFO] Using worker: sync
[2022-11-24 17:32:08 +0530] [10492] [INFO] Booting worker with pid: 10492
...
...
[2022-11-24 17:32:08 +0530] [10500] [INFO] Booting worker with pid: 10500
```

Congratulations 👏. Our Server is online. 


The above code will generate a REST API with the following details.

- Endpoint : `127.0.0.1:8080`
- Route : `/add`
- Method : `POST`
- Sample Request Body : `{"a": 1, "b": 2}`

Let's run the API and test it.

```curl
curl -X POST -H "Content-Type: application/json" -d '{"a": 1, "b": 2}' http://127.0.0.1:8080/add
```

Output

```json
{
    "exit_code": 0, 
    "status_code": 200, 
    "result": 3, 
    "error": ""
}
```


Now you may think, the function name will be always same as the route. But, you can change the route by passing the route parameter.

```python
app.register(add, route="/addition")
```

## Status Codes

| Status Code | Description |
| --- | --- |
| 200 | Request successfully executed and No Error happened during function execution |
| 500 | Request was received but there was an error during function execution |
| 400 | Bad Request (Possible Reason - The required parameters for the function has not provided) |
| 405 | Method Not Allowed (Lumi only supports **POST** request) |
| 404 | The route has no function associated with that |


## Exit Codes
| Exit Code | Description |
| --- | --- |
| 0 | No Error |
| 1 | Error |

> Note : If the function has some error , you can expect the exit code to be 1 and the error message in the response.

## Task Lists
- [x] Base System
- [x] Add support for default parameters that is provided in the function
- [ ] Make available GET request for the function
- [ ] Provide option to override POST with PUT if the user wants
- [ ] Add authentication middleware support
- [ ] Support nested routing of urls
- [ ] For local development, create an file observer that can automatically reload the server when the file is changed.
- [ ] Add support for object serialization and deserialization based on argument types of function

## Contributing

Contributions are always welcome!
## Our community

<!-- readme: contributors -start -->
<!-- readme: contributors -end -->
