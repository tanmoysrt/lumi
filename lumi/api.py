import typing
from nanoid import generate
import json
import io
import os

from lumi.server import DevelopmentServer
from lumi.enums import RequestMethod
from lumi.helpers import parseQueryParameter

class Lumi:
    instance = None

    @staticmethod
    def getInstance():
        if Lumi.instance is None:
            Lumi.instance = Lumi()
        return Lumi.instance

    def __init__(self, debug=True):
        self.registered_functions = {}
        self.function_routing_map = {
            RequestMethod.GET: {},
            RequestMethod.POST : {},
            RequestMethod.PUT : {},
            RequestMethod.PATCH : {}
        }
        '''
        This dictionary will store the route along with request type and the function metadata
        Function metadata will have functionKey .
        With the functionKey we can get the function from the registered_functions dictionary
        '''

        self.debug = debug # Make it false, if you are in production

    def register(self, function, route:str=None, request_method=RequestMethod.POST)->None:
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


        self.function_routing_map[request_method][function_routing_map_key] = {
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
    
    def wsgi_app(self, environ:dict, start_response:typing.Callable):
        method = environ.get("REQUEST_METHOD","")
        content_type = environ.get("CONTENT_TYPE", "")
        route = environ.get("PATH_INFO", "")

        ## Block all the methods except GET, POST, PUT and PATCH
        if method != RequestMethod.GET and method != RequestMethod.POST and method != RequestMethod.PUT and method != RequestMethod.PATCH:
            start_response("405 Method Not Allowed", [('Content-Type', 'application/json')])
            if self.debug:
                print("[%s] [%s] %s" % (method, 405, route))
            return [b'{"exit_code": 1, "status_code": 405, "result": "", "error": "Method Not Allowed"}']

        ## Check content type
        # If other than application/json, return 415 Unsupported Media Type
        if content_type != "application/json" and method in [RequestMethod.POST, RequestMethod.PATCH, RequestMethod.PUT]:
            start_response("415 Unsupported Media Type", [('Content-Type', 'application/json')])
            if self.debug:
                print("[%s] [%s] %s" % (method, 425, route))
            return [b'{"exit_code": 1, "status_code": 415, "result": "", "error": "Unsupported Media Type"}']

        
        ## If route is not in the function_routing_map, return 404 Not Found
        if route not in self.function_routing_map[method]:
            start_response("404 Not Found", [('Content-Type', 'application/json')])
            if self.debug:
                print("[%s] [%s] %s" % (method, 404, route))
            return [b'{"exit_code": 1, "status_code": 404, "result": "", "error": "Not Found"}']

        # Body of the request
        raw_body = environ["wsgi.input"].read()
        if raw_body is None or raw_body == b"" or raw_body == "":
            # Maybe the request is not having any body, [Possible reason : Function needs no parameters]
            # So, we will pass an empty dictionary
            raw_body = "{}"

        ## Parse body of POST, PUT, PATCH
        request_body = None
        try:
            request_body = json.loads(raw_body)
        except :
            # If there is any error parsing the body of the request, return 400 Bad Request
            start_response("400 Bad Request", [('Content-Type', 'application/json')])
            if self.debug:
                print("[%s] [%s] %s" % (method, 400, route))
            return [b'{"exit_code": 1, "status_code": 400, "result": "", "error": "Failed to decode JSON"}']

        ## Parse data from query parameters in case of GET request
        if method == RequestMethod.GET:
            request_body = parseQueryParameter(environ["QUERY_STRING"])

        # Get the function metadata
        function_metadata = self.function_routing_map[method][route]
        function_object = self.registered_functions[function_metadata["key"]]

        ## Serialize the arguments
        arguments = []
        # Check if all the required parameters are present in the request body
        for parameter in function_metadata["parameters"]["required"]:
            if parameter in request_body:
                # If present, add it to the arguments list
                arguments.append(request_body[parameter])
            else:
                # If any of the required parameters are not present, return 400 Bad Request
                start_response("400 Bad Request", [('Content-Type', 'application/json')])
                if self.debug:
                    print("[%s] [%s] %s" % (method, 400, route))
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
        isFile = False

        try:
            result = function_object(*arguments)
            isFile = isinstance(result, io.IOBase)
            status_code = 200
            exit_code = 0
        except FileNotFoundError as e:
            error = str(e.strerror)
            status_code = 404
            exit_code = 1
        except Exception as e:
            error = str(e)
            status_code = 500
            exit_code = 1

        ## Serve Requests
        if isFile:
            # Send the file
            filename_with_path = result.name or 'unnamed'
            # Check if the result is instance of TextIOWrapper
            isTextIOWrapped = isinstance(result, io.TextIOWrapper)
            if isTextIOWrapped:
                result = io.open(filename_with_path, mode='rb')

            start_response("200 OK", [('Content-Disposition', f'attachment; filename={os.path.basename(filename_with_path)}')])
            if self.debug:
                print("[%s] [%s] %s" % (method, "200", route))
            if 'wsgi.file_wrapper' in environ:
                return environ['wsgi.file_wrapper'](result, os.path.getsize(filename_with_path))
            else:
                return iter(lambda: result.read(os.path.getsize(filename_with_path)), '')
        else:
            # All responses except file
            response = {
                "exit_code": exit_code,
                "status_code": status_code,
                "result": result if result is not None else "",
                "error": error if error is not None else ""
            }

            status_text = "200 OK" if status_code == 200 else f"{str(status_code)} Internal Server Error"
            start_response(status_text, [('Content-Type', 'application/json')])
            if self.debug:
                print("[%s] [%s] %s" % (method, status_code, route))
            return iter([json.dumps(response).encode()])

    def print_registered_functions(self):
        import json
        print(json.dumps(self.function_routing_map))

    def runServer(self, host="127.0.0.1", port=8080, threads:int=4):
        options = {
            'listen': '%s:%s' % (host, str(port)),
            'threads': threads,
        }
        devServer = DevelopmentServer(self, options)
        devServer.run()

    def __call__(self, environ:dict, start_response: typing.Callable) -> typing.Any:
        return self.wsgi_app(environ, start_response)
