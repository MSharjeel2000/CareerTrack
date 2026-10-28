import mysql.connector
from flask import Blueprint, current_app, jsonify, request

from db import get_db_connection


skills_bp = Blueprint("skills", __name__)

ALLOWED_LEVELS = {"Beginner", "Intermediate", "Advanced"}
ALLOWED_FIELDS = {"name", "level"}


# -------------------------
# Helper functions
# -------------------------

def skill_to_dict(row):
    """Convert a MySQL skill row into a JSON-friendly dictionary."""
    return {
        "id": row[0],
        "name": row[1],
        "level": row[2],
        "created_at": (
            row[3].isoformat(sep=" ")
            if row[3] is not None
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


def validate_skill_fields(data, *, require_all):
    """
    Validate skill name and proficiency level.

    PUT requires both fields.
    PATCH requires at least one field.
    POST requires name and defaults level to Beginner.
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
                "error": "PUT requires both 'name' and 'level' fields"
            }

    elif not data:
        return None, {
            "error": "At least one field is required: name or level"
        }

    validated = {}

    if "name" in data:
        name = data["name"]

        if not isinstance(name, str):
            return None, {"error": "Skill name must be a string"}

        name = name.strip()

        if not name:
            return None, {"error": "Skill name is required"}

        if len(name) > 100:
            return None, {
                "error": "Skill name cannot exceed 100 characters"
            }

        validated["name"] = name

    if "level" in data:
        level = data["level"]

        if not isinstance(level, str):
            return None, {"error": "Skill level must be a string"}

        if level not in ALLOWED_LEVELS:
            return None, {
                "error": (
                    "Skill level must be Beginner, Intermediate, "
                    "or Advanced"
                )
            }

        validated["level"] = level

    return validated, None


def parse_skill_id(skill_id):
    """Convert and validate a positive integer skill ID."""
    try:
        parsed_id = int(skill_id)
    except (TypeError, ValueError):
        return None

    if parsed_id <= 0:
        return None

    return parsed_id


def rollback_transaction(connection):
    """Attempt to roll back a failed database transaction."""
    if connection is not None:
        try:
            if connection.is_connected():
                connection.rollback()
        except mysql.connector.Error:
            current_app.logger.exception(
                "Failed to roll back transaction"
            )


# -------------------------
# GET all skills
# -------------------------

@skills_bp.route("/api/skills", methods=["GET"])
def get_skills():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, level, created_at
            FROM skills
            ORDER BY id ASC
            """
        )

        rows = cursor.fetchall()

        return jsonify([skill_to_dict(row) for row in rows]), 200

    except mysql.connector.Error:
        current_app.logger.exception("Failed to retrieve skills")

        return jsonify({
            "error": "Unable to retrieve skills"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# GET one skill
# -------------------------

@skills_bp.route("/api/skills/<skill_id>", methods=["GET"])
def get_skill(skill_id):
    parsed_id = parse_skill_id(skill_id)

    if parsed_id is None:
        return jsonify({
            "error": "Skill ID must be a positive integer"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, level, created_at
            FROM skills
            WHERE id = %s
            """,
            (parsed_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return jsonify({
                "error": "Skill not found"
            }), 404

        return jsonify(skill_to_dict(row)), 200

    except mysql.connector.Error:
        current_app.logger.exception("Failed to retrieve skill")

        return jsonify({
            "error": "Unable to retrieve skill"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# POST a new skill
# -------------------------

@skills_bp.route("/api/skills", methods=["POST"])
def create_skill():
    data, error_response = get_json_object()

    if error_response:
        return error_response

    # POST requires a name; level defaults to Beginner.
    if "name" not in data:
        return jsonify({
            "error": "Skill name is required"
        }), 400

    data_with_default = {
        **data,
        "level": data.get("level", "Beginner"),
    }

    validated, validation_error = validate_skill_fields(
        data_with_default,
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
            """
            INSERT INTO skills (name, level)
            VALUES (%s, %s)
            """,
            (validated["name"], validated["level"]),
        )

        connection.commit()
        new_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT id, name, level, created_at
            FROM skills
            WHERE id = %s
            """,
            (new_id,),
        )

        row = cursor.fetchone()

        return jsonify(skill_to_dict(row)), 201

    except mysql.connector.IntegrityError as exc:
        rollback_transaction(connection)

        if exc.errno == 1062:
            return jsonify({
                "error": "A skill with this name already exists"
            }), 409

        current_app.logger.exception(
            "Database integrity error while creating skill"
        )

        return jsonify({
            "error": "Unable to create skill"
        }), 500

    except mysql.connector.Error:
        rollback_transaction(connection)
        current_app.logger.exception("Failed to create skill")

        return jsonify({
            "error": "Unable to create skill"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# PUT: replace skill details
# -------------------------

@skills_bp.route("/api/skills/<skill_id>", methods=["PUT"])
def replace_skill(skill_id):
    parsed_id = parse_skill_id(skill_id)

    if parsed_id is None:
        return jsonify({
            "error": "Skill ID must be a positive integer"
        }), 400

    data, error_response = get_json_object()

    if error_response:
        return error_response

    validated, validation_error = validate_skill_fields(
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
            "SELECT id FROM skills WHERE id = %s",
            (parsed_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Skill not found"
            }), 404

        cursor.execute(
            """
            UPDATE skills
            SET name = %s, level = %s
            WHERE id = %s
            """,
            (
                validated["name"],
                validated["level"],
                parsed_id,
            ),
        )

        connection.commit()

        cursor.execute(
            """
            SELECT id, name, level, created_at
            FROM skills
            WHERE id = %s
            """,
            (parsed_id,),
        )

        row = cursor.fetchone()

        return jsonify(skill_to_dict(row)), 200

    except mysql.connector.IntegrityError as exc:
        rollback_transaction(connection)

        if exc.errno == 1062:
            return jsonify({
                "error": "A skill with this name already exists"
            }), 409

        current_app.logger.exception(
            "Database integrity error while replacing skill"
        )

        return jsonify({
            "error": "Unable to update skill"
        }), 500

    except mysql.connector.Error:
        rollback_transaction(connection)
        current_app.logger.exception("Failed to replace skill")

        return jsonify({
            "error": "Unable to update skill"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# PATCH: update selected fields
# -------------------------

@skills_bp.route("/api/skills/<skill_id>", methods=["PATCH"])
def update_skill(skill_id):
    parsed_id = parse_skill_id(skill_id)

    if parsed_id is None:
        return jsonify({
            "error": "Skill ID must be a positive integer"
        }), 400

    data, error_response = get_json_object()

    if error_response:
        return error_response

    validated, validation_error = validate_skill_fields(
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
            "SELECT id FROM skills WHERE id = %s",
            (parsed_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Skill not found"
            }), 404

        updates = []
        values = []

        if "name" in validated:
            updates.append("name = %s")
            values.append(validated["name"])

        if "level" in validated:
            updates.append("level = %s")
            values.append(validated["level"])

        values.append(parsed_id)

        query = (
            "UPDATE skills SET "
            + ", ".join(updates)
            + " WHERE id = %s"
        )

        cursor.execute(query, tuple(values))
        connection.commit()

        cursor.execute(
            """
            SELECT id, name, level, created_at
            FROM skills
            WHERE id = %s
            """,
            (parsed_id,),
        )

        row = cursor.fetchone()

        return jsonify(skill_to_dict(row)), 200

    except mysql.connector.IntegrityError as exc:
        rollback_transaction(connection)

        if exc.errno == 1062:
            return jsonify({
                "error": "A skill with this name already exists"
            }), 409

        current_app.logger.exception(
            "Database integrity error while updating skill"
        )

        return jsonify({
            "error": "Unable to update skill"
        }), 500

    except mysql.connector.Error:
        rollback_transaction(connection)
        current_app.logger.exception("Failed to update skill")

        return jsonify({
            "error": "Unable to update skill"
        }), 500

    finally:
        close_db(cursor, connection)


# -------------------------
# DELETE a skill
# -------------------------

@skills_bp.route("/api/skills/<skill_id>", methods=["DELETE"])
def delete_skill(skill_id):
    parsed_id = parse_skill_id(skill_id)

    if parsed_id is None:
        return jsonify({
            "error": "Skill ID must be a positive integer"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM skills WHERE id = %s",
            (parsed_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Skill not found"
            }), 404

        cursor.execute(
            "DELETE FROM skills WHERE id = %s",
            (parsed_id,),
        )

        connection.commit()

        return jsonify({
            "message": "Skill deleted successfully",
            "id": parsed_id,
        }), 200

    except mysql.connector.Error:
        rollback_transaction(connection)
        current_app.logger.exception("Failed to delete skill")

        return jsonify({
            "error": "Unable to delete skill"
        }), 500

    finally:
        close_db(cursor, connection)