import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px

# Initialize database connection
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE,
        publication_year INTEGER,
        category TEXT,
        status TEXT DEFAULT 'available',
        shelf_location TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        address TEXT,
        membership_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        membership_status TEXT DEFAULT 'active'
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        member_id INTEGER,
        loan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date TIMESTAMP NOT NULL,
        return_date TIMESTAMP,
        status TEXT DEFAULT 'borrowed',
        fine_amount REAL DEFAULT 0.00,
        FOREIGN KEY (book_id) REFERENCES books (book_id),
        FOREIGN KEY (member_id) REFERENCES members (member_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        member_id INTEGER,
        reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expiry_date TIMESTAMP,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY (book_id) REFERENCES books (book_id),
        FOREIGN KEY (member_id) REFERENCES members (member_id)
    )
    ''')
    
    conn.commit()
    return conn

# Add sample data if database is empty
def add_sample_data(conn):
    c = conn.cursor()
    
    # Check if books table is empty
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        # Add sample books
        books = [
            ('To Kill a Mockingbird', 'Harper Lee', '9780061120084', 1960, 'Fiction', 'available', 'A1'),
            ('1984', 'George Orwell', '9780451524935', 1949, 'Fiction', 'available', 'A2'),
            ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 1925, 'Fiction', 'available', 'A3'),
            ('Pride and Prejudice', 'Jane Austen', '9780141439518', 1813, 'Romance', 'available', 'B1'),
            ('The Hobbit', 'J.R.R. Tolkien', '9780547928227', 1937, 'Fantasy', 'available', 'B2'),
            ('Harry Potter and the Sorcerer\'s Stone', 'J.K. Rowling', '9780590353427', 1997, 'Fantasy', 'available', 'B3'),
            ('The Catcher in the Rye', 'J.D. Salinger', '9780316769488', 1951, 'Fiction', 'available', 'C1'),
            ('The Lord of the Rings', 'J.R.R. Tolkien', '9780618640157', 1954, 'Fantasy', 'available', 'C2'),
            ('Animal Farm', 'George Orwell', '9780451526342', 1945, 'Fiction', 'available', 'C3'),
            ('The Da Vinci Code', 'Dan Brown', '9780307474278', 2003, 'Mystery', 'available', 'D1')
        ]
        c.executemany("INSERT INTO books (title, author, isbn, publication_year, category, status, shelf_location) VALUES (?, ?, ?, ?, ?, ?, ?)", books)
    
    # Check if members table is empty
    c.execute("SELECT COUNT(*) FROM members")
    if c.fetchone()[0] == 0:
        # Add sample members
        members = [
            ('John', 'Doe', 'john.doe@example.com', '555-1234', '123 Main St', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'),
            ('Jane', 'Smith', 'jane.smith@example.com', '555-5678', '456 Oak Ave', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'),
            ('Bob', 'Johnson', 'bob.johnson@example.com', '555-9012', '789 Pine Rd', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'),
            ('Alice', 'Williams', 'alice.williams@example.com', '555-3456', '321 Elm St', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'),
            ('Charlie', 'Brown', 'charlie.brown@example.com', '555-7890', '654 Maple Dr', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active')
        ]
        c.executemany("INSERT INTO members (first_name, last_name, email, phone, address, membership_date, membership_status) VALUES (?, ?, ?, ?, ?, ?, ?)", members)
    
    conn.commit()

# Function to update book status
def update_book_status(conn, book_id, status):
    c = conn.cursor()
    c.execute("UPDATE books SET status = ? WHERE book_id = ?", (status, book_id))
    conn.commit()

# Function to calculate fine
def calculate_fine(due_date, return_date=None):
    if return_date is None:
        return_date = datetime.now()
    else:
        return_date = datetime.strptime(return_date, '%Y-%m-%d %H:%M:%S')
    
    due_date = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
    
    if return_date > due_date:
        days_overdue = (return_date - due_date).days
        fine = days_overdue * 0.50  # $0.50 per day
        return fine
    return 0.0

# Main app
def main():
    st.set_page_config(page_title="Library Management System", layout="wide")
    
    # Initialize database
    conn = init_db()
    add_sample_data(conn)
    
    # Sidebar navigation
    st.sidebar.title("Library Management")
    page = st.sidebar.selectbox("Choose a page", ["Dashboard", "Books", "Members", "Loans", "Reservations", "Reports"])
    
    if page == "Dashboard":
        show_dashboard(conn)
    elif page == "Books":
        show_books(conn)
    elif page == "Members":
        show_members(conn)
    elif page == "Loans":
        show_loans(conn)
    elif page == "Reservations":
        show_reservations(conn)
    elif page == "Reports":
        show_reports(conn)
    
    conn.close()

def show_dashboard(conn):
    st.title("Library Management System - Dashboard")
    
    # Create columns for stats
    col1, col2, col3, col4 = st.columns(4)
    
    # Get stats
    c = conn.cursor()
    
    # Total books
    c.execute("SELECT COUNT(*) FROM books")
    total_books = c.fetchone()[0]
    col1.metric("Total Books", total_books)
    
    # Available books
    c.execute("SELECT COUNT(*) FROM books WHERE status = 'available'")
    available_books = c.fetchone()[0]
    col2.metric("Available Books", available_books)
    
    # Total members
    c.execute("SELECT COUNT(*) FROM members")
    total_members = c.fetchone()[0]
    col3.metric("Total Members", total_members)
    
    # Active loans
    c.execute("SELECT COUNT(*) FROM loans WHERE status = 'borrowed'")
    active_loans = c.fetchone()[0]
    col4.metric("Active Loans", active_loans)
    
    # Recent activities
    st.subheader("Recent Activities")
    
    # Recent loans
    c.execute("""
    SELECT l.loan_id, b.title, m.first_name || ' ' || m.last_name as member_name, 
           l.loan_date, l.due_date, l.status
    FROM loans l
    JOIN books b ON l.book_id = b.book_id
    JOIN members m ON l.member_id = m.member_id
    ORDER BY l.loan_date DESC
    LIMIT 5
    """)
    
    recent_loans = c.fetchall()
    if recent_loans:
        loans_df = pd.DataFrame(recent_loans, columns=["Loan ID", "Book Title", "Member", "Loan Date", "Due Date", "Status"])
        st.write("Recent Loans")
        st.dataframe(loans_df)
    
    # Books by category chart
    c.execute("""
    SELECT category, COUNT(*) as count
    FROM books
    GROUP BY category
    ORDER BY count DESC
    """)
    
    category_data = c.fetchall()
    if category_data:
        category_df = pd.DataFrame(category_data, columns=["Category", "Count"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Books by Category")
            fig = px.pie(category_df, values='Count', names='Category', hole=0.4)
            st.plotly_chart(fig)
        
        # Books by status
        c.execute("""
        SELECT status, COUNT(*) as count
        FROM books
        GROUP BY status
        """)
        
        status_data = c.fetchall()
        status_df = pd.DataFrame(status_data, columns=["Status", "Count"])
        
        with col2:
            st.subheader("Books by Status")
            fig = px.bar(status_df, x='Status', y='Count', color='Status')
            st.plotly_chart(fig)

def show_books(conn):
    st.title("Books Management")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["View Books", "Add Book", "Search Books"])
    
    with tab1:
        st.subheader("All Books")
        c = conn.cursor()
        c.execute("SELECT * FROM books")
        books = c.fetchall()
        
        if books:
            books_df = pd.DataFrame(books, columns=["Book ID", "Title", "Author", "ISBN", "Publication Year", "Category", "Status", "Shelf Location", "Added Date"])
            st.dataframe(books_df)
            
            # Book actions
            st.subheader("Book Actions")
            book_id = st.number_input("Enter Book ID", min_value=1, step=1)
            action = st.selectbox("Select Action", ["Update Status", "Edit Book", "Delete Book"])
            
            if action == "Update Status":
                new_status = st.selectbox("New Status", ["available", "borrowed", "reserved", "lost"])
                if st.button("Update Status"):
                    update_book_status(conn, book_id, new_status)
                    st.success(f"Book status updated to {new_status}")
                    st.rerun()
            
            elif action == "Edit Book":
                # Get current book details
                c.execute("SELECT * FROM books WHERE book_id = ?", (book_id,))
                book = c.fetchone()
                
                if book:
                    title = st.text_input("Title", book[1])
                    author = st.text_input("Author", book[2])
                    isbn = st.text_input("ISBN", book[3])
                    pub_year = st.number_input("Publication Year", value=book[4], min_value=1000, max_value=datetime.now().year)
                    category = st.text_input("Category", book[5])
                    shelf = st.text_input("Shelf Location", book[7])
                    
                    if st.button("Update Book"):
                        c.execute("""
                        UPDATE books 
                        SET title = ?, author = ?, isbn = ?, publication_year = ?, category = ?, shelf_location = ?
                        WHERE book_id = ?
                        """, (title, author, isbn, pub_year, category, shelf, book_id))
                        conn.commit()
                        st.success("Book updated successfully!")
                        st.rerun()
                else:
                    st.error("Book not found!")
            
            elif action == "Delete Book":
                if st.button("Delete Book"):
                    # Check if book is currently borrowed
                    c.execute("SELECT COUNT(*) FROM loans WHERE book_id = ? AND status = 'borrowed'", (book_id,))
                    if c.fetchone()[0] > 0:
                        st.error("Cannot delete book that is currently borrowed!")
                    else:
                        c.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
                        conn.commit()
                        st.success("Book deleted successfully!")
                        st.rerun()
        else:
            st.info("No books in the database. Add some books!")
    
    with tab2:
        st.subheader("Add New Book")
        
        title = st.text_input("Title")
        author = st.text_input("Author")
        isbn = st.text_input("ISBN")
        pub_year = st.number_input("Publication Year", min_value=1000, max_value=datetime.now().year, value=2023)
        category = st.selectbox("Category", ["Fiction", "Non-Fiction", "Mystery", "Science Fiction", "Fantasy", "Biography", "History", "Romance", "Self-Help", "Other"])
        status = st.selectbox("Status", ["available", "borrowed", "reserved", "lost"])
        shelf = st.text_input("Shelf Location")
        
        if st.button("Add Book"):
            if title and author:
                c = conn.cursor()
                c.execute("""
                INSERT INTO books (title, author, isbn, publication_year, category, status, shelf_location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, author, isbn, pub_year, category, status, shelf))
                conn.commit()
                st.success("Book added successfully!")
                st.rerun()
            else:
                st.error("Title and Author are required!")
    
    with tab3:
        st.subheader("Search Books")
        
        search_option = st.selectbox("Search by", ["Title", "Author", "ISBN", "Category"])
        search_term = st.text_input("Enter search term")
        
        if st.button("Search"):
            if search_term:
                c = conn.cursor()
                
                if search_option == "Title":
                    c.execute("SELECT * FROM books WHERE title LIKE ?", (f"%{search_term}%",))
                elif search_option == "Author":
                    c.execute("SELECT * FROM books WHERE author LIKE ?", (f"%{search_term}%",))
                elif search_option == "ISBN":
                    c.execute("SELECT * FROM books WHERE isbn LIKE ?", (f"%{search_term}%",))
                elif search_option == "Category":
                    c.execute("SELECT * FROM books WHERE category LIKE ?", (f"%{search_term}%",))
                
                results = c.fetchall()
                
                if results:
                    results_df = pd.DataFrame(results, columns=["Book ID", "Title", "Author", "ISBN", "Publication Year", "Category", "Status", "Shelf Location", "Added Date"])
                    st.dataframe(results_df)
                else:
                    st.info("No books found matching your search criteria.")
            else:
                st.error("Please enter a search term!")

def show_members(conn):
    st.title("Members Management")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["View Members", "Add Member", "Search Members"])
    
    with tab1:
        st.subheader("All Members")
        c = conn.cursor()
        c.execute("SELECT * FROM members")
        members = c.fetchall()
        
        if members:
            members_df = pd.DataFrame(members, columns=["Member ID", "First Name", "Last Name", "Email", "Phone", "Address", "Membership Date", "Membership Status"])
            st.dataframe(members_df)
            
            # Member actions
            st.subheader("Member Actions")
            member_id = st.number_input("Enter Member ID", min_value=1, step=1)
            action = st.selectbox("Select Action", ["Update Status", "Edit Member", "Delete Member", "View Loans"])
            
            if action == "Update Status":
                new_status = st.selectbox("New Status", ["active", "expired", "suspended"])
                if st.button("Update Status"):
                    c.execute("UPDATE members SET membership_status = ? WHERE member_id = ?", (new_status, member_id))
                    conn.commit()
                    st.success(f"Member status updated to {new_status}")
                    st.rerun()
            
            elif action == "Edit Member":
                # Get current member details
                c.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
                member = c.fetchone()
                
                if member:
                    first_name = st.text_input("First Name", member[1])
                    last_name = st.text_input("Last Name", member[2])
                    email = st.text_input("Email", member[3])
                    phone = st.text_input("Phone", member[4])
                    address = st.text_area("Address", member[5])
                    
                    if st.button("Update Member"):
                        c.execute("""
                        UPDATE members 
                        SET first_name = ?, last_name = ?, email = ?, phone = ?, address = ?
                        WHERE member_id = ?
                        """, (first_name, last_name, email, phone, address, member_id))
                        conn.commit()
                        st.success("Member updated successfully!")
                        st.rerun()
                else:
                    st.error("Member not found!")
            
            elif action == "Delete Member":
                if st.button("Delete Member"):
                    # Check if member has active loans
                    c.execute("SELECT COUNT(*) FROM loans WHERE member_id = ? AND status = 'borrowed'", (member_id,))
                    if c.fetchone()[0] > 0:
                        st.error("Cannot delete member with active loans!")
                    else:
                        c.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
                        conn.commit()
                        st.success("Member deleted successfully!")
                        st.rerun()
            
            elif action == "View Loans":
                c.execute("""
                SELECT l.loan_id, b.title, l.loan_date, l.due_date, l.status
                FROM loans l
                JOIN books b ON l.book_id = b.book_id
                WHERE l.member_id = ?
                ORDER BY l.loan_date DESC
                """, (member_id,))
                
                loans = c.fetchall()
                
                if loans:
                    loans_df = pd.DataFrame(loans, columns=["Loan ID", "Book Title", "Loan Date", "Due Date", "Status"])
                    st.write(f"Loans for Member ID: {member_id}")
                    st.dataframe(loans_df)
                else:
                    st.info("No loans found for this member.")
        else:
            st.info("No members in the database. Add some members!")
    
    with tab2:
        st.subheader("Add New Member")
        
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        address = st.text_area("Address")
        status = st.selectbox("Membership Status", ["active", "expired", "suspended"])
        
        if st.button("Add Member"):
            if first_name and last_name and email:
                c = conn.cursor()
                
                # Check if email already exists
                c.execute("SELECT COUNT(*) FROM members WHERE email = ?", (email,))
                if c.fetchone()[0] > 0:
                    st.error("Email already exists!")
                else:
                    c.execute("""
                    INSERT INTO members (first_name, last_name, email, phone, address, membership_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (first_name, last_name, email, phone, address, status))
                    conn.commit()
                    st.success("Member added successfully!")
                    st.rerun()
            else:
                st.error("First Name, Last Name, and Email are required!")
    
    with tab3:
        st.subheader("Search Members")
        
        search_option = st.selectbox("Search by", ["Name", "Email", "Phone"])
        search_term = st.text_input("Enter search term")
        
        if st.button("Search"):
            if search_term:
                c = conn.cursor()
                
                if search_option == "Name":
                    c.execute("""
                    SELECT * FROM members 
                    WHERE first_name LIKE ? OR last_name LIKE ?
                    """, (f"%{search_term}%", f"%{search_term}%"))
                elif search_option == "Email":
                    c.execute("SELECT * FROM members WHERE email LIKE ?", (f"%{search_term}%",))
                elif search_option == "Phone":
                    c.execute("SELECT * FROM members WHERE phone LIKE ?", (f"%{search_term}%",))
                
                results = c.fetchall()
                
                if results:
                    results_df = pd.DataFrame(results, columns=["Member ID", "First Name", "Last Name", "Email", "Phone", "Address", "Membership Date", "Membership Status"])
                    st.dataframe(results_df)
                else:
                    st.info("No members found matching your search criteria.")
            else:
                st.error("Please enter a search term!")

def show_loans(conn):
    st.title("Loans Management")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["View Loans", "Issue Loan", "Return Book"])
    
    with tab1:
        st.subheader("All Loans")
        
        # Filter options
        status_filter = st.selectbox("Filter by Status", ["All", "borrowed", "returned", "overdue"])
        
        c = conn.cursor()
        
        if status_filter == "All":
            c.execute("""
            SELECT l.loan_id, b.title, m.first_name || ' ' || m.last_name as member_name, 
                   l.loan_date, l.due_date, l.return_date, l.status, l.fine_amount
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN members m ON l.member_id = m.member_id
            ORDER BY l.loan_date DESC
            """)
        else:
            c.execute("""
            SELECT l.loan_id, b.title, m.first_name || ' ' || m.last_name as member_name, 
                   l.loan_date, l.due_date, l.return_date, l.status, l.fine_amount
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN members m ON l.member_id = m.member_id
            WHERE l.status = ?
            ORDER BY l.loan_date DESC
            """, (status_filter,))
        
        loans = c.fetchall()
        
        if loans:
            loans_df = pd.DataFrame(loans, columns=["Loan ID", "Book Title", "Member", "Loan Date", "Due Date", "Return Date", "Status", "Fine Amount"])
            st.dataframe(loans_df)
            
            # Check for overdue loans
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("""
            UPDATE loans
            SET status = 'overdue'
            WHERE due_date < ? AND status = 'borrowed'
            """, (current_date,))
            conn.commit()
            
            # Loan actions
            st.subheader("Loan Actions")
            loan_id = st.number_input("Enter Loan ID", min_value=1, step=1)
            action = st.selectbox("Select Action", ["View Details", "Update Status"])
            
            if action == "View Details":
                c.execute("""
                SELECT l.loan_id, b.title, b.author, m.first_name || ' ' || m.last_name as member_name, 
                       l.loan_date, l.due_date, l.return_date, l.status, l.fine_amount
                FROM loans l
                JOIN books b ON l.book_id = b.book_id
                JOIN members m ON l.member_id = m.member_id
                WHERE l.loan_id = ?
                """, (loan_id,))
                
                loan = c.fetchone()
                
                if loan:
                    st.write(f"**Loan ID:** {loan[0]}")
                    st.write(f"**Book:** {loan[1]} by {loan[2]}")
                    st.write(f"**Member:** {loan[3]}")
                    st.write(f"**Loan Date:** {loan[4]}")
                    st.write(f"**Due Date:** {loan[5]}")
                    st.write(f"**Return Date:** {loan[6] if loan[6] else 'Not returned yet'}")
                    st.write(f"**Status:** {loan[7]}")
                    st.write(f"**Fine Amount:** ${loan[8]:.2f}")
                    
                    # Calculate current fine if overdue
                    if loan[7] == 'borrowed' and datetime.strptime(loan[5], '%Y-%m-%d %H:%M:%S') < datetime.now():
                        current_fine = calculate_fine(loan[5])
                        st.write(f"**Current Fine (if returned now):** ${current_fine:.2f}")
                else:
                    st.error("Loan not found!")
            
            elif action == "Update Status":
                new_status = st.selectbox("New Status", ["borrowed", "returned", "overdue"])
                if st.button("Update Status"):
                    c.execute("UPDATE loans SET status = ? WHERE loan_id = ?", (new_status, loan_id))
                    
                    # If returning, update book status and set return date
                    if new_status == "returned":
                        c.execute("SELECT book_id, due_date FROM loans WHERE loan_id = ?", (loan_id,))
                        book_info = c.fetchone()
                        if book_info:
                            book_id, due_date = book_info
                            update_book_status(conn, book_id, "available")
                            
                            # Set return date
                            return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Calculate fine if overdue
                            fine = calculate_fine(due_date, return_date)
                            
                            c.execute("""
                            UPDATE loans 
                            SET return_date = ?, fine_amount = ?
                            WHERE loan_id = ?
                            """, (return_date, fine, loan_id))
                    
                    conn.commit()
                    st.success(f"Loan status updated to {new_status}")
                    st.rerun()
        else:
            st.info("No loans in the database.")
    
    with tab2:
        st.subheader("Issue New Loan")
        
        # Get available books
        c = conn.cursor()
        c.execute("SELECT book_id, title FROM books WHERE status = 'available'")
        available_books = c.fetchall()
        
        # Get active members
        c.execute("SELECT member_id, first_name || ' ' || last_name FROM members WHERE membership_status = 'active'")
        active_members = c.fetchall()
        
        if available_books and active_members:
            book_options = {f"{book[0]}: {book[1]}": book[0] for book in available_books}
            member_options = {f"{member[0]}: {member[1]}": member[0] for member in active_members}
            
            selected_book = st.selectbox("Select Book", list(book_options.keys()))
            selected_member = st.selectbox("Select Member", list(member_options.keys()))
            
            loan_days = st.number_input("Loan Period (days)", min_value=1, max_value=30, value=14)
            loan_date = datetime.now()
            due_date = loan_date + timedelta(days=loan_days)
            
            st.write(f"Loan Date: {loan_date.strftime('%Y-%m-%d')}")
            st.write(f"Due Date: {due_date.strftime('%Y-%m-%d')}")
            
            if st.button("Issue Loan"):
                book_id = book_options[selected_book]
                member_id = member_options[selected_member]
                
                c.execute("""
                INSERT INTO loans (book_id, member_id, loan_date, due_date, status)
                VALUES (?, ?, ?, ?, 'borrowed')
                """, (book_id, member_id, loan_date.strftime('%Y-%m-%d %H:%M:%S'), due_date.strftime('%Y-%m-%d %H:%M:%S')))
                
                # Update book status
                update_book_status(conn, book_id, "borrowed")
                
                conn.commit()
                st.success("Loan issued successfully!")
                st.rerun()
        else:
            if not available_books:
                st.error("No available books for loan!")
            if not active_members:
                st.error("No active members to issue loans to!")
    
    with tab3:
        st.subheader("Return Book")
        
        # Get active loans
        c = conn.cursor()
        c.execute("""
        SELECT l.loan_id, b.title, m.first_name || ' ' || m.last_name as member_name, l.due_date
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        JOIN members m ON l.member_id = m.member_id
        WHERE l.status = 'borrowed' OR l.status = 'overdue'
        """)
        
        active_loans = c.fetchall()
        
        if active_loans:
            loan_options = {f"{loan[0]}: {loan[1]} - {loan[2]} (Due: {loan[3]})": loan[0] for loan in active_loans}
            
            selected_loan = st.selectbox("Select Loan to Return", list(loan_options.keys()))
            loan_id = loan_options[selected_loan]
            
            # Get loan details
            c.execute("""
            SELECT l.due_date, b.book_id
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            WHERE l.loan_id = ?
            """, (loan_id,))
            
            loan_details = c.fetchone()
            
            if loan_details:
                due_date, book_id = loan_details
                return_date = datetime.now()
                
                # Calculate fine if overdue
                fine = calculate_fine(due_date)
                
                st.write(f"Return Date: {return_date.strftime('%Y-%m-%d')}")
                if fine > 0:
                    st.warning(f"This book is overdue! Fine amount: ${fine:.2f}")
                
                if st.button("Return Book"):
                    # Update loan
                    c.execute("""
                    UPDATE loans
                    SET status = 'returned', return_date = ?, fine_amount = ?
                    WHERE loan_id = ?
                    """, (return_date.strftime('%Y-%m-%d %H:%M:%S'), fine, loan_id))
                    
                    # Update book status
                    update_book_status(conn, book_id, "available")
                    
                    conn.commit()
                    st.success("Book returned successfully!")
                    st.rerun()
        else:
            st.info("No active loans to return.")

def show_reservations(conn):
    st.title("Reservations Management")
    
    # Create tabs
    tab1, tab2 = st.tabs(["View Reservations", "Make Reservation"])
    
    with tab1:
        st.subheader("All Reservations")
        
        c = conn.cursor()
        c.execute("""
        SELECT r.reservation_id, b.title, m.first_name || ' ' || m.last_name as member_name, 
               r.reservation_date, r.expiry_date, r.status
        FROM reservations r
        JOIN books b ON r.book_id = b.book_id
        JOIN members m ON r.member_id = m.member_id
        ORDER BY r.reservation_date DESC
        """)
        
        reservations = c.fetchall()
        
        if reservations:
            reservations_df = pd.DataFrame(reservations, columns=["Reservation ID", "Book Title", "Member", "Reservation Date", "Expiry Date", "Status"])
            st.dataframe(reservations_df)
            
            # Reservation actions
            st.subheader("Reservation Actions")
            reservation_id = st.number_input("Enter Reservation ID", min_value=1, step=1)
            action = st.selectbox("Select Action", ["Update Status", "Delete Reservation"])
            
            if action == "Update Status":
                new_status = st.selectbox("New Status", ["pending", "fulfilled", "cancelled", "expired"])
                if st.button("Update Status"):
                    c.execute("UPDATE reservations SET status = ? WHERE reservation_id = ?", (new_status, reservation_id))
                    
                    # If fulfilling, update book status
                    if new_status == "fulfilled":
                        c.execute("SELECT book_id FROM reservations WHERE reservation_id = ?", (reservation_id,))
                        book_id = c.fetchone()[0]
                        update_book_status(conn, book_id, "reserved")
                    
                    conn.commit()
                    st.success(f"Reservation status updated to {new_status}")
                    st.rerun()
            
            elif action == "Delete Reservation":
                if st.button("Delete Reservation"):
                    c.execute("DELETE FROM reservations WHERE reservation_id = ?", (reservation_id,))
                    conn.commit()
                    st.success("Reservation deleted successfully!")
                    st.rerun()
        else:
            st.info("No reservations in the database.")
    
    with tab2:
        st.subheader("Make New Reservation")
        
        # Get books that can be reserved (not available but not lost)
        c = conn.cursor()
        c.execute("SELECT book_id, title FROM books WHERE status = 'borrowed'")
        reservable_books = c.fetchall()
        
        # Get active members
        c.execute("SELECT member_id, first_name || ' ' || last_name FROM members WHERE membership_status = 'active'")
        active_members = c.fetchall()
        
        if reservable_books and active_members:
            book_options = {f"{book[0]}: {book[1]}": book[0] for book in reservable_books}
            member_options = {f"{member[0]}: {member[1]}": member[0] for member in active_members}
            
            selected_book = st.selectbox("Select Book", list(book_options.keys()))
            selected_member = st.selectbox("Select Member", list(member_options.keys()))
            
            reservation_date = datetime.now()
            expiry_days = st.number_input("Reservation Valid For (days)", min_value=1, max_value=30, value=7)
            expiry_date = reservation_date + timedelta(days=expiry_days)
            
            st.write(f"Reservation Date: {reservation_date.strftime('%Y-%m-%d')}")
            st.write(f"Expiry Date: {expiry_date.strftime('%Y-%m-%d')}")
            
            if st.button("Make Reservation"):
                book_id = book_options[selected_book]
                member_id = member_options[selected_member]
                
                # Check if book is already reserved
                c.execute("SELECT COUNT(*) FROM reservations WHERE book_id = ? AND status = 'pending'", (book_id,))
                if c.fetchone()[0] > 0:
                    st.error("This book is already reserved by someone else!")
                else:
                    c.execute("""
                    INSERT INTO reservations (book_id, member_id, reservation_date, expiry_date, status)
                    VALUES (?, ?, ?, ?, 'pending')
                    """, (book_id, member_id, reservation_date.strftime('%Y-%m-%d %H:%M:%S'), expiry_date.strftime('%Y-%m-%d %H:%M:%S')))
                    
                    conn.commit()
                    st.success("Reservation made successfully!")
                    st.rerun()
        else:
            if not reservable_books:
                st.error("No books available for reservation!")
            if not active_members:
                st.error("No active members to make reservations for!")

def show_reports(conn):
    st.title("Library Reports")
    
    report_type = st.selectbox("Select Report Type", [
        "Overdue Books", 
        "Popular Books", 
        "Active Members",
        "Fine Collection",
        "Book Inventory",
        "Monthly Loans"
    ])
    
    c = conn.cursor()
    
    if report_type == "Overdue Books":
        st.subheader("Overdue Books Report")
        
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("""
        SELECT b.title, b.author, m.first_name || ' ' || m.last_name as member_name, 
               l.due_date, julianday(?) - julianday(l.due_date) as days_overdue,
               (julianday(?) - julianday(l.due_date)) * 0.50 as fine_amount
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        JOIN members m ON l.member_id = m.member_id
        WHERE l.status = 'borrowed' AND l.due_date < ?
        ORDER BY days_overdue DESC
        """, (current_date, current_date, current_date))
        
        overdue_books = c.fetchall()
        
        if overdue_books:
            overdue_df = pd.DataFrame(overdue_books, columns=["Book Title", "Author", "Member", "Due Date", "Days Overdue", "Fine Amount"])
            overdue_df["Days Overdue"] = overdue_df["Days Overdue"].apply(lambda x: round(x))
            overdue_df["Fine Amount"] = overdue_df["Fine Amount"].apply(lambda x: f"${x:.2f}")
            st.dataframe(overdue_df)
            
            # Visualization
            fig = px.bar(overdue_df, x="Book Title", y="Days Overdue", color="Member", title="Overdue Books by Days")
            st.plotly_chart(fig)
        else:
            st.info("No overdue books at the moment.")
    
    elif report_type == "Popular Books":
        st.subheader("Popular Books Report")
        
        c.execute("""
        SELECT b.title, COUNT(l.loan_id) as loan_count
        FROM books b
        JOIN loans l ON b.book_id = l.book_id
        GROUP BY b.title
        ORDER BY loan_count DESC
        LIMIT 10
        """)
        
        popular_books = c.fetchall()
        
        if popular_books:
            popular_df = pd.DataFrame(popular_books, columns=["Book Title", "Number of Loans"])
            st.dataframe(popular_df)
            
            # Visualization
            fig = px.bar(popular_df, x="Book Title", y="Number of Loans", title="Most Popular Books")
            st.plotly_chart(fig)
            
            # Also show by category
            c.execute("""
            SELECT b.category, COUNT(l.loan_id) as loan_count
            FROM books b
            JOIN loans l ON b.book_id = l.book_id
            GROUP BY b.category
            ORDER BY loan_count DESC
            """)
            
            category_popularity = c.fetchall()
            
            if category_popularity:
                category_df = pd.DataFrame(category_popularity, columns=["Category", "Number of Loans"])
                
                fig = px.pie(category_df, values="Number of Loans", names="Category", title="Loans by Book Category")
                st.plotly_chart(fig)
        else:
            st.info("No loan data available yet.")
    
    elif report_type == "Active Members":
        st.subheader("Active Members Report")
        
        c.execute("""
        SELECT m.first_name || ' ' || m.last_name as member_name, COUNT(l.loan_id) as loan_count
        FROM members m
        JOIN loans l ON m.member_id = l.member_id
        GROUP BY m.member_id
        ORDER BY loan_count DESC
        LIMIT 10
        """)
        
        active_members = c.fetchall()
        
        if active_members:
            active_df = pd.DataFrame(active_members, columns=["Member Name", "Number of Loans"])
            st.dataframe(active_df)
            
            # Visualization
            fig = px.bar(active_df, x="Member Name", y="Number of Loans", title="Most Active Members")
            st.plotly_chart(fig)
        else:
            st.info("No loan data available yet.")
    
    elif report_type == "Fine Collection":
        st.subheader("Fine Collection Report")
        
        date_range = st.selectbox("Select Period", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])
        
        if date_range == "Last 7 Days":
            days = 7
        elif date_range == "Last 30 Days":
            days = 30
        elif date_range == "Last 90 Days":
            days = 90
        else:
            days = 36500  # ~100 years, effectively "all time"
        
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        past_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        c.execute("""
        SELECT m.first_name || ' ' || m.last_name as member_name, SUM(l.fine_amount) as total_fine
        FROM loans l
        JOIN members m ON l.member_id = m.member_id
        WHERE l.return_date BETWEEN ? AND ? AND l.fine_amount > 0
        GROUP BY m.member_id
        ORDER BY total_fine DESC
        """, (past_date, current_date))
        
        fine_data = c.fetchall()
        
        if fine_data:
            fine_df = pd.DataFrame(fine_data, columns=["Member Name", "Total Fine"])
            fine_df["Total Fine"] = fine_df["Total Fine"].apply(lambda x: f"${x:.2f}")
            st.dataframe(fine_df)
            
            # Calculate total fines collected
            c.execute("""
            SELECT SUM(fine_amount) as total_fines
            FROM loans
            WHERE return_date BETWEEN ? AND ? AND fine_amount > 0
            """, (past_date, current_date))
            
            total_fines = c.fetchone()[0] or 0
            st.metric("Total Fines Collected", f"${total_fines:.2f}")
            
            # Convert for visualization (remove $ sign)
            fine_df["Total Fine"] = fine_df["Total Fine"].apply(lambda x: float(x.replace('$', '')))
            
            # Visualization
            fig = px.bar(fine_df, x="Member Name", y="Total Fine", title="Fine Collection by Member")
            st.plotly_chart(fig)
        else:
            st.info("No fine data available for the selected period.")
    
    elif report_type == "Book Inventory":
        st.subheader("Book Inventory Report")
        
        # Status breakdown
        c.execute("""
        SELECT status, COUNT(*) as count
        FROM books
        GROUP BY status
        """)
        
        status_data = c.fetchall()
        
        if status_data:
            status_df = pd.DataFrame(status_data, columns=["Status", "Count"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Books by Status")
                st.dataframe(status_df)
            
            with col2:
                fig = px.pie(status_df, values="Count", names="Status", title="Books by Status")
                st.plotly_chart(fig)
        
        # Category breakdown
        c.execute("""
        SELECT category, COUNT(*) as count
        FROM books
        GROUP BY category
        ORDER BY count DESC
        """)
        
        category_data = c.fetchall()
        
        if category_data:
            category_df = pd.DataFrame(category_data, columns=["Category", "Count"])
            
            st.write("Books by Category")
            st.dataframe(category_df)
            
            fig = px.bar(category_df, x="Category", y="Count", title="Books by Category")
            st.plotly_chart(fig)
            
            # Publication year breakdown
            c.execute("""
            SELECT 
                CASE 
                    WHEN publication_year >= 2020 THEN '2020s'
                    WHEN publication_year >= 2010 THEN '2010s'
                    WHEN publication_year >= 2000 THEN '2000s'
                    WHEN publication_year >= 1990 THEN '1990s'
                    WHEN publication_year >= 1980 THEN '1980s'
                    WHEN publication_year >= 1970 THEN '1970s'
                    WHEN publication_year >= 1960 THEN '1960s'
                    WHEN publication_year >= 1950 THEN '1950s'
                    ELSE 'Before 1950'
                END as decade,
                COUNT(*) as count
            FROM books
            GROUP BY decade
            ORDER BY decade DESC
            """)
            
            decade_data = c.fetchall()
            
            if decade_data:
                decade_df = pd.DataFrame(decade_data, columns=["Decade", "Count"])
                
                fig = px.bar(decade_df, x="Decade", y="Count", title="Books by Publication Decade")
                st.plotly_chart(fig)
        else:
            st.info("No book data available.")
    
    elif report_type == "Monthly Loans":
        st.subheader("Monthly Loans Report")
        
        # Get year for filtering
        current_year = datetime.now().year
        year_options = list(range(current_year - 5, current_year + 1))
        selected_year = st.selectbox("Select Year", year_options, index=len(year_options) - 1)
        
        c.execute("""
        SELECT 
            strftime('%m', loan_date) as month,
            COUNT(*) as loan_count
        FROM loans
        WHERE strftime('%Y', loan_date) = ?
        GROUP BY month
        ORDER BY month
        """, (str(selected_year),))
        
        monthly_data = c.fetchall()
        
        if monthly_data:
            # Convert month numbers to names
            month_names = {
                '01': 'January', '02': 'February', '03': 'March', '04': 'April',
                '05': 'May', '06': 'June', '07': 'July', '08': 'August',
                '09': 'September', '10': 'October', '11': 'November', '12': 'December'
            }
            
            monthly_df = pd.DataFrame(monthly_data, columns=["Month", "Loan Count"])
            monthly_df["Month"] = monthly_df["Month"].apply(lambda x: month_names.get(x, x))
            
            st.dataframe(monthly_df)
            
            # Visualization
            fig = px.line(monthly_df, x="Month", y="Loan Count", markers=True, title=f"Monthly Loans for {selected_year}")
            st.plotly_chart(fig)
            
            # Calculate total loans for the year
            total_loans = monthly_df["Loan Count"].sum()
            st.metric(f"Total Loans in {selected_year}", total_loans)
        else:
            st.info(f"No loan data available for {selected_year}.")

if __name__ == "__main__":
    main() 