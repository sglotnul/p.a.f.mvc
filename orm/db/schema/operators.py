from abc import abstractmethod
from mymvc2.orm.db.operator import Operator, OperatorRegistry

def field_to_sql(field: str, data_type: str, default: str=None, null: bool=False) -> str:
	FIELD_TMP = "%(field)s %(data_type)s"
	NULL_POSTFIX = "NULL"
	NOT_NULL_POSTFIX = "NOT NULL"
	DEFAULT_POSTFIX = "DEFAULT %(value)s"
	separator = " "

	raw_field_sql = FIELD_TMP % {'field': field, 'data_type': data_type}
	if default is not None:
		return raw_field_sql + separator + DEFAULT_POSTFIX % {'value': default}
	postfix = NOT_NULL_POSTFIX if not 'null' else NULL_POSTFIX
	return raw_field_sql + separator + postfix

def operator_delegating_metod(func):
	def wrapper(self, *args, instantly=False, **kwargs):
		if instantly:
			schema = self.copy()
			func.__get__(schema, schema.__class__)(*args, **kwargs)
			return str(schema)
		return func(self, *args, **kwargs)
	return wrapper

class SchemaOperatorRegistry(OperatorRegistry):
	@abstractmethod
	def copy(self) -> object:
		return self.__class__()

class SchemaOperator(Operator):
	CMD = ""

class CreateTableOperator(SchemaOperator):
	CMD = "CREATE TABLE %(table)s;"
	TABLE_TMP = "%(table)s (%(definition)s)"
	FOREIGN_KEY = "FOREIGN KEY (%(field)s) REFERENCES %(references)s(%(key)s)"
	PRIMARY_KEY = "PRIMARY KEY (%(field)s)"

	def __init__(self):
		self._tables = {}

	def _field_to_sql(self, field: str, meta: dict) -> str:
		return field_to_sql(field, meta['data_type'], meta['default'], meta['null'])
	
	def _prepare_fields(self, fields: dict) -> str:
		separator = ","
		return separator.join((self._field_to_sql(field, meta) for field, meta in fields.items()))
	
	def _prepare_constraints(self, fields: dict) -> str:
		separator = ","
		default_key = "id"
		f_keys = {}
		p_key = None
		for field, meta in fields.items():
			if meta.get('references'):
				f_keys[field] = meta['references']
			if meta.get('primary_key'):
				p_key = field
		constraints = list(self.FOREIGN_KEY % {'field': field, 'references': related_table, 'key': default_key} for field, related_table in f_keys.items())
		if p_key:
			constraints.append(self.PRIMARY_KEY % {'field': p_key})
		return separator.join(constraints)

	def _prepare_definition(self, fields: dict) -> str:
		separator = ","
		sql_view_fields = self._prepare_fields(fields)
		constraints = self._prepare_constraints(fields)
		return sql_view_fields + separator + constraints

	def _create_single_table_query(self, table: str, fields: dict) -> str:
		table_sql_view = self.TABLE_TMP % {
			'table': table,
			'definition': self._prepare_definition(fields),
		}
		return self.CMD % {'table': table_sql_view}

	def set(self, table: str, fields: dict):
		self._tables[table] = fields

	def __str__(self) -> str:
		separator = "\n"
		return separator.join(self._create_single_table_query(table, fields) for table, fields in self._tables.items())
	
	def __bool__(self) -> bool:
		return bool(self._tables)

class DeleteTableOperator(SchemaOperator):
	CMD = "DROP TABLE %(tables)s;"

	def __init__(self):
		self._tables = []

	def set(self, table: str):
		self._tables.append(table)

	def _get_tables_list(self) -> dict:
		separator = ","
		return {
			'tables': separator.join(self._tables)
		}
	
	def __str__(self) -> str:
		return self.CMD % self._get_tables_list()
	
	def __bool__(self) -> bool:
		return bool(self._tables)

class ChangeTableOperator(Operator):
	def __init__(self):
		self._schemas = []

	def set(self, schema: object):
		self._schemas.append(schema)

	def __str__(self) -> str:
		return "\n".join((str(schema) for schema in self._schemas))

	def __bool__(self) -> bool:
		return bool(self._schemas)

class AlterTableOperator(Operator):
	ALTER_TABLE = "ALTER TABLE %(table)s\n%(operation)s;"

	def __init__(self, table: str):
		self._table = table

class AlterTableSchemaOperator(AlterTableOperator):
	@abstractmethod
	def _create_operation_body(self) -> str:
		raise NotImplementedError()

	def __str__(self) -> str:
		return self.ALTER_TABLE % {
			'table': self._table,
			'operation': self._create_operation_body(),
		}

class AddOperator(AlterTableSchemaOperator):
	CMD = "ADD %(column)s"

	def __init__(self, table: str):
		super().__init__(table)
		self._cols = {}

	def set(self, col: str, meta: dict):
		self._cols[col] = meta
	
	def _add_single_field(self, field: str, meta: dict) -> str:
		return self.CMD % {'column': field_to_sql(field, meta['data_type'], meta['default'], meta['null'])}

	def _create_operation_body(self) -> str:
		separator = ","
		return separator.join((self._add_single_field(field, meta) for field, meta in self._cols.items()))

	def __bool__(self) -> bool:
		return bool(self._cols)

class DropOperator(AlterTableSchemaOperator):
	CMD = "DROP %(column)s"

	def __init__(self, table: str):
		super().__init__(table)
		self._cols = []

	def set(self, col: str):
		self._cols.append(col)
	
	def _drop_single_column(self, col: str) -> str:
		return self.CMD % {'column': col}

	def _create_operation_body(self) -> str:
		separator = ","
		return separator.join(self._drop_single_column(col) for col in self._cols)

	def __bool__(self) -> bool:
		return bool(self._cols)

class AlterOperator(AddOperator):
	CMD = "CHANGE %(column)s"

class RenameOperator(AlterTableSchemaOperator):
	CMD = "RENAME TO %(name)s"

	def __init__(self, table: str):
		super().__init__(table)
		self._name = None

	def set(self, name: str):
		self._name = name

	def _create_operation_body(self) -> str:
		return self.CMD % {'name': self._name}

	def __bool__(self) -> bool:
		return bool(self._name)
	
class AddForeignKeyOperator(AlterTableSchemaOperator):
	CMD  = "ADD FOREIGN KEY (%(field)s) REFERENCES %(references)s(id)"

	def __init__(self, table: str):
		super().__init__(table)
		self._foreign_keys = {}

	def set(self, col: str, table: str):
		self._foreign_keys[col] = table

	def _add_single_fk(self, col: str, table: str) -> str:
		return self.CMD % {
			'field': col,
			'references': table,
		}

	def _create_operation_body(self) -> str:
		separator = ","
		return separator.join((self._add_single_fk(field, table) for field, table in self._foreign_keys.items()))
	
	def __bool__(self) -> bool:
		return bool(self._foreign_keys)