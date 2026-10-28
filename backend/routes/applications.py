from datetime import date

import mysql.connector
from flask import Blueprint, current_app, jsonify, request

from db import get_db_connection


applications_bp = Blueprint("applications", __name__)

ALLOWED_STATUSES = {
    "Applied",
    "Interview",
    "Offer",
    "Accepted",
    "Rejected",
    "Withdrawn",
}

ALLOWED_FIELDS = {
    "company",
    "job_title",
    "status",
    "applied_date",
    "notes",
}

MAX_COMPANY_LENGTH = 150
MAX_JOB_TITLE_LENGTH = 150


# -------------------------
# Helper functions
# -------------------------

def application_to_dict(row):
    """Convert a MySQL application row into a JSON-friendly dictionary."""
    return {
        "id": row[0],
        "company": row[1],
        "job_title": row[2],
        "status": row[3],
        "applied_date": (
            row[4].isoformat()
            if row[4] is not None
            else None
        ),
        "notes": row[5],
        "created_at": (
            row[6].isoformat(sep=" ")
            if row[6] is not None
            else None
        ),
    }


def close_db(cursor, connection):
    """Safely close database resources when they exist."""
    if cursor is not None:
        try:
            cursor.close()
        except mysql.connector.Error:
            current_app.logger.exception(
                "Failed to close database cursor"
            )

    if connection is not None:
        try:
            if connection.is_connected():
                connection.close()
        except mysql.connector.Error:
            current_app.logger.exception(
                "Failed to close database connection"
            )


def rollback_transaction(connection):
    """Attempt to roll back a failed transaction."""
    if connection is not None:
        try:
            if connection.is_connected():
                connection.rollback()
        except mysql.connector.Error:
            current_app.logger.exception(
                "Failed to roll back transaction"
            )


def get_json_object():
    """Require a valid JSON object as the request body."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, (
            jsonify({
                "error": "Request body must be a valid JSON object"
            }),
            400,
        )

    return data, None


def parse_application_id(application_id):
    """Return a positive integer ID, or None if invalid."""
    try:
        parsed_id = int(application_id)
    except (TypeError, ValueError):
        return None

    if parsed_id <= 0:
        return None

    return parsed_id


def validate_application_fields(data, *, require_all):
    """
    Validate application fields.

    POST requires company and job_title.
    PUT requires every editable field.
    PATCH requires at least one editable field.
    """
    unknown_fields = set(data.keys()) - ALLOWED_FIELDS

    if unknown_fields:
        return None, {
            "error": "Unsupported field(s): "
            + ", ".join(sorted(unknown_fields))
        }

    if require_all:
        missing_fields = ALLOWED_FIELDS - set(data.keys())

        if missing_fields:
            return None, {
                "error": (
                    "PUT requires company, job_title, status, "
                    "applied_date, and notes"
                )
            }
    elif not data:
        return None, {
            "error": (
                "At least one field is required: company, job_title, "
                "status, applied_date, or notes"
            )
        }

    validated = {}

    # Company name
    if "company" in data:
        company = data["company"]

        if not isinstance(company, str):
            return None, {"error": "Company must be a string"}

        company = company.strip()

        if not company:
            return None, {"error": "Company is required"}

        if len(company) > MAX_COMPANY_LENGTH:
            return None, {
                "error": "Company cannot exceed 150 characters"
            }

        validated["company"] = company

    # Job title
    if "job_title" in data:
        job_title = data["job_title"]

        if not isinstance(job_title, str):
            return None, {"error": "Job title must be a string"}

        job_title = job_title.strip()

        if not job_title:
            return None, {"error": "Job title is required"}

        if len(job_title) > MAX_JOB_TITLE_LENGTH:
            return None, {
                "error": "Job title cannot exceed 150 characters"
            }

        validated["job_title"] = job_title

    # Application status
    if "status" in data:
        status = data["status"]

        if not isinstance(status, str):
            return None, {"error": "Status must be a string"}

        if status not in ALLOWED_STATUSES:
            return None, {
                "error": (
                    "Status must be Applied, Interview, Offer, "
                    "Accepted, Rejected, or Withdrawn"
                )
            }

        validated["status"] = status

    # Applied date: accept YYYY-MM-DD or null.
    if "applied_date" in data:
        applied_date = data["applied_date"]

        if applied_date is None:
            validated["applied_date"] = None
        elif not isinstance(applied_date, str):
            return None, {
                "error": "Applied date must be YYYY-MM-DD or null"
            }
        else:
            try:
                parsed_date = date.fromisoformat(applied_date)
            except ValueError:
                return None, {
                    "error": (
                        "Applied date must be a valid date in "
                        "YYYY-MM-DD format"
                    )
                }

            # Require the exact ISO date format.
            if parsed_date.isoformat() != applied_date:
                return None, {
                    "error": (
                        "Applied date must be in YYYY-MM-DD format"
                    )
                }

            validated["applied_date"] = parsed_date

    # Notes: accept a string or null.
    if "notes" in data:
        notes = data["notes"]

        if notes is not None and not isinstance(notes, str):
            return None, {
                "error": "Notes must be a string or null"
            }

        validated["notes"] = notes

    return validated, None


def fetch_application(cursor, application_id):
    """Fetch one application and convert it to a dictionary."""
    cursor.execute(
        """
        SELECT
            id,
            company,
            job_title,
            status,
            applied_date,
            notes,
            created_at
        FROM applications
        WHERE id = %s
        """,
        (application_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return application_to_dict(row)


# -------------------------
# GET all applications
# -------------------------

@applications_bp.route("/api/applications", methods=["GET"])
def get_applications():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                company,
                job_title,
                status,
                applied_date,
                notes,
                created_at
            FROM applications
            ORDER BY id ASC
            """
        )

        rows = cursor.fetchall()

        return jsonify([
            application_to_dict(row)
            for row in rows
        ]), 200

    except mysql.connector.Error:
        current_app.logger.exception(
            "Failed to retrieve applications"
        )

        return jsonify({
            "error": "Unable to retrieve applications"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# GET one application
# -------------------------

@applications_bp.route(
    "/api/applications/<application_id>",
    methods=["GET"],
)
def get_application(application_id):
    parsed_id = parse_application_id(application_id)

    if parsed_id is None:
        return jsonify({
            "error": "Application ID must be a positive integer"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        application = fetch_application(cursor, parsed_id)

        if application is None:
            return jsonify({
                "error": "Application not found"
            }), 404

        return jsonify(application), 200

    except mysql.connector.Error:
        current_app.logger.exception(
            "Failed to retrieve application"
        )

        return jsonify({
            "error": "Unable to retrieve application"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# POST a new application
# -------------------------

@applications_bp.route("/api/applications", methods=["POST"])
def create_application():
    data, error_response = get_json_object()

    if error_response:
        return error_response

    # The database default handles status when it is omitted.
    if "company" not in data or "job_title" not in data:
        return jsonify({
            "error": "Company and job_title are required"
        }), 400

    validated, validation_error = validate_application_fields(
        data,
        require_all=False,
    )

    if validation_error:
        return jsonify(validation_error), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Include only supplied fields so MySQL can apply defaults.
        columns = list(validated.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(columns)
        values = tuple(validated[column] for column in columns)

        cursor.execute(
            f"""
            INSERT INTO applications ({column_sql})
            VALUES ({placeholders})
            """,
            values,
        )

        connection.commit()
        new_id = cursor.lastrowid

        application = fetch_application(cursor, new_id)

        if application is None:
            current_app.logger.error(
                "Created application %s could not be retrieved",
                new_id,
            )
            return jsonify({
                "error": "Application was created but could not be retrieved"
            }), 500

        return jsonify(application), 201

    except mysql.connector.Error:
        rollback_transaction(connection)
        current_app.logger.exception(
            "Failed to create application"
        )

        return jsonify({
            "error": "Unable to create application"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# PUT: replace application details
# -------------------------

@applications_bp.route(
    "/api/applications/<application_id>",
    methods=["PUT"],
)
def replace_application(application_id):
    parsed_id = parse_application_id(application_id)

    if parsed_id is None:
        return jsonify({
            "error": "Application ID must be a positive integer"
        }), 400

    data, error_response = get_json_object()

    if error_response:
        return error_response

    validated, validation_error = validate_application_fields(
        data,
        require_all=True,
    )

    if validation_error:
        return jsonify(validation_error), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM applications WHERE id = %s",
            (parsed_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Application not found"
            }), 404

        cursor.execute(
            """
            UPDATE applications
            SET
                company = %s,
                job_title = %s,
                status = %s,
                applied_date = %s,
                notes = %s
            WHERE id = %s
            """,
            (
                validated["company"],
                validated["job_title"],
                validated["status"],
                validated["applied_date"],
                validated["notes"],
                parsed_id,
            ),
        )

        connection.commit()

        application = fetch_application(cursor, parsed_id)

        if application is None:
            return jsonify({
                "error": "Application not found"
            }), 404

        return jsonify(application), 200

    except mysql.connector.Error:
        rollback_transaction(connection)
        current_app.logger.exception(
            "Failed to replace application"
        )

        return jsonify({
            "error": "Unable to update application"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# PATCH: update selected fields
# -------------------------

@applications_bp.route(
    "/api/applications/<application_id>",
    methods=["PATCH"],
)
def update_application(application_id):
    parsed_id = parse_application_id(application_id)

    if parsed_id is None:
        return jsonify({
            "error": "Application ID must be a positive integer"
        }), 400

    data, error_response = get_json_object()

    if error_response:
        return error_response

    validated, validation_error = validate_application_fields(
        data,
        require_all=False,
    )

    if validation_error:
        return jsonify(validation_error), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM applications WHERE id = %s",
            (parsed_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Application not found"
            }), 404

        updates = []
        values = []

        for field in ALLOWED_FIELDS:
            if field in validated:
                updates.append(f"{field} = %s")
                values.append(validated[field])

        values.append(parsed_id)

        query = (
            "UPDATE applications SET "
            + ", ".join(updates)
            + " WHERE id = %s"
        )

        cursor.execute(query, tuple(values))
        connection.commit()

        application = fetch_application(cursor, parsed_id)

        if application is None:
            return jsonify({
                "error": "Application not found"
            }), 404

        return jsonify(application), 200

    except mysql.connector.Error:
        rollback_transaction(connection)
        current_app.logger.exception(
            "Failed to update application"
        )

        return jsonify({
            "error": "Unable to update application"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# DELETE an application
# -------------------------

@applications_bp.route(
    "/api/applications/<application_id>",
    methods=["DELETE"],
)
def delete_application(application_id):
    parsed_id = parse_application_id(application_id)

    if parsed_id is None:
        return jsonify({
            "error": "Application ID must be a positive integer"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM applications WHERE id = %s",
            (parsed_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Application not found"
            }), 404

        cursor.execute(
            "DELETE FROM applications WHERE id = %s",
            (parsed_id,),
        )

        connection.commit()

        return jsonify({
            "message": "Application deleted successfully",
            "id": parsed_id,
        }), 200

    except mysql.connector.Error:
        rollback_transaction(connection)
        current_app.logger.exception(
            "Failed to delete application"
        )

        return jsonify({
            "error": "Unable to delete application"
        }), 500

    finally:
        close_db(cursor, connection)