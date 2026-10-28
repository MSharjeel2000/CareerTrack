import os
import mysql.connector


def get_db_connection():
    connection_settings = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
    }

    # Enable TLS certificate verification for cloud databases.
    if os.getenv("DB_SSL", "false").lower() == "true":
        connection_settings.update({
            "ssl_ca": "/etc/ssl/certs/ca-certificates.crt",
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
        })

    return mysql.connector.connect(**connection_settings)