#imports
import pymongo
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from pydantic import BaseModel, field_validator
from typing import Optional

#mounting FastAPI, webpage templates, and CSS style
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# MongoDB client setup
client = MongoClient("mongodb://localhost:27017/")
db = client["employee_db"]
employees_collection = db["employees"]

#Defined list of departments
List_of_Departments = ['Information Technology', 'Human Resources',
                       'Marketing', 'Finance', 'Operations']

#Pydantic model
class Employee(BaseModel):
    #Required records
    employee_id: int
    full_name: str
    age: int
    department: str

    #Validating employee ID for logical discrepancies
    @field_validator("employee_id")
    def validate_employee_id(cls, value):
        if value < 1:
            raise ValueError("Employee ID must be greater than 0")
        return value

    #Validating age to ensure within proper working age
    @field_validator("age")
    def validate_age(cls, value):
        if value < 18 or value > 100:
            raise ValueError("Age must be within working age range")
        return value

    #Validating names according length, character count, and ensuring string is only letters
    @field_validator("full_name")
    def validate_name(cls, name):
        if len(name) > 100 or len(name) < 5:
            raise ValueError("Length of name invalid, please enter full name")
        if not name.replace(" ", "").isalpha():
            raise ValueError("Name must contain only letters")
        if name == name[0] * len(name):
            raise ValueError("Repeating and duplicate values detected")
        return name

    #Validating departments according to a pre-determined list
    @field_validator("department")
    def validate_department(cls, department):
        if department not in List_of_Departments:
            raise ValueError("Invalid Department, choose from {}".format(List_of_Departments))
        return department.title()

#view employees function
@app.get("/employees")
def view_employees(request: Request, employee_id: Optional[int] = 0):
    #Create a local list of employees
    employees = []

    #On the search tab, look for the specified employee using the input id.
    #Adds specified employee to the employee list if found
    if employee_id != 0:
        specified_employees = employees_collection.find_one({"employee_id": employee_id})
        #Error handling for no employees found
        if not specified_employees:
            return error_page(request, ["View page: No employees found"])
        specified_employees['_id'] = str(specified_employees['_id'])
        employees.append(specified_employees)

    #Show all employee by default on the view page
    else:
        for employee in employees_collection.find().sort("employee_id", pymongo.ASCENDING):
            employee['_id'] = str(employee['_id'])
            employees.append(employee)
        #Display an empty list if no employees added
        if not employees:
            return error_page(request, ["View page: No employees added, add employees through the add function."])
    return templates.TemplateResponse("view.html", context={"request": request, "employees": employees})

#add employees
@app.post("/add")
def add_employee(request: Request, employee_id: int = Form(...), full_name: str = Form(...), age: int = Form(...), department: str = Form(...)):
    #Create a dictionary for new employee
    doc = {"employee_id": employee_id, "full_name": full_name, "age": age, "department": department}

    try:
        # validating data using field validator
        validated_employee = Employee(**doc)
        # Checking for existing employee ID to prevent duplicates when adding, only adds employee if check returns no duplicates
        if employees_collection.find_one({"employee_id": validated_employee.employee_id}):
            return error_page(request, ["Add page: Employee already exists"])
        else:
            employees_collection.insert_one(validated_employee.model_dump())
    #Error handling for field validator
    except Exception as e:
        return error_page(request, [str(e)])
    return RedirectResponse(url="/employees", status_code=303)

#update employee
@app.post("/update")
def update_employee(request: Request, employee_id: int = Form(...), new_id: int = Form(...), full_name: str = Form(...), age: int = Form(...), department: str = Form(...)):
    # Checking if employee actually exists
    existing_employee = employees_collection.find_one({"employee_id": employee_id})
    try:
        #Error handling if employee not found
        if not existing_employee:
            return error_page(request, ["Update page: Employee not found"])

        #Prepare the update data
        update = {"employee_id": new_id, "full_name": full_name, "age": age, "department": department}
        #Validates the updated data using field validator
        validated_employee = Employee(**update)

        #Updates data only if data is validated and does not update over another existing employee
        if new_id != employee_id and employees_collection.find_one({"employee_id": validated_employee.employee_id}):
            return error_page(request, ["Update page: Employee already exists"])
        else:
            employees_collection.update_one({"employee_id": employee_id}, {"$set": validated_employee.model_dump()})

    #Error handling for field validator
    except Exception as e:
        return error_page(request, [str(e)])
    return RedirectResponse(url="/employees", status_code=303)

#delete employee
@app.post("/delete")
def delete_employee(request: Request, employee_id: int = Form(...)):
    existing_employee = employees_collection.find_one({"employee_id": employee_id})

    #Deletes specified employee
    if existing_employee:
        employees_collection.delete_one({"employee_id": employee_id})
    #Deletes all records when input is 0
    elif employee_id == 0:
        employees_collection.delete_many({})
    #Exception handling if employee not found
    else:
        return error_page(request, ["Delete page: Employee not found"])
    return RedirectResponse(url="/employees", status_code=303)

#view webpage is directed directly to the /employee url

#add employee webpage
@app.get("/add")
def add_page(request: Request):
    return templates.TemplateResponse("add.html", {"request": request, "departments": List_of_Departments})

#update employee webpage
@app.get("/update")
def update_page(request: Request):
    return templates.TemplateResponse("update.html", {"request": request, "departments": List_of_Departments})

#delete employee webpage
@app.get("/delete")
def delete_page(request: Request):
    return templates.TemplateResponse("delete.html", context={"request": request})

#global error webpage
def error_page(request: Request, errors: list[str]):
    return templates.TemplateResponse("error.html", {"request": request, "errors": errors})

#Homepage
@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    employees = list(employees_collection.find())
    for emp in employees:
        emp["_id"] = str(emp["_id"])
    return templates.TemplateResponse("index.html", {"request": request, "employees": employees})