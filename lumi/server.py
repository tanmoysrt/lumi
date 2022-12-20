from waitress import serve

'''
Development server for RPC . Used waitress WSGI server.
In production, use gunicorn daemon to manage the server.
'''
class DevelopmentServer:
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def run(self):
        try:
            print("🚀 Running development server at http://%s" % self.options["listen"])
            return serve(self.application, listen=self.options["listen"], threads=self.options["threads"])
        except KeyboardInterrupt:
            print("Shutting down server.")

