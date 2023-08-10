import sqlite3
import threading
from typing import Dict


class SQLiteDB:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SQLiteDB, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, db_name: str = "/Users/mb0390231/Desktop/RGM/GOHIGHLEVELAUTH/oauth_flask/database.db"):
        self.local_storage = threading.local()
        self.db_name = db_name

    @property
    def conn(self):
        if not hasattr(self.local_storage, "conn"):
            self.local_storage.conn = sqlite3.connect(self.db_name)
            self.create_table()
        return self.local_storage.conn

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS api_data (
                    userType TEXT,
                    companyId TEXT,
                    locationId TEXT PRIMARY KEY,  
                    access_token TEXT,
                    token_type TEXT,
                    expires_in INTEGER,
                    refresh_token TEXT,
                    scope TEXT
                );
            """
        )
        self.conn.commit()

    def insert_or_update_token(self, data: Dict):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO api_data (userType, companyId, locationId, access_token, token_type, expires_in, refresh_token, scope) 
            VALUES (:userType, :companyId, :locationId, :access_token, :token_type, :expires_in, :refresh_token, :scope)
            ON CONFLICT(locationId) 
            DO UPDATE SET 
                userType = excluded.userType,
                companyId = excluded.companyId,
                access_token = excluded.access_token,
                token_type = excluded.token_type,
                expires_in = excluded.expires_in,
                refresh_token = excluded.refresh_token,
                scope = excluded.scope
            """,
            {
                "userType": data["userType"],
                "companyId": data["companyId"],
                "locationId": data["locationId"],
                "access_token": data["access_token"],
                "token_type": data["token_type"],
                "expires_in": data["expires_in"],
                "refresh_token": data["refresh_token"],
                "scope": data["scope"],
            },
        )
        self.conn.commit()
        print(f"Updated access token for locationId: {data['locationId']}")

    def fetch_all_records(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()

    def fetch_single_record(self, table_name, column_name, value):
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM {table_name} WHERE {column_name} = "{value}"')
        return cursor.fetchone()

    def fetch_single_column(self, table_name, column_retreived, column_query, value):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT {column_retreived} FROM {table_name} WHERE {column_query} = '{value}'")
        return cursor.fetchone()

    def insert_many_retailer_records(self, mds_data):
        # insert location id and mds_link into rgm_retailers table
        query = "INSERT INTO rgm_retailers (locationId, lds_link) VALUES (?, ?) ON CONFLICT (locationId) DO UPDATE SET lds_link = EXCLUDED.lds_link;"
        cursor = self.conn.cursor()
        cursor.executemany(query, mds_data)
        self.conn.commit()
        print(f"Updated {cursor.rowcount} records in rgm_retailers table")
        return True

    def insert_many_contacts(self, contact_data):
        # insert id", "locationId", "email","timezone", "firstName", "lastName", "contactName", and "phone" into the rgm_contacts table
        query = "INSERT INTO rgm_contacts (id, locationId, email, timezone, firstName, lastName, contactName, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET locationId = EXCLUDED.locationId, email = EXCLUDED.email, timezone = EXCLUDED.timezone, firstName = EXCLUDED.firstName, lastName = EXCLUDED.lastName, contactName = EXCLUDED.contactName, phone = EXCLUDED.phone;"
        cursor = self.conn.cursor()
        # format contact_data from list of objects to list of tuples
        formatted_contact_data = []
        for contact in contact_data:
            formatted_contact_data.append(
                (
                    contact.get("id", None),
                    contact.get("locationId", None),
                    contact.get("email", None),
                    contact.get("timezone", None),
                    contact.get("firstName", None),
                    contact.get("lastName", None),
                    contact.get("contactName", None),
                    contact.get("phone", None),
                )
            )

        cursor.executemany(query, formatted_contact_data)
        print(f"Added/Updated {cursor.rowcount} records in rgm_contacts table")
        self.conn.commit()
        return True

    def attempt_contact_retrieval(self, phone_number, email, first_name, last_name):
        query = f"""
            SELECT *
            FROM rgm_contacts
            WHERE phone = ? OR email = ?
            OR (phone IS NULL AND email IS NULL AND (firstName = ? AND lastName = ?));
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (phone_number, email, first_name, last_name))

        # Fetch the results
        results = cursor.fetchall()

        # if there are no records, return None
        if len(results) == 0:
            return None
        # if there are multiple records, return None
        elif len(results) > 1:
            return None

        return results[0]
