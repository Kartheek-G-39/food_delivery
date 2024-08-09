from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Deletes the "code" field from the specified table.'

    def handle(self, *args, **options):
        table_name = 'core_restaurant'  # Replace with your actual table name
        column_name = 'code'

        with connection.cursor() as cursor:
            # Check if the column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            if column_name not in columns:
                self.stdout.write(self.style.ERROR(f'Column "{column_name}" does not exist in table "{table_name}".'))
                return

            # Create a new table without the column to delete
            cursor.execute(f"""
                CREATE TABLE {table_name}_new AS
                SELECT * FROM {table_name} WHERE 1=0
            """)

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall() if row[1] != column_name]

            column_definitions = ", ".join(columns)
            cursor.execute(f"""
                INSERT INTO {table_name}_new ({column_definitions})
                SELECT {column_definitions} FROM {table_name}
            """)

            # Drop the original table
            cursor.execute(f"DROP TABLE {table_name}")

            # Rename the new table to the original name
            cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

            self.stdout.write(self.style.SUCCESS(f'Column "{column_name}" successfully deleted from table "{table_name}".'))
