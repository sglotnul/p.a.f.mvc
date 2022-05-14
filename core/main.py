from mymvc2.conf.settings import DEBUG
from mymvc2.apps.registry import apps
from mymvc2.core.request import Request
from mymvc2.core.response import Response
from mymvc2.core.response.default_responses import DebugReponse, get_default_page
from mymvc2.core.response.exceptions import ResponseException
from mymvc2.view import View

class PyMVC:
	def _get_request(self, environ: dict) -> Request:
		return Request(environ)

	def _find_view(self, url: str) -> View:
		for app in apps.registered_apps.values():
			for urlpattern in app.get_urlpatterns():
				if urlpattern.match(url):
					return urlpattern.get_view()
		raise ResponseException(404, "view not found")
	
	def _get_response(self, request: Request, url: str) -> Response:
		try:
			view = self._find_view(url)
			response = view(request)
			if not isinstance(response, Response):
				raise ResponseException(500, "view didn't return Response object")
			return response
		except Exception as exc:
			if not DEBUG:
				if isinstance(exc, ResponseException):
					return get_default_page(exc.code)
				return get_default_page()
			raise exc

	def _start_response(self, response: Response, start_response):
		start_response(response.status, response.get_headers())
		return [response.body]
	
	def __call__(self, environ: dict, start_response, **kwargs) -> list:
		request = self._get_request(environ)
		response = self._get_response(request, environ['PATH_INFO'])

		return self._start_response(response, start_response)
	
def main(environ: dict, start_response, **kwargs):
	mvc = PyMVC()
	return mvc(environ, start_response)