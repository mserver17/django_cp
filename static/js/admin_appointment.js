document.addEventListener('DOMContentLoaded', function() {
    const serviceSelect = document.getElementById('id_services');
    const employeeSelect = document.getElementById('id_employee');

    function updateEmployees() {
        const serviceOptions = Array.from(serviceSelect.selectedOptions);
        const serviceIds = serviceOptions.map(option => option.value);

        if (serviceIds.length > 0) {
            fetch(`/admin/beauty_salon/appointment/get_employees/?service_ids[]=${serviceIds.join('&service_ids[]=')}`)
                .then(response => response.json())
                .then(data => {
                    employeeSelect.innerHTML = '';
                    data.forEach(employee => {
                        const option = document.createElement('option');
                        option.value = employee.id;
                        option.textContent = employee.name;
                        employeeSelect.appendChild(option);
                    });
                });
        } else {
            employeeSelect.innerHTML = '';
        }
    }

    if (serviceSelect) {
        serviceSelect.addEventListener('change', updateEmployees);
        updateEmployees();
    }
});