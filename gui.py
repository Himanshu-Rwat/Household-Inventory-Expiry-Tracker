from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import oracledb
import getpass

# Database settings
USERNAME = "HIMANSHU_RAWAT080_SCHEMA_DJLTZ"
DSN = "tcps://db.freesql.com:2484/26ai_un3c1"

# Ask for the password once when the application starts
DB_PASSWORD = getpass.getpass(
    "Enter your Oracle password: "
)


def connect_database():
    return oracledb.connect(
        user=USERNAME,
        password=DB_PASSWORD,
        dsn=DSN
    )


# ---------- VIEW INVENTORY ----------
def view_inventory():
    try:
        connection = connect_database()
        cursor = connection.cursor()

        query = """
            SELECT product_id, product_name, category,
                   quantity, unit, expiry_date
            FROM HOUSEHOLD_PRODUCTS
            ORDER BY product_id
        """

        cursor.execute(query)
        products = cursor.fetchall()

        # Clear old table rows
        for row in inventory_table.get_children():
            inventory_table.delete(row)

        # Display products
        for product in products:
            inventory_table.insert("", "end", values=product)

        messagebox.showinfo(
            "Inventory",
            f"Loaded {len(products)} products successfully."
        )

        cursor.close()
        connection.close()

    except oracledb.Error as error:
        messagebox.showerror("Database Error", str(error))

    except Exception as error:
        messagebox.showerror("Error", str(error))

def add_product_form():
    form = tk.Toplevel(root)
    form.title("Add Product")
    form.geometry("400x450")
    form.resizable(False, False)

    fields = [
        ("Product Name", "name"),
        ("Category", "category"),
        ("Quantity", "quantity"),
        ("Unit", "unit"),
        ("Minimum Stock", "min_stock"),
        ("Expiry Date (YYYY-MM-DD)", "expiry_date")
    ]

    entries = {}

    heading = tk.Label(
        form,
        text="Add New Product",
        font=("Arial", 16, "bold")
    )
    heading.pack(pady=15)

    form_frame = tk.Frame(form)
    form_frame.pack(padx=20, fill="x")

    for row, (label_text, key) in enumerate(fields):
        label = tk.Label(
            form_frame,
            text=label_text,
            anchor="w"
        )
        label.grid(
            row=row,
            column=0,
            padx=5,
            pady=7,
            sticky="w"
        )

        entry = tk.Entry(form_frame, width=22)
        entry.grid(
            row=row,
            column=1,
            padx=5,
            pady=7
        )

        entries[key] = entry

    def save_product():
        name = entries["name"].get().strip()
        category = entries["category"].get().strip()
        unit = entries["unit"].get().strip()

        if not name or not unit:
            messagebox.showwarning(
                "Input Error",
                "Product name and unit are required.",
                parent=form
            )
            return

        try:
            quantity = float(entries["quantity"].get())
            min_stock = float(entries["min_stock"].get())

            if quantity < 0 or min_stock < 0:
                raise ValueError

            expiry_text = entries["expiry_date"].get().strip()

            if expiry_text:
                expiry_date = datetime.strptime(
                    expiry_text, "%Y-%m-%d"
                ).date()
            else:
                expiry_date = None

        except ValueError:
            messagebox.showerror(
                "Input Error",
                "Enter valid non-negative quantities and a date "
                "in YYYY-MM-DD format.",
                parent=form
            )
            return

        connection = None
        cursor = None

        try:
            connection = connect_database()
            cursor = connection.cursor()

            cursor.callproc(
                "ADD_PRODUCT",
                [
                    name,
                    category,
                    quantity,
                    unit,
                    min_stock,
                    expiry_date
                ]
            )

            connection.commit()

            messagebox.showinfo(
                "Success",
                f"{name} added successfully!",
                parent=form
            )

            form.destroy()
            view_inventory()

        except oracledb.Error as error:
            if connection is not None:
                connection.rollback()

            messagebox.showerror(
                "Database Error",
                str(error),
                parent=form
            )

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

    save_button = tk.Button(
        form,
        text="Save Product",
        command=save_product,
        bg="#2878E5",
        fg="white",
        padx=15,
        pady=7
    )
    save_button.pack(pady=15)

def expiry_alerts():
    try:
        connection = connect_database()
        cursor = connection.cursor()

        query = """
            SELECT product_id, product_name, quantity, unit, expiry_date,
                   CASE
                       WHEN expiry_date < TRUNC(SYSDATE)
                           THEN 'EXPIRED'
                       WHEN expiry_date <= TRUNC(SYSDATE) + 7
                           THEN 'EXPIRING SOON'
                       ELSE 'NORMAL'
                   END AS expiry_status
            FROM HOUSEHOLD_PRODUCTS
            WHERE expiry_date <= TRUNC(SYSDATE) + 7
            ORDER BY expiry_date
        """

        cursor.execute(query)
        products = cursor.fetchall()

        # Clear the old table data
        for row in inventory_table.get_children():
            inventory_table.delete(row)

        # Display expiry alerts in the table
        for product in products:
            inventory_table.insert("", "end", values=product)

        messagebox.showinfo(
            "Expiry Alerts",
            f"Found {len(products)} expired or soon-to-expire products."
        )

        cursor.close()
        connection.close()

    except Exception as error:
        messagebox.showerror("Error", str(error))

def low_stock_alerts():
    try:
        connection = connect_database()
        cursor = connection.cursor()

        query = """
            SELECT product_id, product_name, category,quantity, unit, expiry_date, 'LOW STOCK' AS status FROM HOUSEHOLD_PRODUCTS WHERE quantity <= min_stock ORDER BY quantity ASC
        """

        cursor.execute(query)
        products = cursor.fetchall()

        # Clear previous table data
        for row in inventory_table.get_children():
            inventory_table.delete(row)

        # Display low-stock products
        for product in products:
            inventory_table.insert("", "end", values=product)

        messagebox.showinfo(
            "Low Stock Alerts",
            f"Found {len(products)} low-stock products."
        )

        cursor.close()
        connection.close()

    except Exception as error:
        messagebox.showerror("Error", str(error))

def generate_shopping_list():
    try:
        connection = connect_database()
        cursor = connection.cursor()

        cursor.callproc("GENERATE_SHOPPING_LIST")
        connection.commit()

        messagebox.showinfo(
            "Shopping List",
            "Shopping list generated successfully!"
        )

        cursor.close()
        connection.close()

    except Exception as error:
        messagebox.showerror("Error", str(error))

def view_shopping_list():
    try:
        connection = connect_database()
        cursor = connection.cursor()

        query = """
            SELECT item_id, product_name, quantity_needed,unit, is_purchased, generated_on
            FROM SHOPPING_LIST
            ORDER BY item_id DESC
        """

        cursor.execute(query)
        items = cursor.fetchall()

        # Clear previous table data
        for row in inventory_table.get_children():
            inventory_table.delete(row)

        # Display shopping-list items
        for item in items:
            inventory_table.insert(
                "",
                "end",
                values=(
                    item[0],
                    item[1],
                    "Shopping List",
                    item[2],
                    item[3],
                    item[5],
                    "Purchased" if item[4] == "Y" else "Needed"
                )
            )

        if items:
            messagebox.showinfo(
                "Shopping List",
                f"Showing {len(items)} shopping-list items."
            )
        else:
            messagebox.showinfo(
                "Shopping List",
                "Your shopping list is empty. Generate it after checking low-stock products."
            )

        cursor.close()
        connection.close()

    except Exception as error:
        messagebox.showerror("Error", str(error))

# ---------- MAIN WINDOW ----------
root = tk.Tk()
root.title("Household Inventory and Expiry Tracker")
root.geometry("850x550")

# ---------- HEADING ----------
heading = tk.Label(root, text="Household Inventory and Expiry Tracker",font=("Arial", 18, "bold"))
heading.pack(pady=15)

# ---------- BUTTON ----------
view_button = tk.Button(
    root,
    text="View Inventory",
    font=("Arial", 11),
    command=view_inventory
)
view_button.pack(pady=10)

add_button = tk.Button(
    root,
    text="Add Product",
    font=("Arial", 11),
    command=add_product_form
)
add_button.pack(pady=5)

expiry_button = tk.Button(
    root,
    text="Expiry Alerts",
    command=expiry_alerts
)
expiry_button.pack(pady=5)

low_stock_button = tk.Button(
    root,
    text="Low Stock Alerts",
    command=low_stock_alerts
)
low_stock_button.pack(pady=5)

shopping_button = tk.Button(
    root,
    text="Generate Shopping List",
    command=generate_shopping_list
)
shopping_button.pack(pady=5)

view_shopping_button = tk.Button(
    root,
    text="View Shopping List",
    command=view_shopping_list
)
view_shopping_button.pack(pady=5)

# ---------- TABLE ----------
columns = (
    "ID","Name","Category","Quantity","Unit","Expiry Date","Status"
)

inventory_table = ttk.Treeview(
    root,
    columns=columns,
    show="headings"
)

for column in columns:
    inventory_table.heading(column, text=column)
    inventory_table.column(column, width=120, anchor="center")

inventory_table.pack(fill="both", expand=True, padx=15, pady=15)

# ---------- RUN APPLICATION ----------
root.mainloop()
