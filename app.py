from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Homepage route
@app.route('/')
def home():
    return render_template('home.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Here you can add authentication logic (e.g., check against a database)
        return redirect(url_for('home'))  # Redirect to homepage after login
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Here you can add registration logic (e.g., save to a database)
        return redirect(url_for('login'))  # Redirect to login after registration
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
