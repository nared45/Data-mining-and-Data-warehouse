from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

from datetime import datetime


app = Flask(__name__)
app.secret_key = 'data_warehouse'

# ==================================================================================
# Connet database


def openConnection():
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='',
                                 database='data_warehouse',  # Name of database
                                 charset='utf8',
                                 #  cursorclass=pymysql.cursors.DictCursor
                                 )
    return connection
# localhost, username, password, database
# ==================================================================================

# ============================= Model =============================
# =================================================================

# ============================= Route Web =============================
# >> Not Login


@app.route("/")
def indexPage():
    return render_template('NotLogin/index.html')


@app.route("/register")
def registerPage():
    return render_template('NotLogin/register.html')


@app.route("/login")
def loginPage():
    return render_template('NotLogin/login.html')

# >> Login

# =====================================================================

# ============================= Action =============================


@app.route("/register/actions", methods=['POST'])
def registerAction():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']
        dateOfBirth = request.form['dateOfBirth']

        if (password == confirmPassword):
            
            # Hashed password
            hased_password = generate_password_hash(password, method='sha256')

            conn = openConnection()
            cur = conn.cursor()

            sql = "INSERT INTO `employee`(`email`, `password`, `name`, `dateOfBirth`) VALUES (%s, %s, %s, %s)"
            cur.execute(sql, (email, hased_password, name, dateOfBirth))
            conn.commit()
            conn.close()

            flash("Register Success", "success")
            return redirect(url_for('loginPage'))
        else:
            flash("Password and Confirm Password Don't Match", "danger")
            return redirect(url_for('registerPage'))


# ==================================================================


if __name__ == "__main__":
    app.run(debug=True
            # , use_reloader=False
            )
