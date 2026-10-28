import mysql.connector
from flask import Blueprint, current_app, jsonify, request

from db import get_db_connection

goals_bp = Blueprint("goals", __name__)


def goal_to_dict(row):
    """Convert a MySQL goal row into a JSON-friendly dictionary."""
    return {
        "id": row[0],
        "title": row[1],
        "completed": bool(row[2]),
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
            current_app.logger.exception("Failed to close database cursor")

    if connection is not None:
        try:
            if connection.is_connected():
                connection.close()
        except mysql.connector.Error:
            current_app.logger.exception(
                "Failed to close database connection"
            )


def get_json_object():
    """Return a JSON object or a validation error response."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, (
            jsonify({
                "error": "Request body must be a valid JSON object"
            }),
            400,
        )

    return data, None


def validate_goal_fields(data, *, require_all):
    """Validate title and completed fields for PUT and PATCH."""
    allowed_fields = {"title", "completed"}
    unknown_fields = set(data.keys()) - allowed_fields

    if unknown_fields:
        return None, {
            "error": "Unsupported field(s): "
            + ", ".join(sorted(unknown_fields))
        }

    if require_all:
        missing_fields = allowed_fields - set(data.keys())

        if missing_fields:
            return None, {
                "error": "PUT requires both 'title' and 'completed' fields"
            }
    elif not data:
        return None, {
            "error": "PATCH requires at least one field: title or completed"
        }

    validated = {}

    if "title" in data:
        title = data["title"]

        if not isinstance(title, str):
            return None, {"error": "Title must be a string"}

        title = title.strip()

        if not title:
            return None, {"error": "Goal title is required"}

        if len(title) > 255:
            return None, {
                "error": "Title cannot exceed 255 characters"
            }

        validated["title"] = title

    if "completed" in data:
        completed = data["completed"]

        if not isinstance(completed, bool):
            return None, {
                "error": "Completed must be a boolean (true or false)"
            }

        validated["completed"] = completed

    return validated, None


# -------------------------
# GET all goals
# -------------------------

@goals_bp.route("/api/goals", methods=["GET"])
def get_goals():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, title, completed, created_at
            FROM goals
            ORDER BY id
            """
        )

        rows = cursor.fetchall()
        goals = [goal_to_dict(row) for row in rows]

        return jsonify(goals), 200

    except mysql.connector.Error:
        current_app.logger.exception("Failed to retrieve goals")
        return jsonify({
            "error": "Unable to retrieve goals"
        }), 500

    finally:
        close_db(cursor, connection)

# -------------------------
# POST create a goal
# -------------------------

@goals_bp.route("/api/goals", methods=["POST"])
def create_goal():
    data, error_response = get_json_object()

    if error_response:
        return error_response

    validated, error = validate_goal_fields(
        {"title": data.get("title")},
        require_all=False,
    )

    if error:
        return jsonify(error), 400

    title = validated["title"]

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO goals (title) VALUES (%s)",
            (title,),
        )
        connection.commit()

        new_goal_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT id, title, completed, created_at
            FROM goals
            WHERE id = %s
            """,
            (new_goal_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return jsonify({
                "error": "Goal was created but could not be retrieved"
            }), 500

        return jsonify(goal_to_dict(row)), 201

    except mysql.connector.Error:
        if connection is not None:
            try:
                if connection.is_connected():
                    connection.rollback()
            except mysql.connector.Error:
                current_app.logger.exception("Failed to roll back transaction")

        current_app.logger.exception("Failed to create goal")
        return jsonify({
            "error": "Unable to create goal"
        }), 500

    finally:
        close_db(cursor, connection)


# PUT replace a goal
@goals_bp.route("/api/goals/<int:goal_id>", methods=["PUT"])
def replace_goal(goal_id):
    if goal_id <= 0:
        return jsonify({
            "error": "Goal ID must be a positive integer"
        }), 400

    data, error_response = get_json_object()

    if error_response:
        return error_response

    validated, error = validate_goal_fields(
        data,
        require_all=True,
    )

    if error:
        return jsonify(error), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM goals WHERE id = %s",
            (goal_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Goal not found"
            }), 404

        cursor.execute(
            """
            UPDATE goals
            SET title = %s, completed = %s
            WHERE id = %s
            """,
            (
                validated["title"],
                validated["completed"],
                goal_id,
            ),
        )

        connection.commit()

        cursor.execute(
            """
            SELECT id, title, completed, created_at
            FROM goals
            WHERE id = %s
            """,
            (goal_id,),
        )

        row = cursor.fetchone()

        return jsonify(goal_to_dict(row)), 200

    except mysql.connector.Error:
        if connection is not None:
            try:
                if connection.is_connected():
                    connection.rollback()
            except mysql.connector.Error:
                current_app.logger.exception(
                    "Failed to roll back transaction"
                )

        current_app.logger.exception("Failed to replace goal")
        return jsonify({
            "error": "Unable to update goal"
        }), 500

    finally:
        close_db(cursor, connection)
        

# PATCH update selected fields
@goals_bp.route("/api/goals/<int:goal_id>", methods=["PATCH"])
def update_goal(goal_id):
    if goal_id <= 0:
        return jsonify({
            "error": "Goal ID must be a positive integer"
        }), 400

    data, error_response = get_json_object()

    if error_response:
        return error_response

    validated, error = validate_goal_fields(
        data,
        require_all=False,
    )

    if error:
        return jsonify(error), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM goals WHERE id = %s",
            (goal_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Goal not found"
            }), 404

        update_columns = []
        values = []

        if "title" in validated:
            update_columns.append("title = %s")
            values.append(validated["title"])

        if "completed" in validated:
            update_columns.append("completed = %s")
            values.append(validated["completed"])

        values.append(goal_id)

        sql = (
            "UPDATE goals SET "
            + ", ".join(update_columns)
            + " WHERE id = %s"
        )

        cursor.execute(sql, tuple(values))
        connection.commit()

        cursor.execute(
            """
            SELECT id, title, completed, created_at
            FROM goals
            WHERE id = %s
            """,
            (goal_id,),
        )

        row = cursor.fetchone()

        return jsonify(goal_to_dict(row)), 200

    except mysql.connector.Error:
        if connection is not None:
            try:
                if connection.is_connected():
                    connection.rollback()
            except mysql.connector.Error:
                current_app.logger.exception(
                    "Failed to roll back transaction"
                )

        current_app.logger.exception("Failed to update goal")
        return jsonify({
            "error": "Unable to update goal"
        }), 500

    finally:
        close_db(cursor, connection)


# DELETE a goal
@goals_bp.route("/api/goals/<goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    try:
        goal_id = int(goal_id)
    except ValueError:
        return jsonify({
            "error": "Goal ID must be a positive integer"
        }), 400

    if goal_id <= 0:
        return jsonify({
            "error": "Goal ID must be a positive integer"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM goals WHERE id = %s",
            (goal_id,),
        )

        if cursor.fetchone() is None:
            return jsonify({
                "error": "Goal not found"
            }), 404

        cursor.execute(
            "DELETE FROM goals WHERE id = %s",
            (goal_id,),
        )
        connection.commit()

        return jsonify({
            "message": "Goal deleted successfully",
            "id": goal_id,
        }), 200

    except mysql.connector.Error:
        if connection is not None:
            try:
                if connection.is_connected():
                    connection.rollback()
            except mysql.connector.Error:
                current_app.logger.exception(
                    "Failed to roll back transaction"
                )

        current_app.logger.exception("Failed to delete goal")
        return jsonify({
            "error": "Unable to delete goal"
        }), 500

    finally:
        close_db(cursor, connection)