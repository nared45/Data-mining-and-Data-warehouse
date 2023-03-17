from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql


app = Flask(__name__)
app.secret_key = 'data_warehouse'

# ==================================================================================
# Connet database
# def openConnection():
#     connection = pymysql.connect(host='localhost',
#                                  user='root',
#                                  password='',
#                                  database='itm_database',  # Name of database
#                                  charset='utf8',
#                                  #  cursorclass=pymysql.cursors.DictCursor
#                                  )
#     return connection
# localhost, username, password, database
# ==================================================================================

# ============================= Model =============================
# =================================================================

# ============================= Route Web =============================
# >> Not Login
@app.route("/")
def indexPage():
    return render_template('NotLogin/index.html')
# >> Login
# =====================================================================


if __name__ == "__main__":
    app.run(debug=True
    # , use_reloader=False
    )