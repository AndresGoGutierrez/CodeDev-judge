# Script para actualizar registros existentes con valores None
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Configurar tu conexión a la base de datos
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/db_juez-microservicio"
print(f"Conectando a la base de datos:postgres@localhost:5432/db_juez-microservicio")  # Reemplaza con tu URL real
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def inspect_table_structure():
    """Inspeccionar la estructura de la tabla problems"""
    print("🔍 Inspeccionando estructura de la tabla 'problems'...")
    
    inspector = inspect(engine)
    
    # Verificar si la tabla existe
    tables = inspector.get_table_names()
    print(f"Tablas disponibles: {tables}")
    
    if 'problems' not in tables:
        print("❌ La tabla 'problems' no existe!")
        return None
    
    # Obtener columnas de la tabla problems
    columns = inspector.get_columns('problems')
    
    print("\n📋 Columnas en la tabla 'problems':")
    print("-" * 50)
    column_names = []
    for column in columns:
        print(f"- {column['name']} ({column['type']})")
        column_names.append(column['name'])
    
    return column_names

def find_matching_columns(column_names):
    """Encontrar las columnas que corresponden a nuestros campos"""
    # Posibles nombres para cada campo
    field_mappings = {
        'input_format': ['inputFormat', 'input_format', 'inputformat'],
        'output_format': ['outputFormat', 'output_format', 'outputformat'], 
        'constraints': ['constraints', 'constraint'],
        'tags': ['tags', 'tag']
    }
    
    found_columns = {}
    
    for field, possible_names in field_mappings.items():
        for possible_name in possible_names:
            if possible_name in column_names:
                found_columns[field] = possible_name
                break
        
        if field not in found_columns:
            print(f"⚠️  No se encontró columna para {field}")
    
    print(f"\n✅ Columnas encontradas: {found_columns}")
    return found_columns

def update_null_fields_dynamic(column_mapping):
    """Actualizar campos NULL usando los nombres de columna correctos (con comillas)"""
    if not column_mapping:
        print("❌ No se pueden actualizar campos: no se encontraron columnas válidas")
        return
    
    db = SessionLocal()
    try:
        print("🔄 Iniciando actualización de campos NULL...")
        
        set_clauses = []
        where_clauses = []
        
        field_defaults = {
            'input_format': 'No especificado',
            'output_format': 'No especificado', 
            'constraints': 'No especificado',
            'tags': 'Sin etiquetas'
        }
        
        for field, column_name in column_mapping.items():
            default_value = field_defaults[field]
            # envolver el nombre de columna entre comillas dobles
            col = f'"{column_name}"'
            set_clauses.append(f"{col} = COALESCE({col}, :{field}_default)")
            where_clauses.append(f"{col} IS NULL")
        
        where_condition = " OR ".join(where_clauses)
        set_condition   = ", ".join(set_clauses)
        
        # preparar la consulta parametrizada
        update_query = text(f"""
            UPDATE problems
            SET {set_condition}
            WHERE {where_condition}
        """)
        
        # asignar parámetros para los valores por defecto
        params = {f"{field}_default": default for field, default in field_defaults.items() if field in column_mapping}
        
        result = db.execute(update_query, params)
        db.commit()
        
        print(f"✅ Se actualizaron {result.rowcount} registros")
        
    except Exception as e:
        print(f"❌ Error durante la actualización: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_update(column_mapping):
    """Verificar que todos los campos fueron actualizados correctamente"""
    if not column_mapping:
        return
        
    db = SessionLocal()
    try:
        # Columnas fijas
        columns_to_show = ['id_problem', 'title']
        # Añadimos las columnas dinámicas, pero entrecomilladas si tienen mayúsculas
        for col in column_mapping.values():
            # si el nombre difiere de la versión lowercase, lo comillamos
            if col.lower() != col:
                columns_to_show.append(f'"{col}"')
            else:
                columns_to_show.append(col)
        
        columns_str = ", ".join(columns_to_show)
        
        verify_query = text(f"""
            SELECT {columns_str}
            FROM problems 
            LIMIT 5
        """)
        
        result = db.execute(verify_query)
        records = result.fetchall()
        
        print("\n📋 Muestra de registros actualizados:")
        print("-" * 80)
        for record in records:
            print(f"ID: {record[0]}")
            print(f"Título: {record[1]}")
            
            # Mostrar los campos actualizados
            idx = 2
            for field, column_name in column_mapping.items():
                value = record[idx]
                print(f"{field.replace('_', ' ').title()}: {value}")
                idx += 1
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error al verificar: {e}")
    finally:
        db.close()


def main():
    try:
        print("🚀 Iniciando inspección y migración de datos...")
        
        # Paso 1: Inspeccionar estructura
        column_names = inspect_table_structure()
        if column_names is None:
            return
        
        # Paso 2: Encontrar columnas correspondientes
        column_mapping = find_matching_columns(column_names)
        
        # Paso 3: Actualizar campos NULL
        update_null_fields_dynamic(column_mapping)
        
        # Paso 4: Verificar actualización
        verify_update(column_mapping)
        
        print("\n✅ Migración completada exitosamente!")
        print("\n📝 Próximos pasos:")
        print("1. Actualiza tus esquemas de Pydantic para hacer los campos obligatorios")
        print("2. Actualiza las rutas para usar los nombres de columna correctos")
        print("3. Reinicia tu servidor FastAPI")
        
    except Exception as e:
        print(f"💥 Error crítico durante la migración: {e}")
        print("Por favor, revisa la conexión a la base de datos y vuelve a intentar.")

if __name__ == "__main__":
    main()