import sqlite3
import os
from pathlib import Path
import secrets # For generating secure tokens

# Define the database path relative to this script's directory (src/db)
DATABASE_DIR = Path(__file__).resolve().parent # The directory containing this file
DATABASE_PATH = DATABASE_DIR / "subscribers.db"

def init_db():
    """Initializes the database and creates the subscribers table if it doesn't exist."""
    # No need to create the directory as it's the script's own directory
    # os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = None
    # Explicitly print the path being used
    db_path_str = str(DATABASE_PATH.resolve())
    print(f"[init_db] Attempting to connect/create DB at: {db_path_str}")
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # Create table should be sufficient if DB file is deleted
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                email TEXT PRIMARY KEY UNIQUE NOT NULL,
                confirmed BOOLEAN DEFAULT FALSE NOT NULL,
                confirmation_token TEXT UNIQUE
            )
        """)
        # --- Temporarily commented out ALTER TABLE logic ---
        # try:
        #     cursor.execute("ALTER TABLE subscribers ADD COLUMN confirmed BOOLEAN DEFAULT FALSE NOT NULL")
        # except sqlite3.OperationalError:
        #     pass # Column already exists
        # try:
        #     cursor.execute("ALTER TABLE subscribers ADD COLUMN confirmation_token TEXT UNIQUE")
        # except sqlite3.OperationalError:
        #     pass # Column already exists
        # --- End of commented out block ---

        conn.commit()
        print("[init_db] Database initialized successfully.")

        # --- Verify Schema --- 
        try:
            # Reconnect briefly to verify schema immediately after creation
            # Use the connection that was just used to create the table
            cursor.execute("PRAGMA table_info(subscribers);")
            columns = cursor.fetchall()
            print("[init_db] Verifying schema for 'subscribers' table:")
            for col in columns:
                print(f"  - {col}") # Prints tuple: (id, name, type, notnull, default_value, pk)
        except sqlite3.Error as e:
            print(f"[init_db] Error verifying schema: {e}")
        # --- End Verification ---

    except sqlite3.Error as e:
        print(f"[init_db] Database error during initialization: {e}") # Added prefix
    finally:
        if conn:
            conn.close()

def add_subscriber(email: str) -> tuple[bool, str]:
    """Adds a new subscriber email to the database.

    Args:
        email: The email address to add.

    Returns:
        A tuple containing:
        - bool: True if the subscriber was added successfully, False otherwise.
        - str: A message indicating the result (success, already exists, or error).
    """
    conn = None
    confirmation_token = secrets.token_urlsafe(32) # Generate a secure token
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # Insert email with confirmed=False and the generated token
        cursor.execute(
            "INSERT INTO subscribers (email, confirmed, confirmation_token) VALUES (?, ?, ?)",
            (email, False, confirmation_token)
        )
        conn.commit()
        # Return success and the token (so it can potentially be used immediately, e.g., for sending email)
        return True, f"Successfully subscribed. Confirmation required. Token: {confirmation_token}" # Modified message
    except sqlite3.IntegrityError:
        # Check if the existing user is already confirmed
        cursor.execute("SELECT confirmed FROM subscribers WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result and result[0]: # If confirmed is True
             return False, "Email already subscribed and confirmed."
        else:
             # Potentially re-send confirmation or just indicate it exists but isn't confirmed
             # For now, we just signal it exists. Resending logic could be added.
             return False, "Email already subscribed, confirmation pending."
    except sqlite3.Error as e:
        print(f"Database error adding subscriber: {e}")
        return False, f"An error occurred: {e}"
    finally:
        if conn:
            conn.close()

def remove_subscriber(email: str) -> tuple[bool, str]:
    """Removes a subscriber email from the database.

    Args:
        email: The email address to remove.

    Returns:
        A tuple containing:
        - bool: True if the subscriber was removed successfully, False otherwise.
        - str: A message indicating the result (success, not found, or error).
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # Execute the DELETE statement
        cursor.execute("DELETE FROM subscribers WHERE email = ?", (email,))
        conn.commit()
        # Check if any row was actually deleted
        if cursor.rowcount > 0:
            return True, "Successfully unsubscribed."
        else:
            # No rows affected means the email wasn't in the database
            return False, "Email not found."
    except sqlite3.Error as e:
        print(f"Database error removing subscriber: {e}")
        return False, f"An error occurred: {e}"
    finally:
        if conn:
            conn.close()

def confirm_subscriber(token: str) -> tuple[bool, str]:
    """Confirms a subscriber using their confirmation token.

    Args:
        token: The confirmation token.

    Returns:
        A tuple containing:
        - bool: True if confirmation was successful, False otherwise.
        - str: A message indicating the result (success, invalid token, or error).
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # Find the user by token, set confirmed to True, and clear the token
        cursor.execute(
            "UPDATE subscribers SET confirmed = ?, confirmation_token = NULL WHERE confirmation_token = ?",
            (True, token)
        )
        conn.commit()
        # Check if any row was updated
        if cursor.rowcount > 0:
            return True, "Email confirmed successfully."
        else:
            # No rows affected means the token was invalid or already used
            return False, "Invalid or expired confirmation token."
    except sqlite3.Error as e:
        print(f"Database error confirming subscriber: {e}")
        return False, f"An error occurred: {e}"
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Example usage: Initialize DB when script is run directly
    print(f"Database path: {DATABASE_PATH}")
    init_db()
    # Example adding a subscriber
    # success, message = add_subscriber("test@example.com")
    # print(f"Adding test@example.com: {success}, {message}")
    # success, message = add_subscriber("test@example.com") # Try adding again
    # print(f"Adding test@example.com again: {success}, {message}") 