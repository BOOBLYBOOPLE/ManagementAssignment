Instructions to run application

INSTALL ALL RELATED PROGRAMS AND PACKAGES BEFORE USE

1. Modify database values in script.py to specified database and collection and start connection
	db = client["employee_db"]
	employees_collection = db["employees"]

2.Run command prompt and direct directory to project name
cd (directory on where project is located)\EmployeeDatabseManagementSystem

3. run uvicorn script:app --reload

4. To run on FastAPI Backend view add /docs to the localhost url