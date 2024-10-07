from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '6243'
app.config['MYSQL_DB'] = 'library_db'

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    connection = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        return User(user[0], user[1], user[3])  # (id, username, role)
    return None


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        connection = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            connection.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        connection = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        # Check if user exists
        if user is None:
            flash('User does not exist. Please register first.', 'danger')
        elif check_password_hash(user[2], password):  # user[2] is the hashed password
            user_obj = User(user[0], user[1], user[3])
            login_user(user_obj)
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/user_dashboard')
@login_required
def user_dashboard():
    connection = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
    cursor = connection.cursor()

    # Fetch all available books
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    # Fetch borrowed books by the current user
    cursor.execute(
        "SELECT b.id, b.title, b.author FROM borrowed_books bb JOIN books b ON bb.book_id = b.id WHERE bb.user_id = %s",
        (current_user.id,))
    borrowed_books = cursor.fetchall()

    cursor.close()
    connection.close()
    return render_template('user_dashboard.html', books=books, borrowed_books=borrowed_books)


@app.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow(book_id):
    connection = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
    cursor = connection.cursor()
    cursor.execute("SELECT available FROM books WHERE id = %s", (book_id,))
    available = cursor.fetchone()[0]

    if available > 0:
        cursor.execute("UPDATE books SET available = available - 1 WHERE id = %s", (book_id,))
        cursor.execute("INSERT INTO borrowed_books (user_id, book_id) VALUES (%s, %s)", (current_user.id, book_id))
        connection.commit()
        flash('Book borrowed successfully!', 'success')
    else:
        flash('Book is not available.', 'danger')

    cursor.close()
    connection.close()
    return redirect(url_for('user_dashboard'))


@app.route('/return/<int:book_id>', methods=['POST'])
@login_required
def return_book(book_id):
    connection = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
    cursor = connection.cursor()

    cursor.execute("DELETE FROM borrowed_books WHERE user_id = %s AND book_id = %s", (current_user.id, book_id))
    cursor.execute("UPDATE books SET available = available + 1 WHERE id = %s", (book_id,))
    connection.commit()
    cursor.close()
    connection.close()

    flash('Book returned successfully!', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
