import uuid
import sqlite3
from datetime import date, datetime, timedelta


def connect_to_db():
    connection = sqlite3.connect('data.db')
    return connection

def stringToDateTime(value):
    new_value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
    return new_value

def selectFromTable(rows, table_name, find_by_row, value):
    connection = connect_to_db()
    cursor = connection.cursor()
    query = f"select {rows} from {table_name} where {find_by_row}=?"
    result = cursor.execute(query, (value,))
    row = result.fetchone()
    connection.close()
    return row

def insertIntoTable(table_name, total_values, values):
    connection = connect_to_db()
    cursor = connection.cursor()
    insert_query = f"INSERT OR IGNORE INTO {table_name} VALUES{total_values}"
    cursor.execute(insert_query, values)
    connection.commit()
    connection.close()

def updateTable(table_name, rows_to_update, where_cond, values):
    connection = connect_to_db()
    cursor = connection.cursor()
    update_query = f"UPDATE {table_name} SET {rows_to_update} where {where_cond}"
    cursor.execute(update_query, values)
    connection.commit()
    connection.close()

def authUser(username, password):
    rows, table_name, find_by_row, value = "user_id,password", "users", "username", username
    row = selectFromTable(rows, table_name, find_by_row, value)
    if row:
        user_id, passwd = row[0], row[1]
        if passwd == password:
            token = uuid.uuid1().hex
            time = datetime.now()
            rows, table_name, find_by_row, value = "*", "users_token", "user_id", user_id
            row = selectFromTable(rows, table_name, find_by_row, value)
            # -------- INSERT INTO TABLE WHEN TOKEN IS NOT PRESENT -------
            if not row:
                user = (user_id, token, time)
                table_name, total_values, values = "users_token", "(?,?,?)", user
                insertIntoTable(table_name, total_values, values)
                return True, {"token": token}
            # -------- UPDATE THE TOKEN IF TOKEN IS ALREADY PRESENT -------
            new_value = (time, token,user_id)
            table_name, rows_to_update, where_cond, values = "users_token", "expire_time = ?,token = ?", "user_id = ?", new_value
            updateTable(table_name, rows_to_update, where_cond, values)
            return True, {"token": token}
        return False, {"msg": "Incorrect Password"}
    return False, {"msg": "Username not found"}

def tokenCheck(token, time, reqRoute):
    rows, table_name, find_by_row, value = "expire_time", "users_token", "token", token
    row = selectFromTable(rows, table_name, find_by_row, value)
    if not row:
        return False, {"msg": "Token Not Found"}
    # ----- To convert into datetime format -------
    expire_time = stringToDateTime(row[0])
    timeDiff = time - expire_time
    if timeDiff.seconds <= 120:
        # for requested route we will increase the expire time by 3 min
        if reqRoute:
            # ---------- UPDATE THE TOKEN EXPIRE TIME ------------
            new_expire_time = expire_time + timedelta(minutes=3)
            new_values = (new_expire_time, token)
            table_name, rows_to_update, where_cond, values = "users_token", "expire_time = ?", "token = ?", new_values
            updateTable(table_name, rows_to_update, where_cond, values)
        return True, {"msg": "Success"}
    return False, {"msg": "Token Expired Please Login Again"}
