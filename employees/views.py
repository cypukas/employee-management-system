from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q

from .models import Employee, Employee_information, Department, Position, Internal_permission, External_permission, \
    DeactivationLog

from .forms import EmployeeForm, EmployeeInformationForm, DeactivationLogForm, InternalPermissionForm, \
    ExternalPermissionForm

from datetime import date


def valid_employees(request):
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'first_name')
    order = request.GET.get('order', 'asc')

    employees = Employee.objects.filter(
        verification=Employee.VERIFICATION_ACTIVE
    ).select_related('department').prefetch_related('employee_information')

    if search_query:
        employees = employees.filter(
            Q(first_name__istartswith=search_query) |
            Q(last_name__istartswith=search_query) |
            Q(department__name__istartswith=search_query) |
            Q(position__name__istartswith=search_query)
        )

    # Apply sorting to the filtered results
    if order == 'desc':
        sort_by = f'-{sort_by}'
    employees = employees.order_by(sort_by)

    return render(request, 'employees/active_employees.html', {
        'employees': employees
    })


def inactive_employees(request):
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'id')
    order = request.GET.get('order', 'asc')

    employees = Employee.objects.filter(verification=Employee.VERIFICATION_INACTIVE)

    if search_query:
        employees = employees.filter(
            Q(first_name__istartswith=search_query) |
            Q(last_name__istartswith=search_query) |
            Q(department__name__istartswith=search_query) |
            Q(position__name__istartswith=search_query)
        )

    if order == 'desc':
        sort_by = '-' + sort_by

    employees = employees.order_by(sort_by)

    return render(request, 'employees/inactive_employees.html', {
        'employees': employees
    })


def view_employee(request, id):
    employee = get_object_or_404(Employee, pk=id)
    employee_information = get_object_or_404(Employee_information, employee=employee)
    deactivationlog = get_object_or_404(DeactivationLog, employee=employee)
    department = employee.department
    position = employee.position

    context = {
        'employee': employee,
        'employee_information': employee_information,
        'department': department,
        'position': position,
        'deactivationlog': deactivationlog
    }
    return render(request, 'employees/view_employees.html', context)


def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            new_employee = form.save()
            return render(request, 'employees/add.html', {
                'form': EmployeeForm(),
                'success': True
            })
        else:
            return render(request, 'employees/add.html', {
                'form': form
            })
    else:
        form = EmployeeForm()
        return render(request, 'employees/add.html', {
            'form': form
        })


def add_employee_information(request):
    if request.method == 'POST':
        form = EmployeeInformationForm(request.POST)
        if form.is_valid():
            new_employee_information = form.save()
            return render(request, 'employees/add.html', {
                'form': EmployeeInformationForm(),
                'success': True
            })
        else:
            return render(request, 'employees/add.html', {
                'form': form
            })
    else:
        form = EmployeeInformationForm()
        return render(request, 'employees/add.html', {
            'form': form
        })


def edit_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee_information = get_object_or_404(Employee_information, employee=employee)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        info_form = EmployeeInformationForm(request.POST, instance=employee_information)
        if form.is_valid() and info_form.is_valid():
            form.save()
            info_form.save()
            return redirect('active_employees')
    else:
        form = EmployeeForm(instance=employee)
        info_form = EmployeeInformationForm(instance=employee_information)

    return render(request, 'employees/edit.html', {
        'form': form,
        'info_form': info_form,
        'employee': employee
    })


def delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    deactivationlog = get_object_or_404(DeactivationLog, employee=employee)

    if request.method == 'POST':
        form = DeactivationLogForm(request.POST, instance=deactivationlog)
        if form.is_valid():
            form.save()
            employee.verification = Employee.VERIFICATION_INACTIVE
            employee.save()
            return redirect('inactive_employees')

    form = DeactivationLogForm(instance=deactivationlog)

    return render(request, 'employees/deactivate_employee.html', {
        'form': form,
        'employee': employee
    })


@require_POST
def reactivate_employee(request, id):
    employee = get_object_or_404(Employee, pk=id)
    employee.verification = Employee.VERIFICATION_ACTIVE
    employee.save()
    return redirect('inactive_employees')


def index(request):
    today = date.today()
    employees_birthday_this_month = Employee_information.objects.filter(
        date_of_birth__month=today.month
    ).select_related('employee').order_by('date_of_birth__day')

    # Pass the employees to the template
    return render(request, 'employees/index.html', {
        'employees_birthday_this_month': employees_birthday_this_month
    })


def add_internal_permission(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    if request.method == 'POST':
        form = InternalPermissionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Internal permission added successfully.")
            return redirect('active_employees')
    else:
        form = InternalPermissionForm(initial={'employee': employee})

    # If the form is not valid, or if it's a GET request, render the page with the form.
    return render(request, 'employees/add_internal_permission.html', {
        'form': form,
        'employee': employee
    })


def add_external_permission(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    if request.method == 'POST':
        form = ExternalPermissionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "External permission added successfully.")
            return redirect('active_employees')
    else:
        form = ExternalPermissionForm(initial={'employee': employee})
    return render(request, 'employees/add_external_permission.html', {
        'form': form,
        'employee': employee
    })


def edit_internal_permission(request, permission_id):
    permission = get_object_or_404(Internal_permission, pk=permission_id)
    if request.method == 'POST':
        form = InternalPermissionForm(request.POST, request.FILES, instance=permission)
        if form.is_valid():
            form.save()
            return redirect('active_employees')
    else:
        form = InternalPermissionForm(instance=permission)

    return render(request, 'employees/internal_permission_edit_template.html', {'form': form})


def edit_external_permission(request, permission_id):
    permission = get_object_or_404(External_permission, pk=permission_id)
    if request.method == 'POST':
        form = ExternalPermissionForm(request.POST, request.FILES, instance=permission)
        if form.is_valid():
            form.save()
            return redirect('active_employees')
    else:
        form = ExternalPermissionForm(instance=permission)

    return render(request, 'employees/external_permission_edit_template.html', {'form': form})


@require_POST
def delete_employee_permanently(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.delete()
    messages.success(request, f"The employee {employee.first_name} {employee.last_name} has been deleted permanently.")
    return redirect('inactive_employees')
