import mysql.connector


def connect_todb():
    try:
        db_con = mysql.connector.connect(
            host="us-cdbr-east-02.cleardb.com",
            user="b3b214d3762ef4",
            passwd="4a2970a9",
            db="heroku_ff6cdbed3d2eb70")
    except mysql.connector.Error as error:
        print("Failed to connect to database in MySQL: {}".format(error))
    finally:
        if db_con.is_connected():
            conn = [db_con]
        else:
            conn = ["no connection"]
    return conn


def get_categories():
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "Select cat_name,cat_description,cat_image, (select GROUP_CONCAT(subcatName SEPARATOR ', ') from subcategory where catID = cat_id) from category")
    records = cur.fetchall()
    cur.close()
    con[0].close()
    print("Total number of rows in Laptop is: ", cur.rowcount)
    return records


def get_subcat():
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute("Select subcatName from subcategory where catID = 1 ")
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records


def get_products(subcatID):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute("Select productsname from product inner join subcategory where product.subcatid = subcategory.subcatID and subcatName = %s",
                (subcatID,))
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records