from typing import List

TABLE_INFO = "PRAGMA table_info(%s);"

class QuerySet:
	def __init__(self, model_cls: type, executor: object):
		self._executor = executor
		self._model = model_cls
		self._query = self._executor.query(self._model.meta.name)
	
	def _zip_model(self, cols: iter, row: iter) -> object:
		fields = dict(zip(cols, row))
		return self._model(**fields)
		
	def _fetch(self) -> List[object]:
		model_list = []
		self._executor.connect()
		cur = self._executor(self._query.to_str())
		columns = tuple(map(lambda x: x[0], cur.description))
		for row in cur:
			model_list.append(self._zip_model(columns, row))
		self._executor.close()
		return model_list

	def all(self):
		return self

	def filter(self, **params):
		self._query.filter(**params)
		return self

	def get(self, **params) -> object:
		self.filter(**params)
		self._query.set_limit(1)
		models = self._fetch()
		return None if not models else models[0]

	def order_by(self, field: str):
		self._query.order_by(field)
		return self
		
	def __iter__(self):
		for obj in self._fetch():
			yield obj