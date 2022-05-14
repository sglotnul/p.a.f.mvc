from mymvc2.orm.db.schema import SchemaEngine, BaseTableSchemaEngine
from mymvc2.orm.db.sqlite.schema import operators
from mymvc2.orm.db.schema.operators import operator_delegating_metod

class SQLiteTableSchemaEngine(BaseTableSchemaEngine):
	def __init__(self, schema: object, table: str, fields: dict):
		super().__init__(table, fields)
		self._schema = schema
	
	@operator_delegating_metod
	def alter(self, col: str, field_meta: dict):
		self.drop(col)
		self.add(col, field_meta)
		
	def get_table_name(self) -> str:
		return self._table

	def get_state(self) -> dict:
		return self._state
	
	def get_schema(self) -> object:
		return self._schema
	
	def reset(self):
		super().reset()

		self._state = self._fields

		self._operators['drop'] = operators.SQLiteDropOperator(self)
		self._operators['add'] = operators.SQliteAddOperator(self)
		self._operators['add_fk'] = operators.SQliteAddForeignKeyOperator(self)
		self._operators['rename_to'] = operators.SQliteRenameOperator(self)

class SQLiteSchemaEngine(SchemaEngine):
	def alter_table(self, table: str, fields: dict) -> SQLiteTableSchemaEngine:
		table_schema_engine = SQLiteTableSchemaEngine(self, table, fields)
		self._operators['alter_table'].set(table_schema_engine)
		return table_schema_engine

	def reset(self):
		super().reset()
		
		self._operators['delete_table'] = operators.SQliteDeleteTableOperation()