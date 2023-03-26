from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

from datetime import datetime
# ==================================================================================
# Model
import os
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib
import pickle
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = 'data_warehouse'

# ==================================================================================
# load model
# with open('C:/Cassava-Disease-Classification-Using-Line-BOT/Data-mining-and-Data-warehouse/Model_V2/decision_tree_model_feature_selection.pkl', 'rb') as f:
#     clf = pickle.load(f)

clf = joblib.load('C:/Flask_application/model/decision_tree_model_feature_selection.pkl')

def openConnection():
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='',
                                 database='data_warehouseV2',  # Name of database
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

@app.route("/aboutUs")
def aboutUsPage():
    return render_template('NotLogin/aboutUs.html')

# >> Login

@app.route("/<string:id>/name/<string:name>")
def loginFormPage(id, name):
    if 'login' in session:
        return render_template('Login/form.html', data_id = id, data_name = name)
    else :
        return redirect(url_for('indexPage'))
    
@app.route("/<string:id>/name/<string:name>/decide/name/<string:customerName>/loanAmount/<string:customerLoanAmount>/loanAmountTerm/<string:customerLoanAmountTerm>/reason/<string:reason>/status/<string:status>/loan_id/<string:loan_id>")
def loginDecideFormPage(id, name, customerName, customerLoanAmount, customerLoanAmountTerm, reason, status, loan_id):
    if 'login' in session:
        reason = reason.replace('[', '').replace(']', '').replace("'", '')
        reason = reason.split(',')
        return render_template('Login/decide.html', data_id = id, data_name = name, customerName = customerName, customerLoanAmount = customerLoanAmount, customerLoanAmountTerm = customerLoanAmountTerm, reason = reason, status= status, loan_id = loan_id)
    else :
        return redirect(url_for('indexPage'))
# =====================================================================

# ============================= Action =============================

@app.route('/logout')
def logout():
    session.pop('login', None)
    return redirect(url_for('indexPage'))

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
        
@app.route("/login/actions", methods=['POST'])
def loginAction():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        conn = openConnection()
        cur = conn.cursor()
        sql = "SELECT * FROM `employee` WHERE employee.email = %s"
        cur.execute(sql, (email))
        result = cur.fetchone()
        conn.close()
        if result == None :
            flash("Don't have this User in database", "danger")
            return redirect(url_for('loginPage'))
        else :
            if result and check_password_hash(result[2], password):
                session['login'] = result[1]
                return redirect(url_for('loginFormPage', id = result[0], name = result[3]))
            else :
                flash("Please check your password", "warning")
                return redirect(url_for('loginPage'))

def extract_rules(tree, feature_names):
    left = tree.tree_.children_left
    right = tree.tree_.children_right
    threshold = tree.tree_.threshold
    features = [feature_names[i] for i in tree.tree_.feature]
    # print(f"left: {left}")
    # print(f"right: {right}")
    # print(f"threshold: {threshold}")
    # print(f"features: {features}")

    def recurse(left, right, threshold, features, node, rules):
        if threshold[node] != -2:
            rules.append((features[node], threshold[node]))
            left_rules = recurse(left, right, threshold, features, left[node], [])
            right_rules = recurse(left, right, threshold, features, right[node], [])
            return rules + left_rules + right_rules
        else:
            return rules
    return recurse(left, right, threshold, features, 0, [])

def predict_loan_approval(inputs):
    # new_data = inputs[['Credit_History', 'LoanAmount', 'ApplicantIncome', 'CoapplicantIncome', 'Dependents']]
    # new_data.loc[:, 'Dependents'] = new_data['Dependents'].apply(lambda x : {'0' : 0, '1' : 1, '2' : 2, '3+' : 3}[x])
    new_data = inputs
    # print(new_data['Dependents'])
    # new_data['Dependents'] = new_data['Dependents'].apply(lambda x : {'0' : 0, '1' : 1, '2' : 2, '3+' : 3}[x])


    y_pred = clf.predict(new_data.values)
    
    print(y_pred)
    
    # Extract the decision path and rules
    decision_path = clf.decision_path(new_data)

    # print(f"decision_path: {decision_path}")

    rules = extract_rules(clf, new_data.columns)

    # print(f"rule: {rules}")

    reasons = []
    met_conditions = []
    flags = {'Credit_History': False, 'ApplicantIncome': False, 'LoanAmount': False, 'CoapplicantIncome': False, 'Dependents': False}
    

    for rule in rules:
        feature, threshold = rule
        value = new_data.iloc[0][feature]

        if feature == 'Credit_History' and float(value) < float(threshold) and not flags[feature]:
            flags[feature] = True
            reasons.append('Customer does not meet credit history requirement.')
        elif feature == 'ApplicantIncome' and float(value) < float(threshold) and not flags[feature]:
            flags[feature] = True
            reasons.append('Customer does not meet income requirement.')
        elif feature == 'LoanAmount' and float(value) > float(threshold) and not flags[feature]:
            flags[feature] = True
            reasons.append('Customer exceeds loan amount requirement.')
        elif feature == 'CoapplicantIncome' and float(value) < float(threshold) and not flags[feature]:
            flags[feature] = True
            reasons.append('Customer does not meet coapplicant income requirement.')
        elif feature == 'Dependents' and float(value) > float(threshold) and not flags[feature]:
            flags[feature] = True
            reasons.append('Customer has too many dependents.')
        elif not flags[feature]:
            flags[feature] = True
            if feature == 'Credit_History':
                met_conditions.append('Customer meets credit history requirement.')
            elif feature == 'ApplicantIncome':
                met_conditions.append('Customer meets income requirement.')
            elif feature == 'LoanAmount':
                met_conditions.append('Customer meets loan amount requirement.')
            elif feature == 'CoapplicantIncome':
                met_conditions.append('Customer meets coapplicant income requirement.')
            elif feature == 'Dependents':
                met_conditions.append('Customer meets dependents requirement.')

    return y_pred[0], reasons, met_conditions

@app.route("/<string:id>/name/<string:loginName>/decide", methods=['POST'])
def decideFormPage(id, loginName):
    if 'login' in session:
        inputs = []
        customerName = request.form['customername']
        customerSurname = request.form['customersurname']
        customerAge = request.form['customerage']
        customerPhone = request.form['customerphonenumber']
        customerSelfEmployed= request.form['selfEmployed']
        customerLoanAmountTerm = request.form['loanAmountTerm']
        customerGender = request.form['gender']
        customerMarried = request.form['Married']
        customerEducation = request.form['education']
        customerPropertyArea = request.form['propertyArea']
        customerCreditHistory = request.form['creditHistory']
        customerCreditHistory = float(customerCreditHistory)
        inputs.append(customerCreditHistory)
        customerLoanAmount = request.form['loanAmount']
        customerLoanAmount = float(customerLoanAmount)
        inputs.append(customerLoanAmount)
        customerApplicantIncome = request.form['applicantIncome']
        customerApplicantIncome = int(customerApplicantIncome)
        inputs.append(customerApplicantIncome)
        customerCoapplicantIncome = request.form['coapplicantIncome']
        customerCoapplicantIncome = int(customerCoapplicantIncome)
        inputs.append(customerCoapplicantIncome)
        customerDependents = request.form['dependents']
        customerDependents = int(customerDependents)
        inputs.append(customerDependents)
        columns  = ['Credit_History', 'LoanAmount', 'ApplicantIncome', 'CoapplicantIncome', 'Dependents']
        df = pd.DataFrame([inputs], columns=columns)
        # print(df)
        approval_status, reasons, met_conditions = predict_loan_approval(df)
        
        price_per_month = customerLoanAmount / float(customerLoanAmountTerm)
        # print(price_per_month)
        ratio = price_per_month / ((customerCoapplicantIncome+customerApplicantIncome)/1000)
        # print(type(reasons))
        # print(ratio)

        conn = openConnection()
        cur = conn.cursor()
        sql = "INSERT INTO `customer` (`name`, `surname`, `age`, `Phonenumber`, `Gender`, `Married`, `Dependents`, `Education`, `Self_Employed`, `ApplicantIncome`, `CoapplicantIncome`, `LoanAmount`, `Loan_Amount_Term`, `Credit_History`, `Property_Area`, `Loan_Status`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)"
        cur.execute(sql, (customerName, customerSurname, customerAge, customerPhone, customerGender, customerMarried, customerDependents, customerEducation,customerSelfEmployed,customerApplicantIncome,customerCoapplicantIncome,customerLoanAmount,customerLoanAmountTerm, customerCreditHistory, customerPropertyArea))
        # Get the ID of the last inserted record
        loan_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        if ratio >= 0.4:
            status = "Loan application denied."
            reasons = "The monthly installment price is 40'%' higher than the customer's income."
        else:
            if approval_status == 'Y':
                status = "Loan application approved."
                reasons = met_conditions
            else:
                status = "Loan application denied."
                reasons = reasons

        return redirect(url_for('loginDecideFormPage', id = id , name = loginName, customerName = customerName, customerLoanAmount = customerLoanAmount
                                , customerLoanAmountTerm = customerLoanAmountTerm, reason = reasons, status = status, loan_id = loan_id))
    else :
        return redirect(url_for('indexPage'))
    
@app.route("/<string:id>/name/<string:name>/approve/loanid/<string:loanid>/status/<string:status>", methods=['POST'])
def decideApprove(id, name, loanid, status):
    if 'login' in session:
        conn = openConnection()
        cur = conn.cursor()
        sql = "UPDATE `customer` SET `Loan_Status` = %s WHERE `customer`.`ID` = %s"
        cur.execute(sql, (status,loanid))
        conn.commit()
        conn.close()
        return render_template('Login/form.html', data_id = id, data_name = name)
    else :
        return redirect(url_for('indexPage'))
# ==================================================================


if __name__ == "__main__":
    app.run(debug=True,
            # , use_reloader=False
            )
