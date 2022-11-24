import typing
from nanoid import generate
import json
from lumi.server import DevelopmentServer
import multiprocessing

class Lumi:
    instance = None

    @staticmethod
    def getInstance():
        if Lumi.instance is None:
            Lumi.instance = Lumi()
        return Lumi.instance

    def __init__(self):
        self.registered_functions = {}
        self.function_routing_map = {}
        '''
        This dictionary will store the route and the function metadata
        Function metadata will have functionKey .
        With the functionKey we can get the function from the registered_functions dictionary
        '''

    def register(self, function, route:str=None)->None:
        functionKey = generate(size=10)
        
        # Store the function in the registered_functions dictionary
        self.registered_functions[functionKey] = function

        # Function name
        name = function.__code__.co_name
        module_name = function.__module__
        file_name = function.__code__.co_filename
                
        # Generate function metadata and store it in the function_routing_map
        no_of_arguments = function.__code__.co_argcount
        function_parameters = list(function.__code__.co_varnames)[:no_of_arguments]
        default_parameters = function.__defaults__
        default_parameters = list(default_parameters) if default_parameters is not None else []
        
        # Calculate no of parameters
        no_of_function_parameters = len(function_parameters)
        no_of_default_parameters = len(default_parameters)
        no_of_required_parameters = no_of_function_parameters - no_of_default_parameters

        # Calculate the required parameters and optional parameters
        required_parameters = function_parameters[:no_of_required_parameters]
        optional_parameters = function_parameters[no_of_required_parameters:no_of_function_parameters]

        # Create default parameters dictionary
        default_parameters_map = {}
        for i in range(len(optional_parameters)):
            default_parameters_map[optional_parameters[i]] = default_parameters[i]

        # Key for Function Routing Map
        function_routing_map_key = name if route is None else route

        # Add / if not at the start
        if function_routing_map_key.startswith("/") is False:
            function_routing_map_key = '/' + function_routing_map_key

        # Remove / if at the end
        if function_routing_map_key.endswith("/") is True:
            function_routing_map_key = function_routing_map_key[:-1]


        self.function_routing_map[function_routing_map_key] = {
            "name": name,
            "module_name": module_name,
            "file_name": file_name,
            "key": functionKey,
            "parameters": {
                "all": function_parameters,
                "required": required_parameters,
                "optional": optional_parameters
            },
            "default_values": default_parameters_map
        }
    
    def print_registered_functions(self):
        # print(self.registered_functions)
        import json
        print(json.dumps(self.function_routing_map))

    def runServer(self, host="127.0.0.1", port=8080):
        options = {
            'bind': '%s:%s' % (host, str(port)),
            'workers': (multiprocessing.cpu_count() * 2) + 1,
        }
        devServer = DevelopmentServer(self, options)
        devServer.run()

    def wsgi_app(self, environ:dict, start_response:typing.Callable):
        method = environ["REQUEST_METHOD"]
        # Block all the methods except POST
        if method != "POST":
            start_response("405 Method Not Allowed", [('Content-Type', 'application/json')])
            return [b'{"exit_code": 1, "status_code": 405, "result": "", "error": "Method Not Allowed"}']

        # Check content type
        # If other than application/json, return 415 Unsupported Media Type
        content_type = environ["CONTENT_TYPE"]
        if content_type != "application/json":
            start_response("415 Unsupported Media Type", [('Content-Type', 'application/json')])
            return [b'{"exit_code": 1, "status_code": 415, "result": "", "error": "Unsupported Media Type"}']

        route = environ["PATH_INFO"]
        # If route is not in the function_routing_map, return 404 Not Found
        if route not in self.function_routing_map:
            start_response("404 Not Found", [('Content-Type', 'application/json')])
            return [b'{"exit_code": 1, "status_code": 404, "result": "", "error": "Not Found"}']

        # Body of the request
        raw_body = environ["wsgi.input"].read()
        request_body = json.loads(raw_body)

        # Get the function metadata
        function_metadata = self.function_routing_map[route]
        function_object = self.registered_functions[function_metadata["key"]]

        # Serialize the arguments
        arguments = []
        # Check if all the required parameters are present in the request body
        for parameter in function_metadata["parameters"]["required"]:
            if parameter in request_body:
                # If present, add it to the arguments list
                arguments.append(request_body[parameter])
            else:
                # If any of the required parameters are not present, return 400 Bad Request
                start_response("400 Bad Request", [('Content-Type', 'application/json')])
                return [b"400 Bad Request"]

        # Check if any of the optional parameters are present in the request body
        for parameter in function_metadata["parameters"]["optional"]:
            if parameter in request_body:
                # If present, add it to the arguments list
                arguments.append(request_body[parameter])
            else:
                # If not present, add the default value to the arguments list
                arguments.append(function_metadata["default_values"][parameter])
        

        result = None
        error = None
        status_code = 200
        exit_code = 0

        try:
            result = function_object(*arguments)
            status_code = 200
            exit_code = 0
        except Exception as e:
            error = str(e)
            status_code = 500
            exit_code = 1

        response = {
            "exit_code": exit_code,
            "status_code": status_code,
            "result": result if result is not None else "",
            "error": error if error is not None else ""
        }

        status_text = "200 OK" if status_code == 200 else "500 Internal Server Error"
        start_response(status_text, [('Content-Type', 'application/json')])
        return iter([json.dumps(response).encode()])

    def __call__(self, environ:dict, start_response: typing.Callable) -> typing.Any:
        return self.wsgi_app(environ, start_response)
