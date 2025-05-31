# Script to update existing records with None values
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Configure your database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/db_juez-microservicio"
print(f"Connecting to database:postgres@localhost:5432/db_juez-microservicio")  # Replace with your actual URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def inspect_table_structure():
    """Inspect the structure of the problems table"""
    print("🔍 Inspecting structure of 'problems' table...")
    
    inspector = inspect(engine)
    
    # Check if the table exists
    tables = inspector.get_table_names()
    print(f"Available tables: {tables}")
    
    if 'problems' not in tables:
        print("❌ The 'problems' table does not exist!")
        return None
    
    # Get columns of the problems table
    columns = inspector.get_columns('problems')
    
    print("\n📋 Columns in the 'problems' table:")
    print("-" * 50)
    column_names = []
    for column in columns:
        print(f"- {column['name']} ({column['type']})")
        column_names.append(column['name'])
    
    return column_names

def find_matching_columns(column_names):
    """Find columns that correspond to our fields"""
    # Possible names for each field
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
            print(f"⚠️  No column found for {field}")
    
    print(f"\n✅ Found columns: {found_columns}")
    return found_columns

def update_null_fields_dynamic(column_mapping):
    """Update NULL fields using correct column names (with quotes)"""
    if not column_mapping:
        print("❌ Cannot update fields: no valid columns found")
        return
    
    db = SessionLocal()
    try:
        print("🔄 Starting NULL fields update...")
        
        set_clauses = []
        where_clauses = []
        
        field_defaults = {
            'input_format': 'Not specified',
            'output_format': 'Not specified', 
            'constraints': 'Not specified',
            'tags': 'No tags'
        }
        
        for field, column_name in column_mapping.items():
            default_value = field_defaults[field]
            # wrap column name in double quotes
            col = f'"{column_name}"'
            set_clauses.append(f"{col} = COALESCE({col}, :{field}_default)")
            where_clauses.append(f"{col} IS NULL")
        
        where_condition = " OR ".join(where_clauses)
        set_condition   = ", ".join(set_clauses)
        
        # prepare parameterized query
        update_query = text(f"""
            UPDATE problems
            SET {set_condition}
            WHERE {where_condition}
        """)
        
        # assign parameters for default values
        params = {f"{field}_default": default for field, default in field_defaults.items() if field in column_mapping}
        
        result = db.execute(update_query, params)
        db.commit()
        
        print(f"✅ Updated {result.rowcount} records")
        
    except Exception as e:
        print(f"❌ Error during update: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_update(column_mapping):
    """Verify that all fields were updated correctly"""
    if not column_mapping:
        return
        
    db = SessionLocal()
    try:
        # Fixed columns
        columns_to_show = ['id_problem', 'title']
        # Add dynamic columns, quoted if they have uppercase letters
        for col in column_mapping.values():
            # quote if name differs from lowercase version
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
        
        print("\n📋 Sample of updated records:")
        print("-" * 80)
        for record in records:
            print(f"ID: {record[0]}")
            print(f"Title: {record[1]}")
            
            # Show updated fields
            idx = 2
            for field, column_name in column_mapping.items():
                value = record[idx]
                print(f"{field.replace('_', ' ').title()}: {value}")
                idx += 1
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error verifying update: {e}")
    finally:
        db.close()


def main():
    try:
        print("🚀 Starting data inspection and migration...")
        
        # Step 1: Inspect structure
        column_names = inspect_table_structure()
        if column_names is None:
            return
        
        # Step 2: Find corresponding columns
        column_mapping = find_matching_columns(column_names)
        
        # Step 3: Update NULL fields
        update_null_fields_dynamic(column_mapping)
        
        # Step 4: Verify update
        verify_update(column_mapping)
        
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update your Pydantic schemas to make the fields mandatory")
        print("2. Update routes to use the correct column names")
        print("3. Restart your FastAPI server")
        
    except Exception as e:
        print(f"💥 Critical error during migration: {e}")
        print("Please check your database connection and try again.")

if __name__ == "__main__":
    main()