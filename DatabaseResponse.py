import mysql.connector
from datetime import date


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


def store_name(first_name, recipientID):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute("INSERT INTO user (recipientID,username) values (%s,%s) ON DUPLICATE KEY UPDATE username = %s",
                (recipientID, first_name, first_name))
    con[0].commit()
    cur.close()
    con[0].close()
    print("MySQL connection is closed")
    return "done"


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


def get_category(category):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "Select cat_name,cat_description,cat_image, (select GROUP_CONCAT(subcatName SEPARATOR ', ') from subcategory where catID = cat_id) from category where cat_name =%s",
        (category.strip(),))
    records = cur.fetchall()
    cur.close()
    con[0].close()
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
    cur.execute(
        "Select productsname from product inner join subcategory where product.subcatid = subcategory.subcatID and subcatName = %s",
        (subcatID.strip(),))
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records


def get_brands(ProductID):
    con = connect_todb()
    cur = con[0].cursor()
    print(ProductID)
    cur.execute(
        "Select DISTINCT BrandName from brand inner join item ON brand.BrandID = item.brandID inner join product on product.productID = item.productID  where product.productsname = %s ",
        (ProductID,))
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records


def get_items(BrandId):
    a, b = BrandId.split(',', 1)
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "Select ItemDesc, Itemimage, CONCAT(size,' ',sizeunit), CONCAT(FORMAT(price,0),' LBP') from item inner join brand on brand.BrandID = item.brandID inner join product on product.productID = item.productID where BrandName = %s and productsname = %s",
        (a.strip(), b.strip()))
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records


def Add_ToCart(CartItem):
    a, b = CartItem.split(',', 1)
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute("SELECT stock FROM heroku_ff6cdbed3d2eb70.item where ItemDesc=%s", (a.strip(),))
    records = cur.fetchall()
    print(records[0][0])
    if records[0][0] > 0:
        r = cur.execute(
            "Insert into Cart(ItemID, userID, Quantity,Isdeleted,itemstatus)  values ((select ItemID from item where itemDesc = %s),(Select userID from user where recipientID = %s),1,'No','Opened')",
            (a.strip(), b.strip()))
        con[0].commit()
        if cur.rowcount == 1:
            RECORD = "Item has been added to your cart"
        else:
            RECORD = "can't insert"
    else:
        RECORD = "Sorry this item is out of stock currently"
    cur.close()
    con[0].close()
    return RECORD


def Update_Cart(itemid, qtyid):
    con = connect_todb()
    cur = con[0].cursor()
    i = 0
    print(qtyid)
    for row in itemid:
        if int(qtyid[i]) == 0:
            delflag = "yes"
            print(delflag)
        else:
            delflag = "No"
        r = cur.execute("update Cart SET cart.Quantity = %s, cart.Isdeleted = %s where cart.CartID= %s",
                        (qtyid[i], delflag, itemid[i]))
        i = i + 1
    con[0].commit()
    cur.close()
    con[0].close()
    RECORD = "saved"
    return RECORD


def get_CartItem(recipientID):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "Select ItemDesc,CONCAT(size,' ',sizeunit),price, Itemimage, Quantity,(price * Quantity),CartID from cart inner join item ON cart.itemID = item.itemID where userID = (Select userid from user where recipientID = %s) and Isdeleted ='No' and itemstatus = 'Opened' ",
        (recipientID.strip(),))
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records


def get_orderpreview(recipientID):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "SELECT SUM(price * Quantity) AS Subtotal from Cart inner join item On cart.ItemID = item.itemID inner join user on user.userid = cart.userID where recipientID = %s and Isdeleted ='No' and itemstatus ='Opened'",
        (recipientID.strip(),))
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records


def create_order(recipientID):
    today = date.today()
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "insert into heroku_ff6cdbed3d2eb70.order(userID,orderStatus,subTotal,Shipping,Total,creatDate) values ((Select userid from user where recipientID = %s),0,"
        "(SELECT SUM(price * Quantity)  from Cart inner join item where cart.ItemID = item.itemID and cart.userID =(Select userid from user where recipientID = %s) and Isdeleted ='No' and itemstatus ='Opened'),(IF(subTotal>49000,0,5000)),(subTotal + Shipping),%s)",
        (recipientID.strip(), recipientID.strip(), today))
    cur.execute("SELECT LAST_INSERT_ID()")
    records = cur.fetchall()
    cur.execute(
        "Update Cart set Cart.itemstatus = 'Placed', Cart.orderID =%s where cart.userID =(Select userid from user where recipientID = %s) and Isdeleted ='No' and itemstatus ='Opened'",
        (records[0][0], recipientID.strip(),))
    print(records[0][0])
    con[0].commit()
    cur.close()
    con[0].close()
    return records


def fill_Address(recipientID, addr, orderid):
    print(orderid)
    con = connect_todb()
    cur = con[0].cursor()
    r = cur.execute("insert into orderaddress(Fullname,Address1,Address2,telephoneNo) values (%s,%s,%s,%s)",
                    (addr[0].strip(), addr[1].strip(), addr[2].strip(), addr[3].strip(),))
    if cur.rowcount == 1:
        RECORD = "Inserted"
    else:
        RECORD = "can't insert"
    print(RECORD)
    cur.execute("SELECT LAST_INSERT_ID()")
    records = cur.fetchall()
    print(records[0][0])
    print(orderid)
    cur.execute(
        "Update heroku_ff6cdbed3d2eb70.order set orderStatus = 1, AddressID =%s, paymentType = '1' where OrderID =%s ",
        (records[0][0], orderid,))
    cur.execute("Update Cart set itemstatus = 'Ordered' where orderID =%s",
                (orderid,))
    con[0].commit()
    cur.close()
    con[0].close()
    return "Done"


def get_Orders(recipientID):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "select OrderID, orderStatus,FORMAT(Total,0),DATE_FORMAT(creatDate,'%d %b %y'),CASE WHEN orderStatus = 0 THEN 'Pending'  WHEN orderStatus = 1 THEN 'Processing' ELSE 'Delivered' END AS statustext"
        " from heroku_ff6cdbed3d2eb70.order inner join user on heroku_ff6cdbed3d2eb70.order.userID = user.userID where recipientID = %s ORDER BY creatDate DESC",
        (recipientID.strip(),))
    records = cur.fetchall()
    print(records)
    cur.close()
    con[0].close()
    return records


def locationparam():
    return "ok"


def get_orderitems(orderid):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "Select ItemDesc, Itemimage, price, Quantity from cart inner join item on cart.ItemID = item.itemID where cart.Isdeleted = 'No' and cart.orderID= %s",
        (orderid.strip(),))
    records = cur.fetchall()
    print(records)
    cur.close()
    con[0].close()
    return records


def get_orderAmount(orderid):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "Select FORMAT(subTotal,0),FORMAT(Shipping,0),FORMAT(Total,0) from heroku_ff6cdbed3d2eb70.order where OrderID =%s",
        (orderid.strip(),))
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records


def get_orderAddress(orderid):
    con = connect_todb()
    cur = con[0].cursor()
    cur.execute(
        "Select Fullname,Address1,Address2,telephoneNo from heroku_ff6cdbed3d2eb70.order inner join orderaddress on heroku_ff6cdbed3d2eb70.order.AddressID = orderaddress.AddressID  where OrderID =%s",
        (orderid.strip(),))
    records = cur.fetchall()
    cur.close()
    con[0].close()
    return records


def delete_Cartitem(cartid):
    con = connect_todb()
    cur = con[0].cursor()
    delflag = "yes"
    r = cur.execute("update Cart SET cart.Quantity = 0, cart.Isdeleted = %s where cart.CartID= %s",
                    (delflag, cartid,))
    con[0].commit()
    cur.close()
    con[0].close()
    RECORD = "saved"
    return RECORD
