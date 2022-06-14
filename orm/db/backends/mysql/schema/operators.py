from mymvc2.orm.db.operator import Operator

comma = ","

def field_to_sql(field: str, data_type: str, default: str=None, null: bool=False) -> str:
	FIELD_TMP = "{} {}"
	NULL_POSTFIX = "NULL"
	NOT_NULL_POSTFIX = "NOT NULL"
	DEFAULT_POSTFIX = "DEFAULT {}"
	separator = " "

	raw_field_sql = FIELD_TMP.format(field, data_type)
	if default is not None:
		return raw_field_sql + separator + DEFAULT_POSTFIX.format(default)
	postfix = NOT_NULL_POSTFIX if not 'null' else NULL_POSTFIX
	return raw_field_sql + separator + postfix

class CreateTableOperator(Operator):
	CMD = "CREATE TABLE {};"
	TABLE_TMP = "{} ({})"
	FOREIGN_KEY = "FOREIGN KEY ({field}) REFERENCES {references}({key})"
	PRIMARY_KEY = "PRIMARY KEY ({})"

	def __init__(self):
		self._tables = {}

	def _field_to_sql(self, field: str, meta: dict) -> str:
		return field_to_sql(field, meta['data_type'], meta['default'], meta['null'])
	
	def _prepare_fields(self, fields: dict) -> str:
		return comma.join((self._field_to_sql(field, meta) for field, meta in fields.items()))
	
	def _prepare_constraints(self, fields: dict) -> str:
		default_key = "id"
		f_keys = []
		p_key = None
		for field, meta in fields.items():
			if meta.get('references'):
				f_keys.append((field, meta['references']))
			if meta.get('primary_key'):
				p_key = field
		constraints = list(self.FOREIGN_KEY.format(field=field, references=related_table, key=default_key) for field, related_table in f_keys)
		if p_key:
			constraints.append(self.PRIMARY_KEY.format(p_key))
		return comma.join(constraints)

	def _prepare_definition(self, fields: dict) -> str:
		sql_view_fields = self._prepare_fields(fields)
		constraints = self._prepare_constraints(fields)
		return sql_view_fields + comma + constraints

	def _create_single_table_query(self, table: str, fields: dict) -> str:
		table_sql_view = self.TABLE_TMP.format(table, self._prepare_definition(fields))
		return self.CMD.format(table_sql_view)

	def set(self, table: str, fields: dict):
		self._tables[table] = fields

	def to_str(self) -> str:
		separator = "\n"
		return separator.join(self._create_single_table_query(table, fields) for table, fields in self._tables.items())
	
	def __bool__(self) -> bool:
		return bool(self._tables)

class DeleteTableOperator(Operator):
	CMD = "DROP TABLE {};"

	def __init__(self):
		self._tables = []

	def set(self, table: str):
		self._tables.append(table)

	def _get_tables_list(self) -> dict:
		return {
			'tables': comma.join(self._tables)
		}
	
	def to_str(self) -> str:
		return self.CMD.format(self._get_tables_list()) 
	
	def __bool__(self) -> bool:
		return bool(self._tables)

class ChangeTableOperator(Operator):
	def __init__(self):
		self._schemas = []

	def set(self, schema: object):
		self._schemas.append(schema)

	def to_str(self) -> str:
		return "\n".join(schema.to_str() for schema in self._schemas)

	def __bool__(self) -> bool:
		return bool(self._schemas)

class AlterTable(Operator):
	CMD = "ALTER TABLE {}"

	def __init__(self):
		self._table = None
	
	def set(self, table: str):
		self._table = table

	def to_str(self) -> str:
		return self.CMD.format(self._table)
	
	def __bool__(self) -> bool:
		return bool(self._table)

class AddOperator(Operator):
	CMD = "ADD {}"

	def __init__(self):
		self._cols = {}

	def set(self, col: str, meta: dict):
		self._cols[col] = meta
	
	def _add_single_field(self, field: str, meta: dict) -> str:
		return self.CMD.format(field_to_sql(field, meta['data_type'], meta['default'], meta['null']))

	def to_str(self) -> str:
		return comma.join((self._add_single_field(field, meta) for field, meta in self._cols.items()))

	def __bool__(self) -> bool:
		return bool(self._cols)

class DropOperator(Operator):
	CMD = "DROP {}"

	def __init__(self):
		self._cols = []

	def set(self, col: str):
		self._cols.append(col)
	
	def _drop_single_column(self, col: str) -> str:
		return self.CMD.format(col)

	def to_str(self) -> str:
		return comma.join(self._drop_single_column(col) for col in self._cols)

	def __bool__(self) -> bool:
		return bool(self._cols)

class AlterOperator(AddOperator):
	CMD = "CHANGE {}"

class RenameOperator(Operator):
	CMD = "RENAME TO {}"

	def __init__(self):
		self._name = None

	def set(self, name: str):
		self._name = name

	def to_str(self) -> str:
		return self.CMD.format(self._name)

	def __bool__(self) -> bool:
		return bool(self._name)
	
class AddForeignKeyOperator(Operator):
	CMD  = "ADD FOREIGN KEY ({field}) REFERENCES {references}(id)"

	def __init__(self):
		self._foreign_keys = {}

	def set(self, col: str, table: str):
		self._foreign_keys[col] = table

	def _add_single_fk(self, col: str, table: str) -> str:
		return self.CMD.format(field=col, references=table)

	def to_str(self) -> str:
		return comma.join((self._add_single_fk(field, table) for field, table in self._foreign_keys.items()))
	
	def __bool__(self) -> bool:
		return bool(self._foreign_keys)